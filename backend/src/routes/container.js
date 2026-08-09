import { Router } from 'express';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pool } from '../db.js';
import { authenticate } from './auth.js';
import { deployStaticApp } from '../deployer.js';

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
    const st = await fs.stat(path.join(buildDir, 'index.html'));
    return st.isFile() ? buildDir : null;
  } catch {
    return null;
  }
}

async function recordDeploy(sessionId, userId, hostPort, url) {
  const r = await pool.query(
    `INSERT INTO test_containers (session_id, user_id, host_port, url, status)
     VALUES ($1,$2,$3,$4,'running') RETURNING id`,
    [sessionId, userId, hostPort, url],
  );
  return r.rows[0].id;
}

async function latestDeploy(sessionId) {
  const r = await pool.query(
    'SELECT * FROM test_containers WHERE session_id=$1 ORDER BY id DESC LIMIT 1',
    [sessionId],
  );
  return r.rows[0] || null;
}

// 触发拉起测试容器（复用构建产物；再次拉起会先注销旧容器）
router.post('/sessions/:id/container', async (req, res) => {
  const session = await requireSession(req, res);
  if (!session) return;
  const buildDir = await hasBuildOutput(session);
  if (!buildDir) {
    return res.status(409).json({ message: '该会话尚无构建产物，请先在「构建面板」生成应用' });
  }
  try {
    const { hostPort, url } = await deployStaticApp(session.id, buildDir);
    const deployId = await recordDeploy(session.id, req.user.id, hostPort, url);
    res.json({ deployId, hostPort, url, status: 'running' });
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