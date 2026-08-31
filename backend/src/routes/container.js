import { Router } from 'express';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pool } from '../db.js';
import { authenticate } from './auth.js';
import { deployStaticApp, deployServiceApp, getSessionContainer, getRemoteService } from '../deployer.js';

const router = Router();
router.use(authenticate);

const WORKSPACE = process.env.WORKSPACE_DIR || path.join(process.cwd(), '../workspace');

async function requireSession(req, res) {
  const { id } = req.params;
  const result = await pool.query('SELECT * FROM sessions WHERE id=$1 AND user_id=$2', [id, req.user.id]);
  if (result.rowCount === 0) {
    res.status(404).json({ message: '会话不存在' });
    return null;
  }
  return result.rows[0];
}

async function hasBuildOutput(session) {
  const buildDir = path.join(WORKSPACE, session.folder, 'build');
  try {
    // static-web 产物为 index.html；node-service 产物为 server.js
    const st = await fs.stat(path.join(buildDir, 'index.html')).catch(() => null);
    if (st && st.isFile()) return buildDir;
    const st2 = await fs.stat(path.join(buildDir, 'server.js')).catch(() => null);
    return st2 && st2.isFile() ? buildDir : null;
  } catch {
    return null;
  }
}

// 读取构建产物运行时（static-web / node-service），决定部署到本机前端容器还是 8G 后端容器。
// manifest 缺失（构建从未通过）时按产物形态推断（server.js → node-service）。
async function readBuildRuntime(session) {
  const buildDir = path.join(WORKSPACE, session.folder, 'build');
  try {
    const m = JSON.parse(await fs.readFile(path.join(buildDir, 'manifest.json'), 'utf8'));
    if (m.runtime === 'node-service' || m.runtime === 'static-web') return m.runtime;
  } catch {
    /* manifest 缺失或不可读，按目录推断 */
  }
  try {
    await fs.access(path.join(buildDir, 'server.js'));
    return 'node-service';
  } catch {
    return 'static-web';
  }
}

async function recordDeploy(sessionId, userId, hostPort, url, containerId) {
  const r = await pool.query(
    `INSERT INTO test_containers (session_id, user_id, host_port, url, status, container_id)
     VALUES ($1,$2,$3,$4,'running',$5) RETURNING id`,
    [sessionId, userId, hostPort, url, containerId || ''],
  );
  return r.rows[0].id;
}

// 把该会话旧的 running 记录标记为 replaced，保持 DB 与 docker 实际状态一致
async function markOldReplaced(sessionId) {
  await pool.query(
    "UPDATE test_containers SET status='replaced' WHERE session_id=$1 AND status='running'",
    [sessionId],
  );
}

async function latestDeploy(sessionId) {
  const r = await pool.query(
    'SELECT * FROM test_containers WHERE session_id=$1 ORDER BY id DESC LIMIT 1',
    [sessionId],
  );
  return r.rows[0] || null;
}

// 触发拉起测试容器。已有运行中容器且未确认替换时返回 409，由前端弹窗确认后带 replace:true 重试。
router.post('/sessions/:id/container', async (req, res) => {
  const session = await requireSession(req, res);
  if (!session) return;
  const buildDir = await hasBuildOutput(session);
  if (!buildDir) {
    return res.status(409).json({ message: '该会话尚无构建产物，请先在「构建面板」生成应用' });
  }
  try {
    const runtime = await readBuildRuntime(session);
    const isService = runtime === 'node-service';
    // 本地静态容器查本机 docker；node-service 查 8G 远程容器
    const existing = isService
      ? await getRemoteService(session.id)
      : await getSessionContainer(session.id);
    if (existing && req.body.replace !== true) {
      const existingUrl = isService
        ? `${process.env.REMOTE_PUBLIC_BASE || 'http://8.138.36.148'}:${existing.hostPort}/`
        : `http://127.0.0.1:${existing.hostPort}/`;
      return res.status(409).json({
        needConfirm: true,
        message: '已有运行中的测试容器',
        existing: { hostPort: existing.hostPort, url: existingUrl },
      });
    }
    const deployFn = isService ? deployServiceApp : deployStaticApp;
    const { containerId, hostPort, url } = await deployFn(session.id, buildDir, {
      preferredPort: existing ? existing.hostPort : null,
    });
    await markOldReplaced(session.id);
    const deployId = await recordDeploy(session.id, req.user.id, hostPort, url, containerId);
    res.json({ deployId, hostPort, url, status: 'running', runtime });
  } catch (err) {
    console.error('deploy container error:', err);
    res.status(500).json({ message: err.message || '拉起测试容器失败' });
  }
});

// 查询当前会话的测试容器状态
router.get('/sessions/:id/container', async (req, res) => {
  const session = await requireSession(req, res);
  if (!session) return;
  const deploy = await latestDeploy(session.id);
  res.json({ deploy });
});

export default router;