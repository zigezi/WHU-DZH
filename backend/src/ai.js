import 'dotenv/config';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { pool } from './db.js';

const execFileP = promisify(execFile);

const BASE_URL = process.env.MOONSHOT_BASE_URL || 'https://api.moonshot.cn/v1';
const API_KEY = process.env.MOONSHOT_API_KEY || '';
const MODEL = process.env.MOONSHOT_MODEL || 'kimi-k2.6';
const EARS_MODEL = process.env.MOONSHOT_EARS_MODEL || 'kimi-k3';

if (!API_KEY) {
  console.warn('[ai] MOONSHOT_API_KEY 未设置，AI 反问功能将不可用');
}

function moonshotPayload(messages, maxTokens, model, temperature = 1) {
  // kimi-k3 / kimi-k2.6 仅允许 temperature=1；旧版 moonshot-v1 亦接受 1，故统一为 1。
  return { model, messages, temperature, max_tokens: maxTokens };
}

async function callMoonshot(messages, opts = {}) {
  const { maxTokens = 2000, model = MODEL } = opts;
  if (!API_KEY) throw new Error('MOONSHOT_API_KEY 未配置');
  // 使用系统 curl 调用，避免 Node 内置 fetch(undici) 因 TLS 指纹被 Moonshot WAF 拦截。
  const { stdout, stderr } = await execFileP(
    'curl',
    [
      '-sS',
      '--max-time', process.env.MOONSHOT_LLM_TIMEOUT || '600',
      '-X', 'POST',
      `${BASE_URL}/chat/completions`,
      '-H', 'Content-Type: application/json',
      '-H', `Authorization: Bearer ${API_KEY}`,
      '--data-binary', JSON.stringify(moonshotPayload(messages, maxTokens, model, opts.temperature)),
    ],
    { maxBuffer: 32 * 1024 * 1024 },
  );
  if (!stdout) {
    throw new Error(`Moonshot API 无响应: ${(stderr || '').slice(0, 300)}`);
  }
  const data = JSON.parse(stdout);
  if (!data.choices || !data.choices[0]) {
    throw new Error(`Moonshot API 异常响应: ${stdout.slice(0, 300)}`);
  }
  return {
    content: data.choices[0].message.content,
    usage: (data.usage && { prompt_tokens: data.usage.prompt_tokens, completion_tokens: data.usage.completion_tokens }) || null,
  };
}

async function chatCompletion(messages, opts = {}) {
  return (await callMoonshot(messages, opts)).content;
}

const EXPLORE_SYSTEM = `你是一名资深产品/需求分析师，正在遵循 OpenSpec 的"探索(explore)与提案(propose)"方法论与用户共同澄清一个待建设的产品或功能需求。
规则：
1. 一次最多问 1-2 个聚焦的问题，保持简短、口语化。
2. 逐轮追问，逐步澄清：建设目标、目标用户、核心功能/场景、技术约束、验收标准、非目标
3. 不要写代码，不要输出完整文档；只用自然语言澄清需求。
4. 当信息足够时，提示用户："信息已足够，可以点击「完成/归档」生成需求分析文档"。
5. 全程使用简体中文。`;

const DRAFT_SYSTEM = `你是一名资深需求分析师，依据下面用户与你的澄清对话，产出一份规范、结构化的需求分析文档（Markdown）。
文档必须包含以下章节，使用 ## 二级标题：
- # 需求分析
- ## 一、项目概述
- ## 二、目标与用户（含目标用户画像）
- ## 三、功能需求（每条用 - 列出，包含需求描述与验收标准）
- ## 四、非功能需求
- ## 五、技术约束与环境
- ## 六、非目标（Non-goals）
- ## 七、后续任务建议
要求：语言精炼、可执行、可直接作为开发依据。如果对话中信息不足，对明显缺失项标注"[待确认]"，不要编造。
最后重要：直接输出 Markdown 正文，不要用代码块(如 \`\`\`markdown)包裹全文，不要在文档开头或结尾添加任何说明性、总结性或客套性文字（如"以下是根据"、"希望这份"等）。使用简体中文。`;

export function buildHistory(messages) {
  return messages.map((m) => ({ role: m.role === 'assistant' ? 'assistant' : 'user', content: m.content }));
}

export async function askExplorationQuestion(history) {
  const messages = [{ role: 'system', content: EXPLORE_SYSTEM }, ...history];
  return chatCompletion(messages);
}

export async function draftRequirementDoc(history) {
  const messages = [
    { role: 'system', content: DRAFT_SYSTEM },
    ...history,
    { role: 'user', content: '请根据以上完整对话，生成需求分析文档（Markdown 格式）。' },
  ];
  return chatCompletion(messages, { maxTokens: 4000 });
}

const EARS_SYSTEM = `你是需求工程（RE/EARS）规格转换专家。你会收到：①一份《EARS 转换任务提示词》，其中包含完整的转换规则、自检清单和参考范例；②一份待转换的需求分析文档。
请严格、逐条执行任务提示词中的全部规则（句式、消歧专项、术语表、编号规范、TBD 铁律、章节结构、自检清单），把需求文档转换为 EARS 需求规格说明书（Markdown）。
只输出最终规格文档本身，不要输出任何解释、前言、后记或"转换完成"之类的辅助文字。`;

function stripFences(text) {
  const trimmed = text.trim();
  const m = trimmed.match(/^```[a-z]*\n([\s\S]*?)\n```$/);
  return m ? m[1].trim() : trimmed;
}

export async function convertToEars(promptContent, requirementContent) {
  const messages = [
    { role: 'system', content: EARS_SYSTEM },
    { role: 'user', content: `# EARS 转换任务提示词\n\n${promptContent}` },
    { role: 'user', content: `# 待转换的需求分析文档\n\n${requirementContent}\n\n请输出转换后的 EARS 需求规格说明书（Markdown）。` },
  ];
  const raw = await chatCompletion(messages, { maxTokens: 9000, model: EARS_MODEL });
  return stripFences(raw);
}

// ================= 构建子系统（v1.3） =================

// 代码生成/调试使用独立模型，由 .env 的 MODEL_CODEGEN 配置，禁止硬编码模型名。
const CODEGEN_MODEL = process.env.MODEL_CODEGEN || 'kimi-k2.6';

// kimi-k3/k2.6 属于推理模型，reasoning_content 会先占据相当长输出预算，
// 若 max_tokens 过小，正文 content 可能被挤成空串。故把代码相关调用的输出上限拉到模型允许的最大值。
const TOKEN_MAX_OUT = 32000;
const PLAN_MAX_TOKENS = 8000;
// 平衡值：常规代码生成/调试/diff 输出上限。推理模型(如 kimi-k2.6)会先在 reasoning_content
// 上消耗预算，此前 6000 常被挤空、32000 又过慢；12000 为验证过的平衡点。超大文件全文覆写
// （rewriteFile）仍保留 TOKEN_MAX_OUT 兜底。
const TOKEN_BALANCED = 12000;

async function logBuildEvent(buildId, agent, eventType, content) {
  if (!buildId) return;
  try {
    await pool.query(
      'INSERT INTO build_events (build_id, agent, event_type, content) VALUES ($1,$2,$3,$4)',
      [buildId, agent, eventType, content],
    );
  } catch {
    /* 日志写入失败可忽略 */
  }
}

function stripJsonFences(text) {
  const trimmed = (text || '').trim();
  const m = trimmed.match(/^```(?:json)?\s*\n([\s\S]*?)\n```$/);
  if (m) return m[1].trim();
  const jsonStart = trimmed.indexOf('{');
  const jsonEnd = trimmed.lastIndexOf('}');
  if (jsonStart >= 0 && jsonEnd > jsonStart) return trimmed.slice(jsonStart, jsonEnd + 1).trim();
  return trimmed;
}

async function logUsage(buildId, fn, usage, model) {
  if (!buildId) return;
  const amount = usage ? `（prompt=${usage.prompt_tokens} tokens, completion=${usage.completion_tokens} tokens）` : '';
  await logBuildEvent(buildId, 'llm', 'log', `${fn} 调用完成，模型=${model || CODEGEN_MODEL}${amount}`);
}

// 带 1 次重试的结构化文本生成。attempt 返回 { ok, value } 或 { ok:false, raw }。
async function robustGenerate(buildId, fnName, messages, opts, attempt) {
  const call = async () => {
    const { content, usage } = await callMoonshot(messages, opts);
    await logUsage(buildId, fnName, usage, opts.model);
    try {
      const value = attempt(content);
      return { ok: true, value };
    } catch (e) {
      return { ok: false, error: e.message, raw: content };
    }
  };
  const first = await call();
  if (first.ok) return first.value;
  if (first.raw && first.raw.trim()) {
    messages.push({ role: 'assistant', content: first.raw });
    messages.push({ role: 'user', content: `上面的输出无法解析（${first.error}）。请严格按格式重新输出，不要包含解释文字。` });
  } else {
    // 首轮输出为空/纯空白：不要回填空 assistant 消息（Moonshot 会报 400）。
    messages.push({ role: 'user', content: `上面的输出为空且无法解析（${first.error}）。请完整输出结果，禁止留空。` });
  }
  // 至多再试 2 次（共 3 次），抵御弱网/偶发空输出。
  for (let i = 0; i < 2; i++) {
    const next = await call();
    if (next.ok) return next.value;
    if (next.raw && next.raw.trim()) {
      messages.push({ role: 'assistant', content: next.raw });
      messages.push({ role: 'user', content: `仍未解析（${next.error}）。再输出一次，务必符合格式且非空。` });
    } else {
      messages.push({ role: 'user', content: `输出仍为空。请重新完整输出有效结果。` });
    }
    if (i === 1) throw new Error(`Moonshot 输出反复无法解析。原始输出前 400 字：\n${(next.raw || '').slice(0, 400)}`);
  }
}

function looksLikeDiff(text) {
  return /^(diff --git |\+\+\+ |--- a\/)/m.test(text) || /(^|\n)@@ -\d+/.test(text);
}

async function robustGenerateDiff(buildId, fnName, messages, opts) {
  const attempt = (content) => {
    const text = stripFences(content);
    if (!looksLikeDiff(text)) {
      const e = new Error('未包含可应用的 unified diff');
      e.raw = content;
      throw e;
    }
    return text;
  };
  return robustGenerate(buildId, fnName, messages, opts, attempt);
}

// ---------- 上下文预算（一·五） ----------

const TOKEN_BUDGET = 24000;
// token 估算 ≈ 字符数 / 1.5；所有代码生成调用输入必须 ≤ TOKEN_BUDGET。
function estTokens(text) {
  return Math.ceil((text || '').length / 1.5);
}

function cutTail(str, maxChars, label) {
  if (!str || str.length <= maxChars) return str || '';
  return str.slice(0, maxChars) + `\n...（${label}超出上下文预算已裁剪，原始长度 ${str.length} 字符）`;
}

async function domainError(buildId, fn, msg) {
  await logBuildEvent(buildId, 'system', 'error', `${fn}: ${msg}`);
  throw new Error(`${fn}: ${msg}`);
}

// ---------------- EARS 蒸馏（确定性，非 LLM） ----------------

// 从 EARS 文档抽取「代码生成摘要」：术语表全文 + 全局规则 + 全部 FR 一句话索引 + TBD 默认值表。
export function distillEars(earsContent) {
  const lines = (earsContent || '').split('\n');
  const glossary = [];
  const gr = [];
  const fr = [];
  const tbd = [];
  let inGlossary = false;
  for (const raw of lines) {
    const L = raw.trim();
    if (/^#+\s*0\D*术语表/.test(L)) { inGlossary = true; continue; }
    if (inGlossary) {
      if (/^##/.test(L)) inGlossary = false;
      else if (L.startsWith('|')) {
        if (/^\|[-:\s|]+\|?$/.test(L)) continue; // 表头分隔行
        glossary.push(L);
      }
      continue;
    }
    if (/\*\*GR(-\d+)?\b/.test(L)) gr.push(L.replace(/^[-*]\s*/, ''));
    if (/\bFR-\d+\b/.test(L) && !L.startsWith('|')) fr.push(L.replace(/^[-*]\s*/, ''));
    if (/TBD-\d+/.test(L)) tbd.push(L);
  }
  return [
    '# 术语表（全文）',
    glossary.length ? glossary.join('\n') : '（无可提取表格）',
    '',
    '# 全局规则（Ubiquitous）',
    gr.length ? gr.join('\n') : '（无 GR 行）',
    '',
    '# 功能需求索引（FR-xx）',
    fr.length ? fr.join('\n') : '（无 FR 行）',
    '',
    '# TBD 默认值',
    tbd.length ? tbd.join('\n') : '（无 TBD）',
  ].join('\n');
}

// ---------------- 公共约束（每个生/改函数都带） ----------------

const PUBLIC = `构建设置要求：
- 严格按 EARS 蒸馏摘要实现；常量/坐标/时序/默认值（含 [TBD-xx]）必须原样采用，禁止自行更改。
- 不使用任何外部 CDN/网络资源（运行环境断网）。
- 禁止 ES Module 的 import/export，禁止 <script type="module">，全部用普通 <script> 标签（CommonJS 兼容语法）。
- 对 localStorage/sessionStorage/cookie 的任何访问必须 try/catch 包裹并降级为纯内存实现（应用运行在禁用了存储能力的沙箱 iframe 中）。`;

// ---------------- planApp ----------------

const PLAN_APP_SYSTEM = `你是一名资深前端工程师，为一个纯前端应用设计<文件结构>（只做规划，不写任何代码）。
必须严格遵守：
1. 文件数量尽量少（建议 ≤6 个），优先把所有脚本内联进 index.html。
2. 只输出一个 JSON 对象（禁止解释、前言、markdown 标记或代码块外层任何内容），结构严格为：
{"files":[{"path":"index.html","purpose":"说明","exports":"对外暴露的函数/变量签名"},...],"entry":"index.html","runtime":"static-web"}
3. runtime 只能是 "static-web"，其他值一律非法。
4. purpose 与 exports 用一句话概括，供分文件生成时互相感知；不写实现。
${PUBLIC}`;

function parsePlanApp(raw) {
  const data = JSON.parse(raw);
  if (!Array.isArray(data.files) || data.files.length === 0) throw new Error('files 缺失或为空');
  if (!data.entry) throw new Error('entry 缺失');
  if (data.runtime !== 'static-web') throw new Error(`runtime 非法: ${JSON.stringify(data.runtime)}`);
  for (const f of data.files) {
    if (typeof f.path !== 'string' || typeof f.purpose !== 'string') throw new Error('file 项缺少 path 或 purpose');
    if (f.path === '_validate.cjs' || f.path === 'manifest.json') throw new Error(`保留路径不可规划: ${f.path}`);
  }
  return { files: data.files, entry: data.entry, runtime: data.runtime };
}

export async function planApp(buildId, earsDigest) {
  if (estTokens(PLAN_APP_SYSTEM + earsDigest) > TOKEN_BUDGET) {
    await domainError(buildId, 'planApp', `蒸馏摘要过长（约 ${estTokens(PLAN_APP_SYSTEM + earsDigest)} tokens）`);
  }
  const messages = [
    { role: 'system', content: PLAN_APP_SYSTEM },
    { role: 'user', content: earsDigest },
  ];
  return robustGenerate(buildId, 'planApp', messages, { maxTokens: PLAN_MAX_TOKENS, model: CODEGEN_MODEL }, parsePlanApp);
}

// ---------------- generateFile ----------------

const GENERATE_FILE_SYSTEM = `你是一名资深前端工程师。你在编写一个纯前端静态应用（HTML/CSS/JS，无后端）中的<单个文件>。
你会收到：EARS 摘要、项目清单（manifest）、目标文件定位、已生成其他文件的「路径+导出签名」。
任务：只输出目标文件的完整代码文本。
必须严格遵守：
1. 完整、可运行，禁止留任何"…其余省略/其余代码不变"之类的截断注释。
2. 只输出文件正文；不要解释、前言、Markdown 标记或代码块围栏（不要用 \`\`\` 包裹）。
3. 调用其他文件接口时，以「路径+导出签名」为准；如签名尚未生成，可预留一致命名。
4. 遵守 CommonJS 语法；禁止 import/export、禁止 <script type="module">。
5. 不使用任何外部 CDN/网络资源。
6. 对 localStorage/sessionStorage/cookie 一律 try/catch 降级为内存实现。
${PUBLIC}`;

function generateFilePrompt(earsDigest, manifest, targetFile, generatedSignatures) {
  const list = (generatedSignatures || []).filter(Boolean);
  return [
    '# EARS 代码生成摘要',
    '```',
    earsDigest,
    '```',
    '',
    '# 项目文件清单（manifest）',
    '```json',
    JSON.stringify(manifest, null, 2),
    '```',
    '',
    '# 本次要生成的文件',
    `path: ${targetFile.path}`,
    `purpose: ${targetFile.purpose || ''}`,
    `exports: ${targetFile.exports || ''}`,
    '',
    '# 已生成文件的「路径 + 导出签名」',
    list.length ? list.join('\n') : '（尚无已生成文件）',
    '',
    '请只输出该文件完整代码：',
  ].join('\n');
}

export async function generateFile(buildId, earsDigest, manifest, targetFile, generatedSignatures) {
  const user = generateFilePrompt(earsDigest, manifest, targetFile, generatedSignatures);
  if (estTokens(user) > TOKEN_BUDGET) {
    await domainError(buildId, `generateFile:${targetFile.path}`, `输入约 ${estTokens(user)} tokens 超预算`);
  }
  const messages = [
    { role: 'system', content: GENERATE_FILE_SYSTEM },
    { role: 'user', content: user },
  ];
  const { content, usage } = await callMoonshot(messages, { maxTokens: TOKEN_BALANCED, model: CODEGEN_MODEL });
  await logUsage(buildId, `generateFile:${targetFile.path}`, usage, CODEGEN_MODEL);
  return stripFences(content);
}

// ---------------- debugFix ----------------

const DEBUG_FIX_SYSTEM = `你是一名资深调试工程师。你会收到报错（stderr 尾部）、出错/涉及文件内容、其余文件的「路径+导出签名」骨架，以及对应 EARS 相关段落。
任务：输出最小 unified diff 补丁，使应用通过语法检查与静态服务可达性检查。
必须严格遵守：
1. 只做最小改动；禁止整体重写整个文件。
2. 禁止为消除报错而删除、弱化或偏离 EARS 需求要求的功能；报错与需求冲突时以 EARS 原文为准。
3. 只输出标准 git unified diff，禁止 JSON、解释文字或代码块围栏。
4. 语法风格与文件现状一致（CommonJS，无 import/export）。
${PUBLIC}`;

export async function debugFix(buildId, earsRelevantFr, stderrTail, involvedFiles, otherFileSignatures) {
  const involvedTexts = [];
  for (const f of Array.isArray(involvedFiles) ? involvedFiles : []) {
    if (f && f.path) {
      involvedTexts.push(`--- ${f.path} ---（前 ${(f.content || '').slice(0, 8000).length} 字符）\n${(f.content || '').slice(0, 8000)}`);
    } else if (typeof f === 'string') {
      involvedTexts.push(f);
    }
  }
  const user = [
    '# 验证失败（stderr 尾部）',
    '```',
    stderrTail || '(无)',
    '```',
    '# 出错/涉及文件内容',
    involvedTexts.length ? involvedTexts.join('\n') : '（未知，需根据报错判断）',
    '# 其余文件「路径 + 导出签名」',
    Array.isArray(otherFileSignatures) && otherFileSignatures.length ? otherFileSignatures.join('\n') : '（无）',
    '# 对应 EARS 相关段落',
    '```',
    (earsRelevantFr || '').slice(0, 6000),
    '```',
    '',
    '请输出最小 unified diff 补丁：',
  ].join('\n');
  if (estTokens(user) > TOKEN_BUDGET) {
    await domainError(buildId, 'debugFix', `裁剪后约 ${estTokens(user)} tokens 仍超预算`);
  }
  const messages = [
    { role: 'system', content: DEBUG_FIX_SYSTEM },
    { role: 'user', content: user },
  ];
  return robustGenerateDiff(buildId, 'debugFix', messages, { maxTokens: TOKEN_BALANCED, model: CODEGEN_MODEL });
}

// ---------------- rewriteFile（全文覆写兜底） ----------------

const REWRITE_FILE_SYSTEM = `你是一名资深前端工程师。你会收到某文件当前内容、报错信息、对应 EARS 相关段落，以及（可能有）一条要实现/修复的修改指令。
任务：输出该文件修改后的完整内容文本。
1. 只输出文件正文（禁止解释、前言、后记或代码块围栏）。
2. 保持文件职责与项目结构，做最小改动修复报错/实现修改指令，并保留 EARS 要求功能。
3. **若提供了修改指令，指令指定的数值、文案、时序、逻辑必须真正落地**（如"苹果数量改为 15"须把实际创建数量改为 15），禁止只在注释里描述而不改代码。
${PUBLIC}`;

export async function rewriteFile(buildId, filePath, currentContent, earsRelevantFr, stderrTail, instruction) {
  const user = [
    `文件路径: ${filePath}`,
    '# 当前内容',
    `\`\`\`\n${(currentContent || '').slice(0, 12000)}\`\`\``,
    instruction
      ? `# 需要实现的修改指令\n\`\`\`\n${instruction}\`\`\``
      : '# 报错（stderr 尾部）',
    instruction ? '' : `\`\`\`\n${stderrTail || '(无)'}\`\`\``,
    '# 对应 EARS 相关段落',
    `\`\`\`\n${(earsRelevantFr || '').slice(0, 5000)}\`\`\``,
    '',
    '请输出修改/修复后的完整文件正文：',
  ].join('\n');
  if (estTokens(user) > TOKEN_BUDGET) await domainError(buildId, 'rewriteFile', `输入约 ${estTokens(user)} tokens 超预算`);
  const messages = [
    { role: 'system', content: REWRITE_FILE_SYSTEM },
    { role: 'user', content: user },
  ];
  const { content, usage } = await callMoonshot(messages, { maxTokens: TOKEN_MAX_OUT, model: CODEGEN_MODEL });
  await logUsage(buildId, `rewriteFile:${filePath}`, usage, CODEGEN_MODEL);
  return stripFences(content);
}

// ---------------- incrementalModify（两段式） ----------------

const SELECT_FILES_SYSTEM = `你是工程师。为了把一条修改指令应用到项目，指出需要读取哪几个文件的<路径>才能完成改动。
只输出 JSON 数组（字符串数组），例如 ["index.html","game.js"]；不要输出解释。不确定时可多列候选，但不要列无关文件。`;

const INCREMENTAL_SYSTEM = `你是一名资深前端工程师。你会收到修改指令、EARS 相关段落，以及选中的若干文件全文。
请做最小改动，输出"最小 unified diff"补丁，使修改指令真正生效。
必须严格遵守：
1. 只做最少必要改动；禁止整体重写整个文件。
2. **修改必须真正落地**：指令中指定的数值、文案、时序、逻辑等必须直接改写进对应代码（例如"苹果数量改为 15"必须把创建苹果的循环上限改为 15），禁止只加注释、只描述而不改代码。
3. 修改指令与 EARS 需求冲突时以 EARS 需求为准，并在对应 hunk 前加注释"// 按 EARS 执行"。
4. 保持 CommonJS、HTML 结构，禁止引入外部网络资源。
5. 只输出标准 unified diff；diff 中的新增/改动行必须与目标文件现有缩进、风格一致，确保能被 git apply 干净应用。`;

export async function incrementalModify(buildId, instruction, earsDigest, fileMetas) {
  // 第一段：选出需要读的文件
  const metaList = (fileMetas || []).map((m) => `${m.path}（purpose: ${m.purpose || ''}）`).join('\n');
  const stage1Messages = [
    { role: 'system', content: SELECT_FILES_SYSTEM },
    { role: 'user', content: `修改指令：${instruction}\n\n项目文件清单：\n${metaList}\n\n请只输出需要读取的文件路径 JSON 数组。` },
  ];
  const attemptNames = (raw) => {
    const arr = JSON.parse(stripJsonFences(raw));
    if (!Array.isArray(arr)) throw new Error('不是数组');
    return arr.map((s) => (s && s.path) || String(s));
  };
  let selected = null;
  try {
    selected = await robustGenerate(buildId, 'incrementalModify.selectFiles', stage1Messages, { maxTokens: 800, model: CODEGEN_MODEL }, attemptNames);
  } catch {
    selected = null;
  }
  await logBuildEvent(buildId, 'coder', 'log', `增量修改选中文件: ${selected ? selected.join(', ') : '（模型选择失败，回落到全部文件）'}`);

  const targets = selected && selected.length ? selected : (fileMetas || []).map((m) => m.path);
  const fileBodies = (fileMetas || [])
    .filter((m) => targets.indexOf(m.path) >= 0)
    .map((m) => `===== ${m.path} =====\n${(m.content || '').slice(0, 8000)}`)
    .join('\n\n');

  const user2 = [
    `修改指令：${instruction}`,
    '',
    '# EARS 摘要（相关段落）',
    '```',
    (earsDigest || '').slice(0, 8000),
    '```',
    '',
    '# 需修改文件全文',
    fileBodies || '（无，请依据项目创建）',
    '',
    '请输出最小 unified diff 补丁：',
  ].join('\n');
  if (estTokens(user2) > TOKEN_BUDGET) {
    await domainError(buildId, 'incrementalModify', `选中文件过大（约 ${estTokens(user2)} tokens）`);
  }
  const messages2 = [
    { role: 'system', content: INCREMENTAL_SYSTEM },
    { role: 'user', content: user2 },
  ];
  return await robustGenerateDiff(buildId, 'incrementalModify.diff', messages2, { maxTokens: TOKEN_BALANCED, model: CODEGEN_MODEL });
}

// ---------- 导出 ----------

export { logBuildEvent, stripJsonFences };