import { Router } from 'express';
import { authenticate } from './auth.js';

const router = Router();
router.use(authenticate);

// 远程向量服务（新机 2C8G）地址。经安全组限定仅主服务器可访问，故无需额外鉴权。
const VECTOR_BASE = process.env.VECTOR_API_BASE || 'http://8.138.36.148:8000';
const TIMEOUT_MS = 10000;

async function proxy(res, urlPath, opts = {}) {
  try {
    const r = await fetch(`${VECTOR_BASE}${urlPath}`, {
      ...opts,
      headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    const data = await r.json().catch(() => ({}));
    res.status(r.status).json(data);
  } catch (err) {
    console.error('[vector] proxy error:', err.message);
    res.status(502).json({ message: '向量服务不可达（远端或网络异常）', error: err.message });
  }
}

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

// 向量总数
router.get('/vector/vectors/count', (_req, res) => proxy(res, '/vectors/count'));

// 插入向量 { content, embedding }
router.post('/vector/vectors', (req, res) =>
  proxy(res, '/vectors', { method: 'POST', body: JSON.stringify(req.body) }));

// 相似搜索 { embedding, top_k }
router.post('/vector/search', (req, res) =>
  proxy(res, '/search', { method: 'POST', body: JSON.stringify(req.body) }));

export default router;
