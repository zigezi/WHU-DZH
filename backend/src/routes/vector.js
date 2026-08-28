import { Router } from 'express';
import crypto from 'node:crypto';
import { pool } from '../db.js';
import { authenticate } from './auth.js';

const router = Router();

// 远程数据面（新机 2C8G）地址。经安全组限定仅主服务器可访问，故无需额外鉴权。
const VECTOR_BASE = process.env.VECTOR_API_BASE || 'http://8.138.36.148:8000';

// ---------- 双重鉴权 ----------

// 会话级令牌：确保 session 有 api_token（懒生成），返回 token。
export async function ensureSessionApiToken(sessionId) {
  const r = await pool.query('SELECT api_token FROM sessions WHERE id=$1', [sessionId]);
  const row = r.rows[0];
  if (!row) return null;
  if (row.api_token) return row.api_token;
  const token = crypto.randomBytes(24).toString('hex');
  await pool.query('UPDATE sessions SET api_token=$1 WHERE id=$2', [token, sessionId]);
  return token;
}

// JWT（平台用户）或 sessionId+stoken（生成应用）二选一。
// 生成应用身份：req.appSession = { sessionId, namespace }，namespace 强制锁定。
async function dualAuth(req, res, next) {
  if (req.headers.authorization) {
    return authenticate(req, res, next); // 平台用户：全量权限
  }
  const { sessionId, stoken } = req.query;
  if (sessionId && stoken) {
    const r = await pool.query('SELECT api_token FROM sessions WHERE id=$1', [sessionId]);
    const row = r.rows[0];
    if (row && row.api_token && row.api_token === stoken) {
      req.appSession = { sessionId: Number(sessionId), namespace: `sess-${sessionId}` };
      return next();
    }
  }
  return res.status(401).json({ message: '未授权' });
}

router.use('/vector', dualAuth);

// 生成应用的 namespace 强制锁定；平台用户可自定义（默认 default）。
function resolveNamespace(req, bodyNamespace) {
  if (req.appSession) return req.appSession.namespace;
  return bodyNamespace || 'default';
}

// ---------- 代理辅助 ----------

async function proxy(res, urlPath, opts = {}) {
  const timeout = opts.timeoutMs || 10000;
  delete opts.timeoutMs;
  try {
    const r = await fetch(`${VECTOR_BASE}${urlPath}`, {
      ...opts,
      headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
      signal: AbortSignal.timeout(timeout),
    });
    const data = await r.json().catch(() => ({}));
    res.status(r.status).json(data);
  } catch (err) {
    console.error('[vector] proxy error:', err.message);
    res.status(502).json({ message: '向量服务不可达（远端或网络异常）', error: err.message });
  }
}

// ---------- 向量 API ----------

// 健康检查（平台侧增强：返回可达性与延迟）
router.get('/vector/health', async (_req, res) => {
  const started = Date.now();
  try {
    const r = await fetch(`${VECTOR_BASE}/health`, { signal: AbortSignal.timeout(8000) });
    const data = await r.json();
    res.json({ reachable: true, latencyMs: Date.now() - started, base: VECTOR_BASE, remote: data });
  } catch (err) {
    res.status(502).json({ reachable: false, base: VECTOR_BASE, message: '向量服务不可达', error: err.message });
  }
});

// 初始化 pgvector（建扩展+表）
router.post('/vector/init', (_req, res) => proxy(res, '/init', { method: 'POST' }));

// 演示数据（插入 9 条向量并做一次相似搜索）
router.post('/vector/demo', (_req, res) => proxy(res, '/demo', { method: 'POST' }));

// 向量总数（生成应用只能查自己的 namespace）
router.get('/vector/vectors/count', (req, res) => {
  const ns = resolveNamespace(req, req.query.namespace);
  proxy(res, `/vectors/count?namespace=${encodeURIComponent(ns)}`);
});

// 插入向量 { content, embedding, namespace? }（生成应用 namespace 强制 sess-<id>）
router.post('/vector/vectors', (req, res) => {
  const body = { ...req.body, namespace: resolveNamespace(req, req.body?.namespace) };
  proxy(res, '/vectors', { method: 'POST', body: JSON.stringify(body) });
});

// 相似搜索 { embedding, top_k, namespace? }（生成应用 namespace 强制 sess-<id>）
router.post('/vector/search', (req, res) => {
  const body = { ...req.body, namespace: resolveNamespace(req, req.body?.namespace) };
  proxy(res, '/search', { method: 'POST', body: JSON.stringify(body) });
});

// ---------- Skill 运行时 / HTTP 执行原语（仅平台用户，生成应用不可用） ----------

function requirePlatformUser(req, res, next) {
  if (req.appSession) return res.status(403).json({ message: '生成应用无权访问该接口' });
  next();
}

router.post('/vector/skills/install', requirePlatformUser, (req, res) =>
  proxy(res, '/skills/install', { method: 'POST', body: JSON.stringify(req.body), timeoutMs: 180000 }));

router.get('/vector/skills', requirePlatformUser, (_req, res) => proxy(res, '/skills'));

router.get('/vector/skills/:owner/:name/readme', requirePlatformUser, (req, res) =>
  proxy(res, `/skills/${encodeURIComponent(req.params.owner)}/${encodeURIComponent(req.params.name)}/readme`));

router.post('/vector/http/fetch', requirePlatformUser, (req, res) =>
  proxy(res, '/http/fetch', { method: 'POST', body: JSON.stringify(req.body), timeoutMs: 25000 }));

export default router;
