import 'dotenv/config';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

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

async function chatCompletion(messages, opts = {}) {
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
  return data.choices[0].message.content;
}

const EXPLORE_SYSTEM = `你是一名资深产品/需求分析师，正在遵循 OpenSpec 的"探索(explore)与提案(propose)"方法论与用户共同澄清一个待建设的产品或功能需求。
规则：
1. 一次最多问 1-2 个聚焦的问题，保持简短、口语化。
2. 逐轮追问，逐步澄清：建设目标、目标用户、核心功能/场景、技术约束、验收标准、非目标(Non-goals)。
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