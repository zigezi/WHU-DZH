import { Router } from 'express';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pool } from '../db.js';
import { authenticate } from './auth.js';
import { deployStaticApp, getSessionContainer } from '../deployer.js';

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
    const existing = await getSessionContainer(session.id);
    if (existing && req.body.replace !== true) {
      return res.status(409).json({
        needConfirm: true,
        message: '已有运行中的测试容器',
        existing: { hostPort: existing.hostPort, url: `http://127.0.0.1:${existing.hostPort}/` },
      });
    }
    const { containerId, hostPort, url } = await deployStaticApp(session.id, buildDir, {
      preferredPort: existing ? existing.hostPort : null,
    });
    await markOldReplaced(session.id);
    const deployId = await recordDeploy(session.id, req.user.id, hostPort, url, containerId);
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