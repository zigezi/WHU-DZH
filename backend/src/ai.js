import 'dotenv/config';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { pool } from './db.js';

const execFileP = promisify(execFile);

const BASE_URL = process.env.MOONSHOT_BASE_URL || 'https://api.moonshot.cn/v1';
const API_KEY = process.env.MOONSHOT_API_KEY || '';
const MODEL = process.env.MOONSHOT_MODEL || 'moonshot-v1-8k';
const EARS_MODEL = process.env.MOONSHOT_EARS_MODEL || 'moonshot-v1-32k';

if (!API_KEY) {
  console.warn('[ai] MOONSHOT_API_KEY 未设置，AI 反问功能将不可用');
}

function moonshotPayload(messages, maxTokens, model) {
  return { model, messages, temperature: 0.3, max_tokens: maxTokens };
}

async function callMoonshot(messages, opts = {}) {
  const { maxTokens = 2000, model = MODEL } = opts;
  if (!API_KEY) throw new Error('MOONSHOT_API_KEY 未配置');
  // 使用系统 curl 调用，避免 Node 内置 fetch(undici) 因 TLS 指纹被 Moonshot WAF 拦截。
  const { stdout, stderr } = await execFileP(
    'curl',
    [
      '-sS',
      '--max-time', '120',
      '-X', 'POST',
      `${BASE_URL}/chat/completions`,
      '-H', 'Content-Type: application/json',
      '-H', `Authorization: Bearer ${API_KEY}`,
      '--data-binary', JSON.stringify(moonshotPayload(messages, maxTokens, model)),
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
只输出最终规格文档本身，不要输出任何解释、前言、后记或"转换完成"之类的文字。`;

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

// ================= 构建子系统（v1） =================

const BUILD_MODEL = process.env.MOONSHOT_BUILD_MODEL || EARS_MODEL;

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

async function logUsage(buildId, fn, usage) {
  if (!buildId) return;
  const amount = usage ? `（prompt=${usage.prompt_tokens} tokens, completion=${usage.completion_tokens} tokens）` : '';
  await logBuildEvent(buildId, 'llm', 'log', `${fn} 调用完成${amount}`);
}

// 带 1 次重试的结构化文本生成。attempt 返回 { ok, value } 或 { ok:false, raw }。
async function robustGenerate(buildId, fnName, messages, opts, attempt) {
  const call = async () => {
    const { content, usage } = await callMoonshot(messages, opts);
    await logUsage(buildId, fnName, usage);
    try {
      const value = attempt(content);
      return { ok: true, value };
    } catch (e) {
      return { ok: false, error: e.message, raw: content };
    }
  };
  const first = await call();
  if (first.ok) return first.value;
  messages.push({ role: 'assistant', content: first.raw });
  messages.push({ role: 'user', content: `上面的输出无法解析（${first.error}）。请严格按格式重新输出，不要包含解释文字。` });
  const second = await call();
  if (second.ok) return second.value;
  throw new Error(`Moonshot 输出反复无法解析。原始输出前 400 字：\n${(second.raw || '').slice(0, 400)}`);
}

const GENERATE_APP_SYSTEM = `你是一名资深前端工程师，根据输入的 EARS 需求规格，生成一个"纯前端可运行应用"（仅 HTML/CSS/JS，无后端）作为演示静态网页。
必须严格遵守：
1. 严格并逐条按 EARS 规格实现全部功能需求；术语表中的常量/坐标/时序/默认值（含 [TBD-xx]）必须原样采用，禁止自行更改或省略。
2. 文件数量尽量少（建议 ≤6 个），优先把所有脚本内联进 index.html；禁止留任何"……(其余省略)"之类的截断注释，输出必须能在静态环境完整运行。
3. 只输出一个 JSON 对象（禁止任何解释、前言、markdown 标记或代码块外文字），结构严格为：
{"files":[{"path":"index.html","content":"..."}],"entry":"index.html","runtime":"static-web"}
4. runtime 只能等于 "static-web"，其他值一律视为非法。
5. 不使用任何外部 CDN/网络资源（运行环境断网）；禁止使用 ES Module 的 import/export，禁止 <script type="module">，全部用普通 <script> 标签（CommonJS 兼容语法）。
6. 对 localStorage/sessionStorage/cookie 的任何访问必须用 try/catch 包裹，失败时降级为纯内存实现（应用会运行在禁用了存储能力的沙箱 iframe 中）。

现在，以下面这份 EARS 需求规格实现前端应用，并只输出上述 JSON。`;

function parseGenerateApp(raw) {
  const data = JSON.parse(raw);
  if (!Array.isArray(data.files) || data.files.length === 0) throw new Error('files 缺失或为空');
  if (!data.entry) throw new Error('entry 缺失');
  if (data.runtime !== 'static-web') throw new Error(`不支持的 runtime: ${data.runtime}`);
  for (const f of data.files) {
    if (typeof f.path !== 'string' || typeof f.content !== 'string') throw new Error('file 项缺少 path 或 content');
    if (f.path === '_validate.cjs' || f.path === 'manifest.json') throw new Error(`保留路径，禁止生成: ${f.path}`);
  }
  return { files: data.files, entry: data.entry, runtime: data.runtime };
}

export async function generateApp(buildId, earsContent) {
  const messages = [
    { role: 'system', content: GENERATE_APP_SYSTEM },
    { role: 'user', content: earsContent },
  ];
  return robustGenerate(buildId, 'generateApp', messages, { maxTokens: 8000, model: BUILD_MODEL }, parseGenerateApp);
}

function looksLikeDiff(text) {
  return /^(diff --git|@@ )/m.test(text) || /(^|\n)\+\+\+ /.test(text);
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

const DEBUG_FIX_SYSTEM = `你是一名资深调试工程师。你将收到：某应用运行的报错信息（stderr 尾部）、出错/涉及文件，以及对应的 EARS 需求。
你的任务：输出一个"最小 unified diff"补丁修复该报错，使应用通过语法检查与静态服务可达性检查。
必须严格遵守：
1. 只做最小改动；禁止整体重写整个文件。
2. 禁止为消除报错而删除、弱化或偏离 EARS 需求所要求的功能；当报错与需求冲突时，以 EARS 需求原文为准。
3. 只输出标准 git unified diff（以 diff --git / --- / +++ / @@ 开头的 hunk），禁止输出 JSON、解释文字或代码块围栏。
4. 语法风格需与文件现状完全一致（本项目统一 CommonJS，无 import/export）。`;

function buildDebugUser(earsPart, stderrTail, involvedFiles) {
  return [
    '# 验证失败（stderr 尾部）',
    '```',
    stderrTail || '(无)',
    '```',
    '# 出错/涉及文件',
    '```',
    involvedFiles || '（未知，需自行根据报错判断）',
    '```',
    '# 对应 EARS 需求（节选）',
    '```',
    (earsPart || '').slice(0, 12000),
    '```',
    '',
    '请输出最小 unified diff 补丁（只输出 patch 文本）：',
  ].join('\n');
}

export async function debugFix(buildId, earsPart, stderrTail, involvedFiles) {
  const messages = [
    { role: 'system', content: DEBUG_FIX_SYSTEM },
    { role: 'user', content: buildDebugUser(earsPart, stderrTail, involvedFiles) },
  ];
  return robustGenerateDiff(buildId, 'debugFix', messages, { maxTokens: 4000, model: BUILD_MODEL });
}

const REWRITE_FILE_SYSTEM = `你是一名资深前端工程师。你会收到某文件当前内容及其报错信息、对应的 EARS 需求。
任务：输出该文件"修复后的完整内容文本"。
1. 只输出文件正文本身，禁止任何解释、前言、后记或代码块围栏（不要用 \`\`\` 包裹）。
2. 保持文件职责与项目结构不变，做最小必要改动以修复报错，并保留 EARS 要求的功能。`;

export async function rewriteFile(buildId, filePath, currentContent, earsPart, stderrTail) {
  const messages = [
    { role: 'system', content: REWRITE_FILE_SYSTEM },
    {
      role: 'user',
      content: [
        `文件路径: ${filePath}`,
        '',
        '# 当前内容',
        '```',
        currentContent || '(空文件)',
        '```',
        '',
        '# 报错（stderr 尾部）',
        '```',
        stderrTail || '(无)',
        '```',
        '',
        '# 对应 EARS 需求（节选）',
        '```',
        (earsPart || '').slice(0, 6000),
        '```',
        '',
        '请输出修复后的完整文件正文：',
      ].join('\n'),
    },
  ];
  const { content, usage } = await callMoonshot(messages, { maxTokens: 6000, model: BUILD_MODEL });
  await logUsage(buildId, 'rewriteFile', usage);
  return stripFences(content);
}

const INCREMENTAL_MODIFY_SYSTEM = `你是一名资深前端工程师。你会收到用户的一条增量修改指令、当前项目文件信息，以及对应 EARS 需求。
请按指令对相关文件做最小改动，输出"最小 unified diff"补丁。
必须严格遵守：
1. 只做最少的必要改动；禁止整体重写整个文件。
2. 修改指令与 EARS 需求冲突时，以 EARS 需求为准，并在补丁相关 hunk 上方加入注释行"// 按 EARS 执行"。
3. 保持 CommonJS 语法与 HTML 结构不变，禁止引入外部网络资源。
4. 只输出标准 unified diff（diff --git / a/ / b+++ 开行），禁止 JSON、代码块围栏或解释文字。`;

export async function incrementalModify(buildId, instruction, earsContent, currentFilesText) {
  const messages = [
    { role: 'system', content: INCREMENTAL_MODIFY_SYSTEM },
    {
      role: 'user',
      content: [
        `修改指令: ${instruction}`,
        '',
        '# 对应 EARS 需求（节选）',
        '```',
        (earsContent || '').slice(0, 12000),
        '```',
        '',
        '# 当前项目文件（节选，供定位改动位置）',
        '```',
        (currentFilesText || '').slice(0, 20000),
        '```',
        '',
        '请输出最小 unified diff 补丁（只输出该文本）：',
      ].join('\n'),
    },
  ];
  return robustGenerateDiff(buildId, 'incrementalModify', messages, { maxTokens: 4000, model: BUILD_MODEL });
}

export { logBuildEvent, stripJsonFences, parseGenerateApp };