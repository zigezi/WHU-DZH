import { Router } from 'express';
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pool } from '../db.js';

const require = createRequire(import.meta.url);
const { ZipArchive } = require('archiver');
import { authenticate } from './auth.js';
import { askExplorationQuestion, draftRequirementDoc, buildHistory, convertToEars } from '../ai.js';

const EARS_PROMPT_FILE = process.env.EARS_PROMPT_FILE || path.join(process.cwd(), '..', 'ears-convert.prompt.md');

async function findRequirementFile(dir) {
  const files = await fs.readdir(dir);
  const reqs = files
    .filter((f) => /^requirements.*\.md$/i.test(f))
    .sort()
    .reverse();
  return reqs.length ? reqs[0] : null;
}

const router = Router();
router.use(authenticate);

const WORKSPACE = process.env.WORKSPACE_DIR || path.join(process.cwd(), '../workspace');

function timestampName() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
}

function sessionFolder(row) {
  return path.join(WORKSPACE, row.folder);
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

async function aiReply(session, history) {
  const reply = await askExplorationQuestion(history);
  const inserted = await pool.query(
    'INSERT INTO messages (user_id, session_id, role, content) VALUES ($1,$2,$3,$4) RETURNING id, role, content, created_at',
    [session.user_id, session.id, 'assistant', reply],
  );
  return inserted.rows[0];
}

router.get('/sessions', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT id, name, folder, status, created_at FROM sessions WHERE user_id=$1 ORDER BY created_at DESC',
      [req.user.id],
    );
    res.json({ sessions: result.rows });
  } catch (err) {
    console.error('list sessions error:', err);
    res.status(500).json({ message: '服务器错误' });
  }
});

router.post('/sessions', async (req, res) => {
  const { name = '' } = req.body || {};
  const folder = `session-${timestampName()}`;
  try {
    await fs.mkdir(path.join(WORKSPACE, folder), { recursive: true });
    const result = await pool.query(
      'INSERT INTO sessions (user_id, name, folder) VALUES ($1,$2,$3) RETURNING id, name, folder, status, created_at',
      [req.user.id, String(name).trim(), folder],
    );
    const session = result.rows[0];
    let opening = null;
    try {
      const reply = await askExplorationQuestion([]);
      const inserted = await pool.query(
        'INSERT INTO messages (user_id, session_id, role, content) VALUES ($1,$2,$3,$4) RETURNING id, role, content, created_at',
        [req.user.id, session.id, 'assistant', reply],
      );
      opening = inserted.rows[0];
    } catch (err) {
      console.error('opening question error:', err.message);
    }
    res.status(201).json({ session, opening, message: '会话已创建' });
  } catch (err) {
    console.error('create session error:', err);
    res.status(500).json({ message: '服务器错误' });
  }
});

router.get('/sessions/:id/messages', async (req, res) => {
  const session = await requireSession(req, res);
  if (!session) return;
  try {
    const result = await pool.query(
      'SELECT id, role, content, created_at FROM messages WHERE session_id=$1 ORDER BY created_at ASC, id ASC',
      [session.id],
    );
    res.json({ messages: result.rows });
  } catch (err) {
    console.error('list messages error:', err);
    res.status(500).json({ message: '服务器错误' });
  }
});

router.post('/sessions/:id/messages', async (req, res) => {
  const session = await requireSession(req, res);
  if (!session) return;
  const { content } = req.body || {};
  if (typeof content !== 'string' || !content.trim()) {
    return res.status(400).json({ message: '消息内容不能为空' });
  }
  if (content.trim().length > 2000) {
    return res.status(400).json({ message: '消息过长（最多2000字）' });
  }
  try {
    const userMsg = await pool.query(
      'INSERT INTO messages (user_id, session_id, role, content) VALUES ($1,$2,$3,$4) RETURNING id, role, content, created_at',
      [session.user_id, session.id, 'user', content.trim()],
    );
    const historyRows = await pool.query(
      'SELECT role, content FROM messages WHERE session_id=$1 ORDER BY created_at ASC, id ASC',
      [session.id],
    );
    const aiMsg = await aiReply(session, buildHistory(historyRows.rows));
    await pool.query('UPDATE sessions SET updated_at=now() WHERE id=$1', [session.id]);
    res.status(201).json({ user: userMsg.rows[0], assistant: aiMsg });
  } catch (err) {
    console.error('post message error:', err);
    res.status(500).json({ message: 'AI 回复失败，请稍后重试' });
  }
});

router.get('/sessions/:id/download', async (req, res) => {
  const session = await requireSession(req, res);
  if (!session) return;
  const dir = sessionFolder(session);
  let stat;
  try {
    stat = await fs.stat(dir);
  } catch {
    return res.status(404).json({ message: '尚未生成产物，无文件可下载' });
  }
  if (!stat.isDirectory()) {
    return res.status(404).json({ message: '产物数据异常' });
  }
  const archive = new ZipArchive({ zlib: { level: 9 } });
  res.setHeader('Content-Type', 'application/zip');
  res.setHeader('Content-Disposition', `attachment; filename="${encodeURIComponent(session.folder)}.zip"`);
  archive.pipe(res);
  archive.directory(dir, session.folder);
  archive.on('error', (err) => {
    console.error('zip error:', err);
    res.destroy(err);
  });
  archive.finalize();
});

router.post('/sessions/:id/ears', async (req, res) => {
  const session = await requireSession(req, res);
  if (!session) return;
  const dir = sessionFolder(session);
  try {
    const reqFile = await findRequirementFile(dir);
    if (!reqFile) {
      return res.status(404).json({ message: '该会话尚未生成需求分析文档，请先完成/归档' });
    }
    const requirementContent = await fs.readFile(path.join(dir, reqFile), 'utf8');
    let promptContent;
    try {
      promptContent = await fs.readFile(EARS_PROMPT_FILE, 'utf8');
    } catch {
      return res.status(500).json({ message: `未找到 EARS 任务提示词文件: ${EARS_PROMPT_FILE}` });
    }
    const earsDoc = await convertToEars(promptContent, requirementContent);
    const outFile = `${reqFile.replace(/\.md$/i, '')}-ears.md`;
    await fs.writeFile(path.join(dir, outFile), earsDoc, 'utf8');
    res.json({ message: 'EARS 转换成功', file: `${session.folder}/${outFile}` });
  } catch (err) {
    console.error('ears convert error:', err);
    res.status(500).json({ message: 'EARS 转换失败，请稍后重试' });
  }
});

router.post('/sessions/:id/archive', async (req, res) => {
  const session = await requireSession(req, res);
  if (!session) return;
  if (session.status === 'archived') {
    return res.status(400).json({ message: '该会话已归档' });
  }
  try {
    const historyRows = await pool.query(
      'SELECT role, content FROM messages WHERE session_id=$1 ORDER BY created_at ASC, id ASC',
      [session.id],
    );
    if (historyRows.rowCount === 0) {
      return res.status(400).json({ message: '还没有任何对话内容，无法生成文档' });
    }
    const doc = await draftRequirementDoc(buildHistory(historyRows.rows));
    const dir = sessionFolder(session);
    const filename = `requirements-${timestampName()}.md`;
    await fs.mkdir(dir, { recursive: true });
    await fs.writeFile(path.join(dir, filename), doc, 'utf8');
    await pool.query("UPDATE sessions SET status='archived', updated_at=now() WHERE id=$1", [session.id]);
    res.json({ message: '已归档并生成需求分析文档', file: `${session.folder}/${filename}`, status: 'archived' });
  } catch (err) {
    console.error('archive error:', err);
    res.status(500).json({ message: '生成文档失败，请重试' });
  }
});

export default router;
