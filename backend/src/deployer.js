import fs from 'node:fs/promises';
import path from 'node:path';
import net from 'node:net';
import { docker, CONTAINER_IMAGE } from './sandbox.js';

// 部署测试容器：把会话 build 目录挂载进 node:20-alpine 容器，
// 用内联 node HTTP 静态服务器对外提供服务（复用 builder 产物，不引第三方依赖）。
// 端口从 3001-3004 顺次选择首个空闲端口；再次部署时先注销同会话旧容器。

const HOST_PORTS = [3001, 3002, 3003, 3004];
const CONTAINER_PORT = 8080;
const LABEL = { 'nl2e.deploy': '1', 'nl2e.session': '' };
const containerName = (sessionId) => `nl2e-test-${sessionId}`;

// ---------- 测试容器固定资源配额 ----------
const CONTAINER_MEM_BYTES = 256 * 1024 * 1024; // 内存固定 256MB
const CONTAINER_NANO_CPUS = 500000000; // CPU 固定 0.5 核
const CONTAINER_DISK_SIZE = '128m'; // 硬盘固定 128MB（需 backing fs 支持，失败自动降级）
const BANDWIDTH_BYTES_PER_SEC = 128 * 1024; // 带宽固定 128KB/s（容器内静态服务器全局限流）

// 静态服务器：内联实现，含全局令牌桶限流（所有连接共享 BANDWIDTH_BYTES_PER_SEC）
const staticServer = `const http=require('http'),fs=require('fs'),path=require('path'),{Transform}=require('stream');
const ROOT='/app',PORT=process.env.PORT||8080,RATE=${BANDWIDTH_BYTES_PER_SEC};
let bucket=RATE;setInterval(()=>{bucket=RATE;},1000).unref();
class Throttle extends Transform{
  _transform(chunk,enc,cb){
    const send=()=>{
      if(bucket>=chunk.length){bucket-=chunk.length;this.push(chunk);cb();}
      else if(bucket>0){const head=chunk.slice(0,bucket);this.push(head);chunk=chunk.slice(bucket);bucket=0;setTimeout(send,200);}
      else setTimeout(send,200);
    };send();
  }
}
const MIME={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.ico':'image/x-icon','.txt':'text/plain; charset=utf-8'};
const server=http.createServer((req,res)=>{
  if(req.method==='GET'||req.method==='HEAD'){
    let up=decodeURIComponent((req.url||'/').split('?')[0]);
    if(up==='/')up='/index.html';
    let fp=path.normalize(path.join(ROOT,up));
    if(fp!==ROOT&&!fp.startsWith(ROOT+path.sep)){res.writeHead(403);res.end('forbidden');return;}
    fs.stat(fp,(e,st)=>{
      if(e||!st.isFile()){res.writeHead(404);res.end('not found');return;}
      const ct=MIME[path.extname(fp).toLowerCase()]||'application/octet-stream';
      res.writeHead(200,{'Content-Type':ct,'Cache-Control':'no-cache'});
      if(req.method==='HEAD'){res.end();return;}
      fs.createReadStream(fp).pipe(new Throttle()).pipe(res);
    });
  }else{res.writeHead(405);res.end();}
});
server.listen(PORT,'0.0.0.0',()=>console.log('serving',ROOT,'on',PORT));
process.on('uncaughtException',()=>{});
`;

export function isHostPortAllowed(p) {
  return HOST_PORTS.includes(Number(p));
}

// 语义检查（与 sandbox.isBuildDirAllowed 一致），防止把任意宿主目录挂进容器。
function assertBuildDirAllowed(buildDir) {
  const ws = process.env.WORKSPACE_DIR
    ? path.resolve(process.env.WORKSPACE_DIR)
    : path.resolve(process.cwd(), '../workspace');
  const resolved = path.resolve(buildDir);
  const rel = path.relative(ws, resolved);
  if (rel.startsWith('..') || path.isAbsolute(rel)) throw new Error('非法 build 目录');
  const parts = rel.split(path.sep);
  if (!(parts.length === 2 && parts[0].startsWith('session-') && parts[1] === 'build')) {
    throw new Error('build 目录必须位于 workspace/session-*/build 下');
  }
}

async function findFreePort(sessionId, excluding = [], preferred = null) {
  const ordered = preferred && HOST_PORTS.includes(Number(preferred))
    ? [Number(preferred), ...HOST_PORTS.filter((p) => p !== Number(preferred))]
    : HOST_PORTS;
  for (const p of ordered) {
    if (excluding.includes(p)) continue;
    const free = await new Promise((resolve) => {
      const srv = net.createServer();
      srv.once('error', () => resolve(false));
      srv.listen(p, '0.0.0.0', () => srv.close(() => resolve(true)));
    });
    if (free) return p;
  }
  return null;
}

// 查询某会话当前运行中的测试容器（按 label，权威来源是 docker 而非 DB）
export async function getSessionContainer(sessionId) {
  const list = await docker.listContainers({
    all: false,
    filters: JSON.stringify({ label: ['nl2e.deploy=1', `nl2e.session=${sessionId}`] }),
  });
  if (list.length === 0) return null;
  const c = list[0];
  return {
    containerId: c.Id,
    name: (c.Names[0] || '').replace(/^\//, ''),
    hostPort: Number((c.Labels || {})['nl2e.port']) || null,
  };
}

// 依据 label 清理旧测试容器（同一会话的部署容器或全部同类）。
async function removeOldContainers(sessionId) {
  const list = await docker.listContainers({
    all: true,
    filters: JSON.stringify({ label: ['nl2e.deploy=1'] }),
  });
  for (const c of list) {
    const labels = c.Labels || {};
    // 同会话旧容器必须停；全局同名旧容器也停，保证"新拉起即作废旧容器"
    if (labels['nl2e.session'] === String(sessionId) || c.Names.some((n) => n.endsWith(`-${sessionId}`))) {
      try {
        await docker.getContainer(c.Id).kill().catch(() => {});
        await docker.getContainer(c.Id).remove({ force: true }).catch(() => {});
        console.log(`[deployer] 停用旧测试容器 ${c.Id.slice(0, 12)} (session ${sessionId})`);
      } catch (err) {
        console.error(`[deployer] 停旧容器失败: ${err.message}`);
      }
    }
  }
}

export async function deployStaticApp(sessionId, buildDir, { preferredPort = null } = {}) {
  assertBuildDirAllowed(buildDir);
  if (!buildDir) throw new Error('缺少 build 目录');
  // 校验产物存在
  const idx = path.join(buildDir, 'index.html');
  await fs.access(idx).catch(() => {
    throw new Error('构建产物缺失 index.html，请先完成构建');
  });

  // 1) 注销旧的同会话测试容器
  await removeOldContainers(sessionId);

  // 2) 占端口（优先复用旧端口，保证用户已收藏的 URL 不变）
  const hostPort = await findFreePort(sessionId, [], preferredPort);
  if (!hostPort) throw new Error(`端口 ${HOST_PORTS.join('/')} 均被占用，无法拉起容器`);

  // 3) 创建并启动容器：只读挂载 build 产物，固定内存/CPU/硬盘/带宽配额
  const cmd = ['node', '-e', staticServer];
  const baseConfig = {
    name: containerName(sessionId),
    Image: CONTAINER_IMAGE,
    Cmd: cmd,
    Env: [`PORT=${CONTAINER_PORT}`],
    Labels: { ...LABEL, 'nl2e.session': String(sessionId), 'nl2e.port': String(hostPort) },
    HostConfig: {
      Binds: [`${path.resolve(buildDir)}:/app:ro`],
      PortBindings: { [`${CONTAINER_PORT}/tcp`]: [{ HostIp: '0.0.0.0', HostPort: String(hostPort) }] },
      Memory: CONTAINER_MEM_BYTES,
      NanoCpus: CONTAINER_NANO_CPUS,
      PidsLimit: 100,
      ReadonlyRootfs: true,
      RestartPolicy: { Name: 'no' },
    },
    ExposedPorts: { [`${CONTAINER_PORT}/tcp`]: {} },
  };
  let container;
  try {
    // 硬盘限额依赖 backing fs（xfs pquota/zfs/btrfs）；不支持会抛错，降级重试
    container = await docker.createContainer({
      ...baseConfig,
      HostConfig: { ...baseConfig.HostConfig, StorageOpt: { size: CONTAINER_DISK_SIZE } },
    });
  } catch (err) {
    console.warn(`[deployer] 硬盘限额不可用（${String(err.message || err).slice(0, 120)}），跳过 StorageOpt 重试`);
    container = await docker.createContainer(baseConfig);
  }
  await container.start();

  // 4) 探活：最多 15s 等 /index.html 返回 200
  const base = `http://127.0.0.1:${hostPort}`;
  const ok = await probe(base, 15);
  if (!ok) await container.remove({ force: true }).catch(() => {});
  if (!ok) throw new Error(`容器已启动但探活失败（${base}）`);

  return { containerId: container.id, hostPort, url: `http://127.0.0.1:${hostPort}/` };
}

async function probe(base, { path: p = '/index.html', timeout = 15000 } = {}) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    try {
      const r = await fetch(`${base}${p}`);
      if (r.ok && (await r.text()).length > 0) return true;
    } catch {
      /* 未就绪，继续轮询 */
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  return false;
}