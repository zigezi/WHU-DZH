import { Router } from 'express';
import jwt from 'jsonwebtoken';
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pool } from '../db.js';
import { JWT_SECRET, authenticate } from './auth.js';
import { startBuild, applyModification, revalidate, restoreBuild, logBuildEvent } from '../builder.js';
import { pullTemplateImage, CONTAINER_IMAGE } from '../sandbox.js';

const require = createRequire(import.meta.url);
const { ZipArchive } = require('archiver');

const WORKSPACE = process.env.WORKSPACE_DIR || path.join(process.cwd(), '../workspace');

function sessionFolder(session) {
  return path.join(WORKSPACE, session.folder);
}

const ACTIVE_STATUSES = ['queued', 'coding', 'validating', 'debugging', 'modifying'];

// ---------- token 辅助（preview / events 使用查询参数或 cookie） ----------

function parseCookies(header) {
  const out = {};
  if (!header) return out;
  for (const part of header.split(';')) {
    const i = part.indexOf('=');
    if (i > 0) out[part.slice(0, i).trim()] = decodeURIComponent(part.slice(i + 1).trim());
  }
  return out;
}

function authFromToken(req) {
  const cookies = parseCookies(req.headers.cookie || '');
  const token =
    req.query.token ||
    cookies.preview_auth ||
    (req.headers.authorization || '').replace(/^Bearer\s+/, '');
  if (!token) return null;
  try {
    return jwt.verify(token, JWT_SECRET);
  } catch {
    return null;
  }
}

async function requireSession(req, res) {
  const { id } = req.params;
  const result = await pool.query('SELECT * FROM sessions WHERE id=$1 AND user_id=$2', [id, req.user.id]);
  if (result.rowCount === 0) {
    res.status(404).json({ message: '会话不存在' });
    return null;
  }
  return result.rows[0];
}

async function findEarsFile(dir) {
  const files = await fs.readdir(dir).catch(() => []);
  const ears = files.filter((f) => /-ears\.md$/i.test(f)).sort().reverse();
  return ears[0] || null;
}

async function activeBuildForSession(sessionId) {
  const r = await pool.query('SELECT id, status FROM builds WHERE session_id=$1 ORDER BY id DESC LIMIT 1', [sessionId]);
  if (r.rowCount === 0) return null;
  const b = r.rows[0];
  if (ACTIVE_STATUSES.includes(b.status)) return b;
  return null;
}

function buildDirOf(session) {
  return path.join(sessionFolder(session), 'build');
}

async function requireBuildForUser(buildId, userId) {
  const r = await pool.query(
    'SELECT b.* FROM builds b JOIN sessions s ON s.id=b.session_id WHERE b.id=$1 AND s.user_id=$2',
    [buildId, userId],
  );
  return r.rows[0] || null;
}

const router = Router();
// 普通接口走 Authorization 头；events/preview 用 EventSource/iframe，只能带 ?token=，故 query token 也放行。
router.use((req, res, next) => {
  if (req.query && typeof req.query.token === 'string' && req.query.token) {
    try {
      req.user = jwt.verify(req.query.token, JWT_SECRET);
      return next();
    } catch {
      return res.status(401).json({ message: '登录已过期' });
    }
  }
  return authenticate(req, res, next);
});

// 构建状态查询（前端面板入口判断用）
router.get('/sessions/:id/build', async (req, res) => {
  const session = await requireSession(req, res);
  if (!session) return;
  try {
    const earsFile = await findEarsFile(sessionFolder(session));
    const b = (await pool.query('SELECT id, status, iterations, error_summary, created_at FROM builds WHERE session_id=$1 ORDER BY id DESC LIMIT 1', [session.id])).rows[0] || null;
    res.json({ ears: !!earsFile, build: b });
  } catch (err) {
    console.error('build state error:', err);
    res.status(500).json({ message: '服务器错误' });
  }
});

// ---------- 触发构建 ----------

router.post('/sessions/:id/build', async (req, res) => {
  const session = await requireSession(req, res);
  if (!session) return;
  const dir = sessionFolder(session);

  try {
    const earsFile = await findEarsFile(dir);
    if (!earsFile) {
      return res.status(409).json({ message: '该会话尚未生成 EARS 文档，请先完成 EARS 转换' });
    }
    const active = await activeBuildForSession(session.id);
    if (active) {
      return res.status(409).json({ message: `该会话已有进行中的构建（状态 ${active.status}）` });
    }
    const lastBuild = (await pool.query('SELECT id FROM builds WHERE session_id=$1 ORDER BY id DESC LIMIT 1', [session.id])).rows[0];
    if (lastBuild) {
      return res.status(409).json({ message: '该会话已有构建产物，请使用「修改应用」或「重新验证」' });
    }
    const imageReady = await pullTemplateImage();
    if (!imageReady) {
      return res.status(503).json({ message: `沙箱镜像 ${CONTAINER_IMAGE} 缺失，请先执行 setup-build-env.sh` });
    }
    const created = await pool.query(
      "INSERT INTO builds (session_id, user_id, status) VALUES ($1,$2,'queued') RETURNING id",
      [session.id, req.user.id],
    );
    const buildId = created.rows[0].id;
    res.status(201).json({ buildId });
    startBuild(session.id, req.user.id, buildId);
  } catch (err) {
    console.error('trigger build error:', err);
    res.status(500).json({ message: '触发构建失败，请稍后重试' });
  }
});

// ---------- 增量修改 / 重新验证 ----------

router.post('/builds/:id/modify', async (req, res) => {
  const { id } = req.params;
  const { instruction } = req.body || {};
  if (typeof instruction !== 'string' || !instruction.trim()) {
    return res.status(400).json({ message: '修改指令不能为空' });
  }
  const build = await requireBuildForUser(id, req.user.id);
  if (!build) return res.status(404).json({ message: '构建不存在' });
  if (!['passed', 'failed'].includes(build.status)) {
    return res.status(409).json({ message: `构建处于 ${build.status}，需等待终态后才能修改` });
  }
  try {
    await pool.query("UPDATE builds SET status='modifying', iterations=0, error_summary=NULL, finished_at=NULL WHERE id=$1", [build.id]);
    await logBuildEvent(build.id, 'coder', 'status', 'modifying');
    res.json({ buildId: build.id });
    applyModification(build.id, instruction.trim(), req.user.id);
  } catch (err) {
    console.error('modify error:', err);
    res.status(500).json({ message: '增量修改失败，请稍后重试' });
  }
});

router.post('/builds/:id/revalidate', async (req, res) => {
  const { id } = req.params;
  const build = await requireBuildForUser(id, req.user.id);
  if (!build) return res.status(404).json({ message: '构建不存在' });
  if (!['passed', 'failed'].includes(build.status)) {
    return res.status(409).json({ message: `构建处于 ${build.status}，需等待终态后才能重新验证` });
  }
  try {
    await pool.query("UPDATE builds SET status='validating', iterations=0, error_summary=NULL, finished_at=NULL WHERE id=$1", [build.id]);
    await logBuildEvent(build.id, 'sandbox', 'status', 'validating');
    res.json({ buildId: build.id });
    revalidate(build.id, req.user.id);
  } catch (err) {
    console.error('revalidate error:', err);
    res.status(500).json({ message: '重新验证失败，请稍后重试' });
  }
});

// ---------- SSE 事件流 ----------

router.get('/builds/:id/events', async (req, res) => {
  const { id } = req.params;
  const user = authFromToken(req);
  if (!user) return res.status(401).json({ message: '未登录' });
  const build = await requireBuildForUser(id, user.id);
  if (!build) return res.status(403).json({ message: '无权访问该构建' });

  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'X-Accel-Buffering': 'no',
    Connection: 'keep-alive',
  });
  res.flushHeaders();

  let closed = false;
  let lastId = parseInt(req.headers['last-event-id'] || req.query.after || 0, 10) || 0;
  let heartbeatTimer;
  let pollTimer;

  const send = (type, data) => {
    if (closed) return;
    const idVal = data && data.id ? data.id : Date.now();
    res.write(`id: ${idVal}\n`);
    res.write(`event: ${type}\n`);
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  };

  // 先推送一次当前状态快照
  const cur = await pool.query('SELECT id, status, iterations, error_summary FROM builds WHERE id=$1', [id]);
  if (cur.rowCount) send('status', { status: cur.rows[0].status, iterations: cur.rows[0].iterations, error_summary: cur.rows[0].error_summary });

  const poll = async () => {
    if (closed) return;
    try {
      const rows = await pool.query(
        'SELECT id, agent, event_type, content, created_at FROM build_events WHERE build_id=$1 AND id>$2 ORDER BY id ASC',
        [id, lastId],
      );
      for (const r of rows.rows) {
        lastId = r.id;
        if (r.event_type === 'status') {
          send('status', { status: r.content, id: r.id, created_at: r.created_at });
        } else {
          send('event', { agent: r.agent, event_type: r.event_type, content: r.content, id: r.id, created_at: r.created_at });
        }
      }
      const b = (await pool.query('SELECT status FROM builds WHERE id=$1', [id])).rows[0];
      if (b && ['passed', 'failed'].includes(b.status)) {
        send('done', { status: b.status, id: b.id });
        cleanup();
      }
    } catch (err) {
      console.error('SSE poll error:', err);
    }
  };

  const cleanup = () => {
    if (closed) return;
    closed = true;
    clearInterval(heartbeatTimer);
    clearInterval(pollTimer);
    res.end();
  };

  heartbeatTimer = setInterval(() => {
    if (!closed) res.write(': ping\n\n');
  }, 20000);
  pollTimer = setInterval(poll, 1500);
  req.on('close', cleanup);
  req.on('error', cleanup);
});

// ---------- 文件树 / 文件内容 ----------

const TREE_EXCLUDE = new Set(['.git', 'node_modules', '.versions', '_validate.cjs', 'manifest.json']);

async function buildTree(dir, base = '') {
  const out = [];
  let entries;
  try {
    entries = await fs.readdir(dir, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const e of entries) {
    if (TREE_EXCLUDE.has(e.name)) continue;
    const rel = base ? path.join(base, e.name) : e.name;
    if (e.isDirectory()) {
      out.push({ name: e.name, path: rel, type: 'dir', children: await buildTree(path.join(dir, e.name), rel) });
    } else {
      out.push({ name: e.name, path: rel, type: 'file' });
    }
  }
  return out;
}

router.get('/sessions/:id/build/files', async (req, res) => {
  const session = await requireSession(req, res);
  if (!session) return;
  const dir = buildDirOf(session);
  try {
    const stat = await fs.stat(dir);
    if (!stat.isDirectory()) return res.status(404).json({ message: '尚未构建' });
    const tree = await buildTree(dir);
    res.json({ files: tree });
  } catch {
    res.status(404).json({ message: '尚未构建，无文件' });
  }
});

router.get('/sessions/:id/build/file', async (req, res) => {
  const session = await requireSession(req, res);
  if (!session) return;
  const rel = req.query.path;
  if (typeof rel !== 'string' || !rel || rel.includes('\0')) return res.status(400).json({ message: '非法路径' });
  const buildDir = buildDirOf(session);
  const abs = path.resolve(buildDir, rel);
  if (abs !== buildDir && !abs.startsWith(buildDir + path.sep)) return res.status(400).json({ message: '非法路径' });
  try {
    const st = await fs.stat(abs);
    if (!st.isFile()) return res.status(404).json({ message: '不是文件' });
    if (st.size > 100 * 1024) return res.status(413).json({ message: '文件超过 100KB' });
    const content = await fs.readFile(abs, 'utf8');
    res.json({ path: rel, content });
  } catch {
    res.status(404).json({ message: '文件不存在' });
  }
});

// ---------- 版本列表 / 回滚 ----------

router.get('/sessions/:id/build/versions', async (req, res) => {
  const session = await requireSession(req, res);
  if (!session) return;
  const buildDir = buildDirOf(session);
  try {
    const { execFile } = await import('node:child_process');
    const { promisify } = await import('node:util');
    const execFileP = promisify(execFile);
    const { stdout } = await execFileP(
      'git',
      ['-C', buildDir, 'log', '--pretty=format:%H%x1f%s%x1f%ct'],
      { maxBuffer: 4 * 1024 * 1024 },
    );
    const versions = stdout.split('\n').filter(Boolean).map((line) => {
      const [hash, message, ts] = line.split('\x1f');
      return { hash, message, time: new Date(Number(ts) * 1000).toISOString() };
    });
    res.json({ versions });
  } catch {
    // git 不可用：列出快照
    const vdir = path.join(buildDir, '.versions');
    try {
      const names = (await fs.readdir(vdir)).filter((n) => /^\d+$/.test(n)).sort((a, b) => Number(a) - Number(b));
      const versions = [];
      for (const n of names) {
        const tag = await fs.readFile(path.join(vdir, n, '.tag'), 'utf8').catch(() => `snapshot ${n}`);
        versions.push({ hash: n, message: tag, time: '' });
      }
      return res.json({ versions, snapshot: true });
    } catch {
      res.json({ versions: [] });
    }
  }
});

router.post('/sessions/:id/build/restore', async (req, res) => {
  const session = await requireSession(req, res);
  if (!session) return;
  const { hash } = req.body || {};
  if (typeof hash !== 'string' || !/^[0-9a-f]{7,40}$/.test(hash)) {
    return res.status(400).json({ message: '非法版本号' });
  }
  const build = (await pool.query('SELECT id, status FROM builds WHERE session_id=$1 ORDER BY id DESC LIMIT 1', [session.id])).rows[0];
  if (!build || !['passed', 'failed'].includes(build.status)) {
    return res.status(409).json({ message: '当前无终态构建，无法回滚' });
  }
  try {
    await pool.query("UPDATE builds SET status='validating', iterations=0, error_summary=NULL, finished_at=NULL WHERE id=$1", [build.id]);
    await logBuildEvent(build.id, 'system', 'log', `用户请求恢复到版本 ${hash}`);
    res.json({ buildId: build.id });
    restoreBuild(build.id, hash, req.user.id);
  } catch (err) {
    console.error('restore error:', err);
    res.status(500).json({ message: '回滚失败，请稍后重试' });
  }
});

// ---------- 下载 ZIP ----------

router.get('/sessions/:id/build/download', async (req, res) => {
  const session = await requireSession(req, res);
  if (!session) return;
  const buildDir = buildDirOf(session);
  try {
    const stat = await fs.stat(buildDir);
    if (!stat.isDirectory()) return res.status(404).json({ message: '尚未构建' });
  } catch {
    return res.status(404).json({ message: '尚未构建' });
  }

  const archive = new ZipArchive({ zlib: { level: 9 } });
  res.setHeader('Content-Type', 'application/zip');
  res.setHeader('Content-Disposition', `attachment; filename="${encodeURIComponent(`${session.folder}-build`)}.zip"`);
  archive.pipe(res);
  archive.glob('**/*', {
    cwd: buildDir,
    ignore: ['**/.git/**', '**/node_modules/**', '**/.versions/**', '**/_validate.cjs', '**/manifest.json'],
    dot: false,
  });
  archive.on('error', (err) => {
    console.error('zip error:', err);
    res.destroy(err);
  });
  archive.finalize();
});

export default router;

// ---------- Preview 路由（独立挂载到 /preview，token/cookie 鉴权） ----------

export const previewRouter = Router();

function sendPreviewError(res, code, msg) {
  res.status(code).send(`<!doctype html><meta charset="utf-8"><title>Preview</title><p>${msg}</p>`);
}

previewRouter.get('/:sessionId/*', async (req, res) => {
  const { sessionId } = req.params;
  const rest = (req.params[0] || '').replace(/^\/+/, '');

  const user = authFromToken(req);
  if (!user) {
    return sendPreviewError(res, 401, '未授权访问预览');
  }
  const session = (await pool.query('SELECT * FROM sessions WHERE id=$1 AND user_id=$2', [sessionId, user.id])).rows[0];
  if (!session) return sendPreviewError(res, 403, '无权访问该预览');

  const buildDir = buildDirOf(session);

  // 首次带 token 访问：下发 HttpOnly cookie 后 302 到无 token URL，避免 token 落访问日志/浏览器历史。
  if (req.query.token && !parseCookies(req.headers.cookie || '').preview_auth) {
    res.setHeader('Set-Cookie', `preview_auth=${encodeURIComponent(req.query.token)}; HttpOnly; Path=/preview/${sessionId}/; SameSite=Strict`);
    const target = `/preview/${sessionId}/${rest}`;
    return res.redirect(302, target);
  }

  const abs = path.resolve(buildDir, rest || 'index.html');
  if (abs !== buildDir && !abs.startsWith(buildDir + path.sep)) {
    return sendPreviewError(res, 400, '非法路径');
  }
  let st;
  try {
    st = await fs.stat(abs);
  } catch {
    return sendPreviewError(res, 404, '文件不存在');
  }
  if (st.isDirectory()) {
    return sendPreviewError(res, 403, '目录不可预览');
  }
  res.setHeader('Content-Security-Policy', "default-src 'self' 'unsafe-inline'; img-src 'self' data:;");
  res.sendFile(abs);
});