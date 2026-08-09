import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pool } from './db.js';
import { runValidation, isBuildDirAllowed, CONTAINER_IMAGE } from './sandbox.js';
import { planApp, generateFile, debugFix, rewriteFile, incrementalModify, distillEars } from './ai.js';

const execFileP = promisify(execFile);

const WORKSPACE = process.env.WORKSPACE_DIR || path.join(process.cwd(), '../workspace');
const MAX_ITERATIONS = 8;
const MODIFY_MESSAGE_CAP = 50;

// git 可用性在首次 startBuild 时判定一次并全局缓存，全程一致使用，不得中途切换。
let gitMode = null; // 'git' | 'snapshot'

async function detectGit() {
  if (gitMode) return gitMode;
  try {
    await execFileP('git', ['--version']);
    gitMode = 'git';
    console.log('[builder] git 可用，启用 commit 历史与版本回滚');
  } catch {
    gitMode = 'snapshot';
    console.warn('[builder] git 不可用，降级为 .versions 快照模式（补丁采用全文覆写）');
  }
  return gitMode;
}

function sessionFolder(session) {
  return path.join(WORKSPACE, session.folder);
}

// ---------- DB / 事件辅助 ----------

async function getBuild(buildId) {
  const r = await pool.query('SELECT * FROM builds WHERE id=$1', [buildId]);
  return r.rows[0] || null;
}

async function setStatus(buildId, status) {
  const terminal = ['passed', 'failed'].includes(status);
  await pool.query(
    `UPDATE builds SET status=$1, finished_at = CASE WHEN $2 THEN now() ELSE finished_at END WHERE id=$3`,
    [status, terminal, buildId],
  );
}

async function incrementIterations(buildId) {
  await pool.query('UPDATE builds SET iterations = iterations + 1 WHERE id=$1', [buildId]);
}

async function setErrorSummary(buildId, text) {
  await pool.query('UPDATE builds SET error_summary=$1 WHERE id=$2', [text || null, buildId]);
}

export async function logBuildEvent(buildId, agent, eventType, content) {
  try {
    await pool.query(
      'INSERT INTO build_events (build_id, agent, event_type, content) VALUES ($1,$2,$3,$4)',
      [buildId, agent, eventType, content],
    );
  } catch {
    /* 忽略事件写入失败 */
  }
}

// ---------- 文件系统辅助 ----------

export function sanitizeRelPath(p) {
  const rel = path.normalize(String(p || ''));
  if (!rel || path.isAbsolute(rel) || rel.startsWith('..') || rel.includes('\0') || rel.includes('..' + path.sep)) {
    throw new Error(`非法路径: ${p}`);
  }
  return rel;
}

async function writeFileSafe(buildDir, relPath, content) {
  const rel = sanitizeRelPath(relPath);
  const abs = path.join(buildDir, rel);
  if (!abs.startsWith(buildDir + path.sep) && abs !== buildDir) throw new Error('非法路径');
  await fs.mkdir(path.dirname(abs), { recursive: true });
  await fs.writeFile(abs, content, 'utf8');
}

async function readFileSafe(buildDir, relPath) {
  const rel = sanitizeRelPath(relPath);
  const abs = path.join(buildDir, rel);
  if (!abs.startsWith(buildDir + path.sep)) throw new Error('非法路径');
  return fs.readFile(abs, 'utf8');
}

async function listProjectFiles(buildDir, base = '') {
  const out = [];
  let entries;
  try {
    entries = await fs.readdir(buildDir);
  } catch {
    return out;
  }
  for (const name of entries) {
    if (name === '.git' || name === '.versions' || name === '_validate.cjs' || name === 'manifest.json') continue;
    const abs = path.join(buildDir, name);
    const st = await fs.stat(abs);
    if (st.isDirectory()) out.push(...(await listProjectFiles(abs, path.join(base, name))));
    else out.push(path.join(base, name));
  }
  return out;
}

async function collectFilesText(buildDir) {
  const files = await listProjectFiles(buildDir);
  let text = '';
  for (const rel of files) {
    let content;
    try {
      content = await readFileSafe(buildDir, rel);
    } catch {
      continue;
    }
    text += `===== ${rel} =====\n${content}\n\n`;
    if (text.length > 100_000) {
      text += '\n...（内容过长已裁剪）\n';
      break;
    }
  }
  return { text, files };
}

// 从 manifest.json（若存在）读取每文件的 purpose/exports，读取全文内容，组装 fileMetas。
async function collectFileMetas(buildDir) {
  const rels = await listProjectFiles(buildDir);
  const metas = new Map();
  try {
    const manifest = JSON.parse(await fs.readFile(path.join(buildDir, 'manifest.json'), 'utf8'));
    for (const f of manifest.files || []) {
      metas.set(f.path, { purpose: f.purpose || '', exports: f.exports || '' });
    }
  } catch {
    /* 无 manifest 则 fallback 到空元信息 */
  }
  const out = [];
  for (const rel of rels) {
    try {
      const content = await readFileSafe(buildDir, rel);
      const meta = metas.get(rel) || {};
      out.push({ path: rel, purpose: meta.purpose || '', exports: meta.exports || '', content });
    } catch {
      /* 跳过不可读文件 */
    }
  }
  return out;
}

// ---------- git 辅助 ----------

async function git(buildDir, args) {
  const { stdout } = await execFileP('git', ['-C', buildDir, ...args], { maxBuffer: 16 * 1024 * 1024 });
  return stdout.trim();
}

async function gitAvailable() {
  return (await detectGit()) === 'git';
}

async function initRepo(buildDir, mode) {
  if (mode === 'git') {
    await git(buildDir, ['init']);
    await git(buildDir, ['config', 'user.email', 'builder@localhost']);
    await git(buildDir, ['config', 'user.name', 'builder']);
    return 'git';
  }
  await fs.mkdir(path.join(buildDir, '.versions'), { recursive: true });
  return 'snapshot';
}

async function snapshotNumber(buildDir) {
  const dir = path.join(buildDir, '.versions');
  const names = await fs.readdir(dir).catch(() => []);
  return names.length;
}

async function saveSnapshot(buildDir, tag) {
  const n = await snapshotNumber(buildDir);
  const target = path.join(buildDir, '.versions', String(n));
  await fs.mkdir(target, { recursive: true });
  for (const rel of await listProjectFiles(buildDir)) {
    const src = path.join(buildDir, rel);
    const dst = path.join(target, rel);
    await fs.mkdir(path.dirname(dst), { recursive: true });
    await fs.copyFile(src, dst);
  }
  await fs.writeFile(path.join(target, '.tag'), tag || `snapshot ${n}`, 'utf8');
  return n;
}

async function commitState(buildDir, mode, message) {
  const msg = cleanCommitMessage(message);
  if (mode === 'git') {
    await git(buildDir, ['add', '-A']);
    await git(buildDir, ['commit', '-m', msg, '--allow-empty']).catch(async (e) => {
      // 无任何变更时 git commit 会失败，允许空提交作为状态记录
      await git(buildDir, ['commit', '--allow-empty', '-m', msg]);
    });
    return await git(buildDir, ['rev-parse', 'HEAD']);
  }
  return String(await saveSnapshot(buildDir, msg));
}

async function gitApplyPatch(buildDir, diff) {
  const patchFile = path.join(buildDir, '.patch.tmp');
  try {
    await fs.writeFile(patchFile, diff, 'utf8');
    await execFileP('git', ['-C', buildDir, 'apply', '--whitespace=fix', '--recount', patchFile], { maxBuffer: 8 * 1024 * 1024 });
    return true;
  } catch {
    return false;
  } finally {
    await fs.rm(patchFile, { force: true }).catch(() => {});
  }
}

function diffTargetPaths(diff) {
  const paths = [];
  const re = /^\+\+\+ b\/(.+)$/gm;
  let m;
  while ((m = re.exec(diff))) {
    const p = m[1].trim();
    if (p && p !== '/dev/null') paths.push(p);
  }
  return [...new Set(paths)];
}

function firstLine(text) {
  return (text || '').split('\n').find((l) => l.trim()) || '';
}

// 清洗 commit 消息中的 NUL/控制字符（沙箱输出可能含 docker 帧头等二进制），防止 execFile 报 null bytes 错误。
function cleanCommitMessage(msg) {
  return String(msg || '').replace(/[\u0000-\u001f\u007f]/g, '').trim().slice(0, 200) || 'wip';
}

function guessInvolvedFile(buildDir, errTail) {
  const m = /\/app\/([\w.\-/]+\.(?:js|html|cjs))/i.exec(errTail || '');
  if (m) {
    const rel = m[1];
    try {
      fs.statSync(path.join(buildDir, rel));
      return rel;
    } catch {
      /* 该文件不存在，继续回落 */
    }
  }
  return 'index.html';
}

// 从报错尾部提取涉及文件并在 buildDir 读取其内容（其余文件只给路径+导出签名骨架，见 otherFileSignatures）。
async function collectInvolvedFiles(buildDir, errTail) {
  const rels = new Set();
  const re = /\/app\/([\w.\-/]+\.(?:js|html|cjs))/gi;
  let m;
  while ((m = re.exec(errTail || ''))) rels.add(m[1]);
  if (rels.size === 0) rels.add(guessInvolvedFile(buildDir, errTail));
  const out = [];
  for (const rel of rels) {
    try {
      const content = await readFileSafe(buildDir, rel);
      out.push({ path: rel, content });
    } catch {
      out.push({ path: rel, content: '' });
    }
  }
  return out;
}

async function otherFileSignatures(buildDir, involvedRels) {
  const all = await listProjectFiles(buildDir);
  return all
    .filter((rel) => !involvedRels.includes(rel))
    .map((rel) => `${rel}: <导出签名待模型自查>`);
}

async function distillSessionDigest(dir, earsFile) {
  const earsContent = await fs.readFile(path.join(dir, earsFile), 'utf8');
  const cacheFile = path.join(dir, `${earsFile}.digest`);
  try {
    const cached = await fs.readFile(cacheFile, 'utf8');
    if (cached) return cached;
  } catch {
    /* 无缓存则重新蒸馏 */
  }
  const digest = distillEars(earsContent);
  await fs.writeFile(cacheFile, digest, 'utf8').catch(() => {});
  return digest;
}

// ---------- 修复循环 ----------

async function applyFullRewrite(buildId, buildDir, earsDigest, errTail, targetRel, instruction) {
  const rel = targetRel || guessInvolvedFile(buildDir, errTail);
  const current = await readFileSafe(buildDir, rel).catch(() => '');
  const newContent = await rewriteFile(buildId, rel, current, earsDigest, errTail, instruction);
  await writeFileSafe(buildDir, rel, newContent);
  await logBuildEvent(buildId, 'debugger', 'file', `全文覆写 ${rel}${instruction ? '（携带修改指令）' : ''}`);
  return true;
}

// 在 snapshot 模式下 diff 仅用于定位受影响文件，一律全文覆写应用。
async function applyRepairDiff(buildId, buildDir, earsDigest, errTail, diff, mode) {
  if (mode === 'snapshot') {
    const targets = diffTargetPaths(diff);
    if (targets.length === 0) return false;
    for (const rel of targets) await applyFullRewrite(buildId, buildDir, earsDigest, errTail, rel);
    return true;
  }
  return gitApplyPatch(buildDir, diff);
}

// 修复循环：验证 → 失败则 debugging → 出补丁应用 → 复验。最多 MAX_ITERATIONS 轮。
async function repairLoop(buildId, buildDir, earsDigest, mode) {
  let iterations = 0;
  while (true) {
    await setStatus(buildId, 'validating');
    await logBuildEvent(buildId, 'sandbox', 'status', 'validating');
    const result = await runValidation(buildDir);
    const tail = (result.stderrTail || result.stdoutTail || '').slice(0, 3000);
    await logBuildEvent(buildId, 'sandbox', 'log', `验证结束 exitCode=${result.exitCode} errorType=${result.errorType || 'none'}\n${tail}`);

    if (result.passed) {
      return { passed: true, iterations };
    }
    if (result.errorType === 'path') {
      throw new Error(tail || '沙箱路径校验拒绝');
    }

    iterations += 1;
    await incrementIterations(buildId);
    if (iterations > MAX_ITERATIONS) {
      await setStatus(buildId, 'failed');
      await setErrorSummary(buildId, tail || '超过 8 轮修复仍未通过');
      await logBuildEvent(buildId, 'system', 'status', 'failed');
      await logBuildEvent(buildId, 'debugger', 'error', `超过 ${MAX_ITERATIONS} 轮修复仍未通过`);
      return { passed: false, iterations };
    }

    await setStatus(buildId, 'debugging');
    await logBuildEvent(buildId, 'debugger', 'status', 'debugging');

    const involved = await collectInvolvedFiles(buildDir, tail);
    const otherSigs = await otherFileSignatures(buildDir, involved.map((f) => f.path));

    let applied = false;
    if (mode === 'git') {
      for (let attempt = 0; attempt < 2 && !applied; attempt++) {
        let diff;
        try {
          diff = await debugFix(buildId, earsDigest, tail, involved, otherSigs);
        } catch (e) {
          await logBuildEvent(buildId, 'debugger', 'error', `debugFix 失败: ${e.message}`);
          break;
        }
        await logBuildEvent(buildId, 'debugger', 'patch', diff.slice(0, 3000));
        applied = await applyRepairDiff(buildId, buildDir, earsDigest, tail, diff, mode);
        if (!applied) await logBuildEvent(buildId, 'debugger', 'log', '补丁应用失败，将重试');
      }
      if (!applied) {
        await logBuildEvent(buildId, 'debugger', 'log', '连续失败，降级为全文覆写');
        try {
          applied = await applyFullRewrite(buildId, buildDir, earsDigest, tail);
        } catch (e) {
          await logBuildEvent(buildId, 'debugger', 'error', `全文覆写失败: ${e.message}`);
          applied = false;
        }
      }
    } else {
      // snapshot：debugFix 产物仅用于获取受影响文件清单，全文覆写应用
      try {
        const diff = await debugFix(buildId, earsDigest, tail, involved, otherSigs);
        await logBuildEvent(buildId, 'debugger', 'patch', diff.slice(0, 3000));
        applied = await applyRepairDiff(buildId, buildDir, earsDigest, tail, diff, mode);
      } catch (e) {
        await logBuildEvent(buildId, 'debugger', 'error', `debugFix 失败: ${e.message}`);
        applied = false;
      }
      if (!applied) {
        try {
          applied = await applyFullRewrite(buildId, buildDir, earsDigest, tail);
        } catch (e) {
          applied = false;
        }
      }
    }

    if (!applied) {
      await setStatus(buildId, 'failed');
      await setErrorSummary(buildId, '修复补丁连续失败，无法继续');
      return { passed: false, iterations };
    }
    await commitState(buildDir, mode, `fix round ${iterations}: ${firstLine(tail).slice(0, 80)}`);
  }
}

async function writeManifest(buildDir, buildId, entry, files) {
  const row = await getBuild(buildId);
  const head = (await git(buildDir, ['rev-parse', 'HEAD']).catch(() => '')) || String((await snapshotNumber(buildDir)) - 1);
  const manifest = {
    generatedAt: new Date().toISOString(),
    entry: entry || 'index.html',
    runtime: 'static-web',
    iterations: row ? row.iterations : 0,
    files,
    commit: head,
  };
  await fs.writeFile(path.join(buildDir, 'manifest.json'), JSON.stringify(manifest, null, 2), 'utf8');
}

// ---------- 对外接口（fire-and-forget） ----------

export function startBuild(sessionId, userId, buildId) {
  runStartBuild(sessionId, userId, buildId).catch((err) => {
    console.error('[builder] startBuild error:', err);
    if (buildId) {
      setStatus(buildId, 'failed').catch(() => {});
      setErrorSummary(buildId, err.message).catch(() => {});
      logBuildEvent(buildId, 'system', 'error', `构建异常终止: ${err.message}`).catch(() => {});
    }
  });
}

async function runStartBuild(sessionId, userId, buildId) {
  let targetBuildId = buildId;
  if (!targetBuildId) {
    const r = await pool.query(
      "SELECT id FROM builds WHERE session_id=$1 AND user_id=$2 AND status='queued' ORDER BY id DESC LIMIT 1",
      [sessionId, userId],
    );
    targetBuildId = r.rows[0] && r.rows[0].id;
  }
  if (!targetBuildId) throw new Error('未找到可执行的构建任务');
  const row = await getBuild(targetBuildId);
  if (!row) throw new Error('构建不存在');

  const session = (await pool.query('SELECT * FROM sessions WHERE id=$1', [row.session_id])).rows[0];
  if (!session) throw new Error('会话不存在');

  const dir = sessionFolder(session);
  const earsFiles = (await fs.readdir(dir).catch(() => [])).filter((f) => /-ears\.md$/i.test(f)).sort().reverse();
  if (earsFiles.length === 0) throw new Error('会话目录缺少 EARS 文档');

  const buildDir = path.join(dir, 'build');
  await fs.mkdir(buildDir, { recursive: true });
  const mode = await initRepo(buildDir, await detectGit());

  await setStatus(targetBuildId, 'coding');
  await logBuildEvent(targetBuildId, 'coder', 'status', 'coding');
  await logBuildEvent(targetBuildId, 'system', 'log', `使用 EARS 文档: ${earsFiles[0]}`);

  const earsDigest = await distillSessionDigest(dir, earsFiles[0]);

  const manifest = await planApp(targetBuildId, earsDigest);
  await logBuildEvent(targetBuildId, 'coder', 'log', `已规划文件结构: ${manifest.files.map((f) => f.path).join(', ')}`);

  const generatedSignatures = [];
  for (const tf of manifest.files) {
    const content = await generateFile(targetBuildId, earsDigest, manifest, tf, generatedSignatures);
    await writeFileSafe(buildDir, tf.path, content);
    generatedSignatures.push(`${tf.path} => exports: ${tf.exports || '<待声明>'}`);
    await logBuildEvent(targetBuildId, 'coder', 'file', `已生成 ${tf.path}`);
  }
  const filesList = manifest.files.map((f) => f.path);
  await commitState(buildDir, mode, 'v0: initial generation');

  const outcome = await repairLoop(targetBuildId, buildDir, earsDigest, mode);
  if (outcome.passed) {
    await writeManifest(buildDir, targetBuildId, manifest.entry, manifest.files);
    await setStatus(targetBuildId, 'passed');
    await logBuildEvent(targetBuildId, 'system', 'status', 'passed');
    await logBuildEvent(targetBuildId, 'system', 'log', `构建通过（迭代 ${outcome.iterations} 轮）`);
  }
}

export function applyModification(buildId, instruction, userId) {
  runModification(buildId, instruction, userId).catch((err) => {
    console.error('[builder] applyModification error:', err);
    setStatus(buildId, 'failed').catch(() => {});
    setErrorSummary(buildId, err.message).catch(() => {});
    logBuildEvent(buildId, 'system', 'error', `增量修改异常终止: ${err.message}`).catch(() => {});
  });
}

async function runModification(buildId, instruction, userId) {
  const row = await getBuild(buildId);
  if (!row) throw new Error('构建不存在');
  const session = (await pool.query('SELECT * FROM sessions WHERE id=$1', [row.session_id])).rows[0];
  if (!session || session.user_id !== userId) throw new Error('无权操作');

  const dir = sessionFolder(session);
  const earsFiles = (await fs.readdir(dir).catch(() => [])).filter((f) => /-ears\.md$/i.test(f)).sort().reverse();
  if (earsFiles.length === 0) throw new Error('会话目录缺少 EARS 文档');
  const earsDigest = await distillSessionDigest(dir, earsFiles[0]);
  const buildDir = path.join(dir, 'build');
  const mode = await detectGit();

  await setStatus(buildId, 'modifying');
  await logBuildEvent(buildId, 'coder', 'status', 'modifying');

  const fileMetas = await collectFileMetas(buildDir);
  await logBuildEvent(buildId, 'system', 'log', `读取 ${fileMetas.length} 个文件`);

  const diff = await incrementalModify(buildId, instruction, earsDigest, fileMetas);
  await logBuildEvent(buildId, 'coder', 'patch', diff.slice(0, 3000));

  let applied = await applyRepairDiff(buildId, buildDir, earsDigest, '', diff, mode);
  if (!applied) {
    await logBuildEvent(buildId, 'coder', 'log', '补丁应用失败，降级为全文覆写（携带修改指令）');
    const targets = diffTargetPaths(diff);
    for (const rel of targets.length ? targets : ['index.html']) {
      applied = (await applyFullRewrite(buildId, buildDir, earsDigest, `增量修改失败: ${firstLine(diff)}`, rel, instruction)) || applied;
    }
  }
  if (!applied) throw new Error('增量修改补丁无法应用');

  await commitState(buildDir, mode, `modify: ${String(instruction).slice(0, MODIFY_MESSAGE_CAP)}`);

  const outcome = await repairLoop(buildId, buildDir, earsDigest, mode);
  if (outcome.passed) {
    await writeManifest(buildDir, buildId, 'index.html', await listProjectFiles(buildDir));
    await setStatus(buildId, 'passed');
    await logBuildEvent(buildId, 'system', 'status', 'passed');
    await logBuildEvent(buildId, 'system', 'log', `增量修改通过（迭代 ${outcome.iterations} 轮）`);
  }
}

export function revalidate(buildId, userId) {
  runRevalidate(buildId, userId).catch((err) => {
    console.error('[builder] revalidate error:', err);
    setStatus(buildId, 'failed').catch(() => {});
    setErrorSummary(buildId, err.message).catch(() => {});
    logBuildEvent(buildId, 'system', 'error', `重新验证异常终止: ${err.message}`).catch(() => {});
  });
}

async function runRevalidate(buildId, userId) {
  const row = await getBuild(buildId);
  if (!row) throw new Error('构建不存在');
  const session = (await pool.query('SELECT * FROM sessions WHERE id=$1', [row.session_id])).rows[0];
  if (!session || session.user_id !== userId) throw new Error('无权操作');

  const dir = sessionFolder(session);
  const earsFiles = (await fs.readdir(dir).catch(() => [])).filter((f) => /-ears\.md$/i.test(f)).sort().reverse();
  if (earsFiles.length === 0) throw new Error('会话目录缺少 EARS 文档');
  const earsDigest = await distillSessionDigest(dir, earsFiles[0]);
  const buildDir = path.join(dir, 'build');
  const mode = await detectGit();

  const outcome = await repairLoop(buildId, buildDir, earsDigest, mode);
  if (outcome.passed) {
    await writeManifest(buildDir, buildId, 'index.html', await listProjectFiles(buildDir));
    await setStatus(buildId, 'passed');
    await logBuildEvent(buildId, 'system', 'status', 'passed');
    await logBuildEvent(buildId, 'system', 'log', `重新验证通过（迭代 ${outcome.iterations} 轮）`);
  }
}

// ---------- 版本回滚 ----------

export function restoreBuild(buildId, hash, userId) {
  runRestore(buildId, hash, userId).catch((err) => {
    console.error('[builder] restore error:', err);
    setStatus(buildId, 'failed').catch(() => {});
    setErrorSummary(buildId, err.message).catch(() => {});
    logBuildEvent(buildId, 'system', 'error', `版本回滚异常终止: ${err.message}`).catch(() => {});
  });
}

async function runRestore(buildId, hash, userId) {
  const row = await getBuild(buildId);
  if (!row) throw new Error('构建不存在');
  const session = (await pool.query('SELECT * FROM sessions WHERE id=$1', [row.session_id])).rows[0];
  if (!session || session.user_id !== userId) throw new Error('无权操作');

  const buildDir = path.join(sessionFolder(session), 'build');
  const mode = await detectGit();

  if (mode === 'git') {
    await git(buildDir, ['restore', `--source=${hash}`, '--staged', '--worktree', '--', '.']);
    await git(buildDir, ['clean', '-fd']);
  } else {
    // 快照模式：把目标快照暂存到临时目录，再整体替换（同时保留历史快照）。
    const n = Number(hash);
    const src = path.join(buildDir, '.versions', String(n));
    const tmp = path.join(buildDir, `.restore-${Date.now()}`);
    await fs.mkdir(tmp, { recursive: true });
    const entries = await fs.readdir(src).catch(() => []);
    for (const name of entries) {
      if (name === '.versions') continue;
      await fs.cp(path.join(src, name), path.join(tmp, name), { recursive: true });
    }
    const oldVersions = path.join(buildDir, '.versions');
    const movedVersions = path.join(buildDir, `.versions-move-${Date.now()}`);
    await fs.rename(oldVersions, movedVersions).catch(() => {});
    await fs.rm(buildDir, { recursive: true, force: true });
    await fs.mkdir(buildDir, { recursive: true });
    await fs.rename(movedVersions, oldVersions).catch(() => {});
    const tmpEntries = await fs.readdir(tmp);
    for (const name of tmpEntries) {
      await fs.cp(path.join(tmp, name), path.join(buildDir, name), { recursive: true });
    }
    await fs.rm(tmp, { recursive: true, force: true });
  }
  await logBuildEvent(buildId, 'system', 'log', `已恢复到版本 ${hash}，开始重新验证`);

  const dir = sessionFolder(session);
  const earsFiles = (await fs.readdir(dir).catch(() => [])).filter((f) => /-ears\.md$/i.test(f)).sort().reverse();
  const earsDigest = earsFiles.length ? await distillSessionDigest(dir, earsFiles[0]) : '';

  const outcome = await repairLoop(buildId, buildDir, earsDigest, mode);
  if (outcome.passed) {
    await commitState(buildDir, mode, `restore to ${hash}`);
    await writeManifest(buildDir, buildId, 'index.html', await listProjectFiles(buildDir));
    await setStatus(buildId, 'passed');
    await logBuildEvent(buildId, 'system', 'status', 'passed');
    await logBuildEvent(buildId, 'system', 'log', `恢复并验证通过（迭代 ${outcome.iterations} 轮）`);
  }
}

export { isBuildDirAllowed, CONTAINER_IMAGE };