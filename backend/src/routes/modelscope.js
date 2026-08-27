import { Router } from 'express';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pipeline } from 'node:stream/promises';
import { Readable } from 'node:stream';
import { createWriteStream } from 'node:fs';
import { pool } from '../db.js';
import { authenticate } from './auth.js';

const router = Router();
router.use(authenticate);

const WORKSPACE = process.env.WORKSPACE_DIR || path.join(process.cwd(), '../workspace');
const MS_BASE = 'https://www.modelscope.cn';

// ① 搜索 skill（代理转发，无需 Token）
router.get('/modelscope/skills/search', async (req, res) => {
  const { q = '', page = 1, size = 10 } = req.query;
  try {
    const url = new URL('/openapi/v1/skills', MS_BASE);
    url.searchParams.set('page_number', String(page));
    url.searchParams.set('page_size', String(size));
    if (q) url.searchParams.set('search', q);
    const r = await fetch(url, { headers: { 'Accept': 'application/json' } });
    const data = await r.json();
    res.json(data);
  } catch (err) {
    console.error('[modelscope] search error:', err);
    res.status(502).json({ message: 'ModelScope 搜索失败' });
  }
});

// ② 已安装列表（必须在 :owner/:name 之前，避免路由冲突）
router.get('/modelscope/skills/installed/:sessionId', async (req, res) => {
  const session = (await pool.query('SELECT * FROM sessions WHERE id=$1 AND user_id=$2', [req.params.sessionId, req.user.id])).rows[0];
  if (!session) return res.status(404).json({ message: '会话不存在' });

  const skillsDir = path.join(WORKSPACE, session.folder, 'skills');
  try {
    const entries = await fs.readdir(skillsDir, { withFileTypes: true });
    const skills = entries
      .filter((e) => e.isDirectory())
      .map((e) => {
        const [owner, ...rest] = e.name.split('--');
        return { id: `@${owner}/${rest.join('--')}`, dir: e.name };
      });
    res.json({ skills });
  } catch {
    res.json({ skills: [] });
  }
});

// ③ skill 详情（代理转发，无需 Token）
router.get('/modelscope/skills/:owner/:name', async (req, res) => {
  // Express params 会保留 @ 前缀（如 @steipete → owner=@steipete），需清理
  const owner = req.params.owner.replace(/^@/, '');
  const name = req.params.name;
  try {
    const url = new URL(`/openapi/v1/skills/@${owner}/${name}`, MS_BASE);
    const r = await fetch(url, { headers: { 'Accept': 'application/json' } });
    const data = await r.json();
    res.json(data);
  } catch (err) {
    console.error('[modelscope] detail error:', err);
    res.status(502).json({ message: '获取技能详情失败' });
  }
});

// ④ 安装 skill（用 modelscope Python SDK 下载，复制到 session/skills/）
router.post('/modelscope/skills/install', async (req, res) => {
  const { sessionId, skillId } = req.body;
  if (!sessionId || !skillId) {
    return res.status(400).json({ message: '缺少 sessionId 或 skillId' });
  }

  const session = (await pool.query('SELECT * FROM sessions WHERE id=$1 AND user_id=$2', [sessionId, req.user.id])).rows[0];
  if (!session) return res.status(404).json({ message: '会话不存在' });

  const normalizedId = skillId.startsWith('@') ? skillId : `@${skillId}`;
  const [owner, name] = normalizedId.replace(/^@/, '').split('/');
  if (!owner || !name) return res.status(400).json({ message: 'skillId 格式无效，应为 @owner/name' });

  const skillsDir = path.join(WORKSPACE, session.folder, 'skills', `${owner}--${name}`);
  const cacheDir = path.join(WORKSPACE, '.cache', 'modelscope-skills', `${owner}--${name}`);

  try {
    const { execFile } = await import('node:child_process');
    const { promisify } = await import('node:util');
    const execFileP = promisify(execFile);

    // 1) 用 modelscope SDK 下载到缓存目录
    await fs.mkdir(cacheDir, { recursive: true });
    const dlScript = `
import sys
from modelscope.hub.api import HubApi
api = HubApi()
skill_dir = api.download_skill(skill_id='${normalizedId}')
print(skill_dir)
`;
    const { stdout } = await execFileP('python3', ['-c', dlScript], {
      timeout: 120000,
      cwd: cacheDir,
    });
    const downloadedPath = stdout.trim().split('\n').pop();

    // 2) 复制到 session skills 目录
    await fs.rm(skillsDir, { recursive: true, force: true }).catch(() => {});
    await fs.cp(downloadedPath, skillsDir, { recursive: true });

    // 3) 读取 skill 描述
    let description = '';
    for (const md of ['SKILL.md', 'README.md', 'readme.md']) {
      try {
        description = await fs.readFile(path.join(skillsDir, md), 'utf8');
        break;
      } catch {}
    }

    res.json({
      message: '技能安装成功',
      skillId: normalizedId,
      installPath: `${session.folder}/skills/${owner}--${name}`,
      description: description.slice(0, 2000),
    });
  } catch (err) {
    console.error('[modelscope] install error:', err);
    res.status(500).json({ message: err.message || '安装技能失败（需 modelscope Python 包）' });
  }
});

export default router;
