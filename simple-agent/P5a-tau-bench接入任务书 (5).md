# P5a · τ-bench 评测集接入任务书（opencode 实施版）v1.4

> **实施者**：opencode 调用 DeepSeek-V4 ｜ **目标仓库**：https://github.com/zigezi/WHU-DZH 分支 `simple-agent`，只改 `simple-agent/` 子目录
> **前置状态**：v2.3 任务书全部 Phase 已验收（P-1~P4 绿，证据在 `.agent/evidence/`）
> **元规则继承**：MR-1~MR-6 全文有效（交付=代码+证据、Phase 是闸门、禁止伪造、卡住 BLOCKED 等人裁、报告溯源）。本任务书任何验收命令失败同样适用 MR-5。
> **目标**：把 τ-bench（airline + retail）变成 simple-agent 的燃料——任务进 requirements/ 体系、多轮对话进 worker、评判进 V 层、结果进 epoch 报告，烧出第一批 precedents / routes / 学习曲线。

---

## 作者裁决 v1.1（2026-09-11，针对服务端源码实测对账）

**四条全部接受。架构级变更一条：桥接从"进程内"改为"sidecar 进程"。**

1. **依赖隔离（最大风险）→ 强制 sidecar 架构**。τ-bench 真实依赖（litellm/anthropic/mistralai/google-generativeai…）**禁止进入 mini-agent 环境**。裁决：τ 环境跑在独立 venv 的 **sidecar 进程**里（`127.0.0.1:8010`，复用 pidmap 登记模式），worker 的 `tau__*` 工具桥改成对该进程的 JSON-RPC over HTTP 调用。~~sidecar 内以 `pip install -e . --no-deps` + 最小依赖集安装，且自写 user simulator 用 openai 兼容 client，不引入 litellm~~（**本句已被 v1.2 作废**：envs 导入链硬依赖 litellm，sidecar venv 内改为完整安装并允许 litellm；自写 simulator 的裁决保留，改由 driver 侧 openai client 实现）。5a.0 升级为探针闸门。
2. **任务口径 → 只接 test 的 165 条**（airline ~50 + retail ~115）。retail train ~500 条**登记但本期不入库**，等 165 条上烧出学习信号后再放量（那时单日成本上限和预算模型也有了实测依据）。§5a.4 相应修正。
3. **成本口径 → 采纳"双模型 ≈ 2 倍 + evaluator replay 可能再触发 user LLM"**。探针必须实测：本版 `calculate_reward()` 的 GT actions replay 是否会经 `self.step()` 触发 user simulator 额外调用；若会，scoring 实现必须给 replay 注入**桩 user**（返回固定 `###STOP###`），把 replay 的 LLM 成本压到 0。成本护栏其余条款不变且严格执行。
4. **DeepSeek 通过率预期 → 采纳并写进验收**：参照官方 gpt-4o airline Pass^1≈0.42，DeepSeek 基线必然更低、曲线噪声大。**本期目标是学习信号（epoch 间相对改善 + 同族 token 下降），不是绝对 reward**；5a.5 验收删除对高 reward 的任何隐含期待，只要求基线数据真实完整。
5. **补充**：τ-bench 不在 PyPI、仓库已被官方标记过期——我们把它当**任务语料+评判器**用，不追上游：vendor 时在 evidence 里记录 git commit hash 锁版本。τ²/τ³ 仍在"明确不做"清单。

---

## 作者裁决 v1.2（2026-09-11，针对第二轮对账：litellm 硬依赖）

**对账实测：`base.py` 顶部 `from tau_bench.envs.user import load_user`，`user.py:5` `from litellm import completion`——导入 envs 必然拉起 litellm，v1.1"不引用 litellm 模块"的约束在物理上不成立。接受方案 (a)，理由与边界如下：**

1. **litellm 解禁，但仅限 sidecar venv 内**。原禁令的目的是保护 mini-agent 运行环境，不是与 litellm 有仇——sidecar 独立 venv 已经实现了这个目的，继续在隔离环境里自残式绕行（sys.modules 注桩/补丁 vendor 源码）只会引入新的脆弱性。**边界**：litellm 永远不得出现在 mini-agent 环境的 pip list 里（5a.0 的"前后 diff 为空"验收不变）；worker/bridge 代码禁止 import litellm；sidecar venv 的完整依赖清单入 evidence。
2. **user simulator 归属写死（对账第 2 条）**：`env.step(RESPOND)` 内部会调 `self.user.step()`，所以——**sidecar 内零 LLM**。env 构造时注入 `QueueUser`：它不调任何 LLM，只阻塞等待队列消息。流程：worker 产出回应 → bridge.step(RESPOND) → env 调 QueueUser.step() 阻塞 → sidecar 返回 WAITING；worker 侧 DialogueDriver 用自写 simulator（openai client）生成下一用户回合 → RPC `provide_user_msg` 推进队列 → env.step 完成返回观测。**`###STOP###` 由 driver 判定**，不由 sidecar。
3. **replay 注桩（对账第 4 条）与上一条同源解决**：`calculate_reward()` 是 env 实例方法，scoring 触发 replay 前把 env 的 user 替换为 `StubUser`（固定返回 `###STOP###`），replay LLM 成本 = 0。
4. **session 管理补入（对账第 3 条）**：sidecar RPC 全部带 `session_id`（reset 返回、step/reward/list_tools 携带），每个 episode 独立 env 实例，db 状态按 session 隔离。当前 eval_loop 是串行的，但这是防止状态串味污染证据的廉价保险，现在做。

---

## 作者裁决 v1.3（2026-09-11，针对第三轮对账：三个源码级地雷）

**三条全部接受，写入 5a.0 探针"已知地雷"清单与对应 Phase 正文：**

1. **QueueUser 流程自相矛盾（死锁）→ 改非阻塞哨兵**。v1.2 描述的"QueueUser 阻塞等队列、同时 sidecar 返回 WAITING"不可能成立（同一 RPC 不能既阻塞又返回）。定稿实现：`QueueUser.step()` **抛 `WaitingForUser` 异常** → sidecar 捕获后 step RPC 返回 `{status:"WAITING_FOR_USER"}`（此刻 RESPOND 已记入 env.actions）→ driver 生成用户消息 U → `provide_user_msg(session, U)` 推进；**U 本就是 worker 侧生成的，worker 已有 U，原 step 无需再"完成后返回观测"**。
2. **RESPOND 语义（5a.1 的真正核心，v1.2 漏写）**：τ-bench 里 RESPOND 不是工具，是"无 tool_call 的纯文本回复"（`message_to_action`：有 tool_calls→工具动作，否则→`Action(name="respond")`）。而 worker 现有逻辑是"LLM 没返回 tool_calls → 判任务成功并 break"——τ 模式下这会把 agent 的第一句开口误判为任务完成，对话走不到第二轮。**裁决：τ 模式下 `get_next_user_input()` 钩子必须拦截"无 tool_call"分支——纯文本回复 = 一次 RESPOND，继续对话；任务成功只允许由 driver 判 `###STOP###`、guard HALT、预算耗尽三条路径结束。**桥接只注册真实工具，不伪造 respond 工具。
3. **REQ task 字段口径（防 hidden instruction 泄露）**：`env.reset()` 的首轮用户消息本身就是 simulator 的一次 LLM 生成，ingest 时预生成既花钱又非确定。定稿：**REQ.task = 通用占位开场白**（如"你好，我需要帮助"，仅作流程触发器），REQ 另存 `{tau_env, tau_task_id}` 引用；**turn 0 由 driver 经 RPC `get_instruction(session_id)` 取回 hidden instruction（纯数据查找，非 LLM），喂给 worker 侧 simulator 生成真实首轮用户消息注入**。hidden instruction 只存在于 driver/simulator 上下文，永不进入 worker 的对话历史（约束 4 不变）。

---

## 作者裁决 v1.4（2026-09-11，针对第四轮对账：三个接口缺口）

**全部接受，本轮后任务书进入可施工状态：**

1. **step RPC 补 `done`/`reward`，终止路径补第 4 条**。源码事实：`Env.step()` 遇 `terminate_tools`（τ 为 `transfer_to_human_agents`，在 ALL_TOOLS 里，agent 可主动调用）即 `done=True` 并当场算 reward。v1.3 的 step 只回 observation|WAITING，丢了 done/reward——agent 正常转人工时 worker 收不到终止信号，会继续空转或漏收 reward。定稿：step 返回 `{observation, done, reward}`；**第 4 条终止路径 = `env.done`（terminate 工具被调用）**，与 ###STOP###/guard/预算并列。
2. **wiki/rules 注入 system prompt（效度问题，不是小问题）**。τ 官方 ToolCallingAgent 以 `{role:"system", content: env.wiki}` 起手——airline/retail 的 rules.md 是任务能否做对的政策依据。不注入，agent 只能瞎猜政策，基线 reward 系统性偏低且**不能反映模型真实水平**。定稿：sidecar 暴露 `get_wiki(session_id)`，driver 在任务开始用它**替换** worker 的 system prompt（τ 模式专用；同时服务于"轮换验证"思路——不同 env 不同政策，天然是判断力泛化的对照组）。
3. **`get_instruction` 补进 §4 RPC 定稿清单**（v1.3 在 §5a.3 用了但清单漏列）。
4. **次要项一并落**：τ 工具 per-session 生命周期——bridge 在每 episode `reset` 后动态注册 `tau__*`、episode 结束注销（tool_registry 进程级初始化的现状下必须显式管理）；**turn 0 顺序修正——driver 在 agent 首次 LLM 调用前就替换占位开场白**，agent 第一眼看到的必须是真实诉求；标注裁决 v1.1 第 1 条中 `--no-deps + 最小依赖集` 表述**作废**（已被 v1.2 完整安装取代），防止实现者按旧文执行。

---

## 0. 背景认知（实施前先验证，不要照抄）

τ-bench（github.com/sierra-research/tau-bench）结构要点：

```
tau_bench/
├── envs/airline|retail/   # 每个域：rules.md(政策) + db.json(纯JSON数据库) + tools(本地Python函数)
├── envs/user.py           # 用户模拟器：LLM 扮演用户，手持 task 的 hidden instruction
├── evaluator.py           # 程序化校验：db 终态比对 + 动作序列检查 + 部分 nl_assertions
└── tasks_airline.py / tasks_retail.py   # 任务定义（instruction + 期望动作/db断言）
```

**关键事实（动工前逐条实测确认，把输出贴进 evidence）**：
1. 环境无外部服务依赖：db 是 JSON，tools 是本地函数，**不需要 Docker/浏览器/网络**——这是它能在 8G 机器上跑的唯一原因；
2. 任务是**多轮对话**：agent 面对的"任务"不是一句话，而是一个持有隐藏 instruction 的用户模拟器；
3. **evaluator 以源码实测为准**（v1.1 修正：对账发现本版 `calculate_reward()` 只有 db 终态 hash + outputs 两类检查，**没有 nl_assertions**；且 GT actions replay 会经 `self.step()` 触发 user simulator 产生额外 LLM 调用——replay 必须注桩 user，见裁决 3）；
4. **任务口径（v1.1 锁定）：仅 test split**——airline ~50 + retail ~115 ≈ 165 条；retail train ~500 条登记在 ingest 报告里但本期不入库。禁止写死数字，以 adapter 实测解析为准。

---

## 1. 全局约束（在 v2.3 之上增补）

1. **依赖隔离（v1.1/v1.2 最高优先级）**：mini-agent 的 conda 环境**一个包都不许动**。τ-bench 全部依赖进独立 venv `.agent/venv/tau/`；安装方式 `pip install -e .` 完整装（v1.2 修正：envs 导入链硬依赖 litellm，绕不开；**litellm 只允许存在于 sidecar venv 内**，mini-agent 环境的禁令绝对有效，worker/bridge 代码禁止 import litellm）。仍禁止 torch/transformers。DeepSeek 一律走 openai 兼容 client + `base_url`。
2. τ-bench 源码放入 `.agent/vendor/tau-bench/`（受 .gitignore 的 `.agent/*` 覆盖，**不进 git**，evidence 记录 commit hash 锁版本），adapter 代码放 `requirements/adapters/tau/`（进 git）。
2.1 **sidecar 进程纪律（v1.1）**：sidecar 监听 `127.0.0.1:8010`（仅 loopback），PID 登记进 `.agent/pidmap.json`；启停脚本 `scripts/tau_sidecar.sh {start|stop}` 复用 shadow.sh 的模式（ss 反查真实监听 PID、等待循环健康检查）；janitor 需认识该进程类型。
3. τ-bench 的 db.json 每 episode 结束必须 reset 回原状（env.reset 语义），**禁止跨任务残留状态**——污染状态 = 后续任务的证据全部失效。
4. user simulator 与 worker 共用同一个 DeepSeek key 可以，但**必须是两个独立的 system prompt/会话**；user 侧禁止泄露 hidden instruction 原文之外的任何信息。
5. 成本护栏：本 Phase 全程 `--limit` 先行；任何批量运行前先出**预估 token 成本**并粘贴进 evidence，单日 API 花费上限由人工设定（默认 ¥50，超出即 BLOCKED 等人裁）。
6. worker 的 `MAX_STEPS=10` 天花板对 τ-bench 不够用（多轮对话轻松超 10 步）：改为环境变量 `SA_MAX_STEPS` 可配，默认仍 10；τ REQ 的 `budget.max_steps=30`，跑批时 `SA_MAX_STEPS=30`。**仅限 τ 批跑场景调高，常规任务不变。**

---

## 2. Phase 5a.0 — 探针闸门（预估 0.5 天，v1.1 升级为探针）

> 目的不是"装完"，是**实测四个未知数**，输出探针报告决定后续细节。探针报告本身就是验收物。

1. vendor 锁版本：clone 到 `.agent/vendor/tau-bench/`，记录 commit hash；
2. **sidecar venv 建立**：`.agent/venv/tau/` 内 `pip install -e .` 完整安装（v1.2 修正：envs 导入链硬依赖 litellm，允许其存在于 sidecar venv），sidecar venv 完整 pip list 入 evidence；
3. **replay 成本探测**：实测 `calculate_reward()` 的 GT actions replay 经 StubUser 注桩后 LLM 调用次数 = 0（数 API 请求数）；
4. **sidecar 冒烟**：起 sidecar 原型，JSON-RPC 完成 `reset(airline, task_0)`（返回 session_id）→ `step`（QueueUser 抛 `WaitingForUser` → 返回 `WAITING_FOR_USER` → `provide_user_msg` 推进）→ `reward` 全回路；driver 侧自写 simulator（openai client，base_url 指向 DeepSeek）跑通一轮用户回合，且**覆盖 v1.3 三条已知地雷**：非阻塞哨兵不死锁、无 tool_call 回复被正确拦截为 RESPOND、turn 0 真实首轮消息由 driver 用 hidden instruction 生成且不泄露进 worker 对话历史。
5. **接口缺口验证（v1.4）**：实测 `transfer_to_human_agents` 触发 `done=True` 且 reward 随 done 一并返回；`get_wiki` 返回非空政策文本；`tau__*` 工具在 episode 结束后已注销（跨 episode 不残留）。
- **验收**：`.agent/evidence/phase-P5a0-evidence.md` 含 commit hash、sidecar venv pip list、replay 零 LLM 实测、sidecar 全回路日志（含 session_id 流转）；`pip list` 于 **mini-agent 环境**执行的前后 diff 为空（隔离证明）。

## 3. Phase 5a.1 — DialogueDriver：多轮回路（预估 1 天）

> 这是本任务书唯一的真实结构改动：worker 从"单指令循环"升级为"可被对话驱动"。

- 新建 `backend/dialogue_driver.py`：`UserSimulator` 包装 hidden instruction，DeepSeek 生成用户回合（v1.1：自写 openai client 实现，**不复用 env 自带 `load_user`**——它依赖 litellm，已被约束第 1 条排除）；`DialogueDriver` 把用户回合逐轮注入 worker 主循环（worker 每轮输出 → driver 喂给 simulator → 拿回下一句用户话 → 注入）。
- 终止三条件（全部走现有 Guard）：用户 simulator 输出 `###STOP###` / 步数达 budget / guard HALT。
- **worker 改动最小化**：主循环抽出一个 `get_next_user_input()` 钩子，默认实现返回 None（单轮模式，行为与现状完全一致）；τ 模式下由 driver 接管。**老任务的 trace 结构不许变（回归验收）。**
- **RESPOND 语义拦截（v1.3，5a.1 的核心）**：worker 现有逻辑"LLM 无 tool_calls → 判任务成功并 break"在 τ 模式下是错的——纯文本回复是 τ-bench 的 RESPOND 动作，不是任务完成。τ 模式下钩子必须拦截"无 tool_call"分支：纯文本 → 记为一次 RESPOND → 经 bridge.step 推进对话。**任务结束只允许四条路径（v1.4 补第 4 条）：driver 判 `###STOP###`、guard HALT、预算耗尽、`env.done`（agent 主动调 terminate 工具如 transfer_to_human_agents——step 返回 done=True 即终局，reward 随 done 一并收下）。**
- **wiki 注入（v1.4）**：任务开始时 driver 调 `get_wiki(session_id)` 取回该 env 的政策文本（rules.md），**替换** worker 的 system prompt——这是任务能否做对的政策依据，不注入则基线 reward 失真。τ 模式专用，常规任务 system prompt 不变。
- **turn 0 顺序（v1.4）**：driver 必须在 agent **首次 LLM 调用之前**就把占位开场白替换为真实首轮用户消息——agent 第一眼看到的必须是真实诉求，不能是"你好，我需要帮助"。
- 每轮用户/助手消息写 span `layer="L", type="dialogue_turn", attributes={turn, role, tokens}`。
- **验收**：跑 1 个 retail 任务，trace 中 dialogue_turn span ≥2 且 role 交替正确；再跑 1 个老的单轮 REQ（如 REQ-001），trace 结构与 v2.3 证据**逐字段一致**（回归）。

## 4. Phase 5a.2 — 工具桥（sidecar 客户端，预估 0.5 天）

> v1.1 架构变更：桥接不再是 in-process 调用，而是对 sidecar（`127.0.0.1:8010`）的 JSON-RPC 客户端。sidecar 服务端 `requirements/adapters/tau/sidecar.py` 在独立 venv 内运行。

- **RPC 接口（v1.4 定稿，全部带 session 隔离）**：`reset(env_name, task_id) -> session_id`；`step(session_id, action) -> {observation, done, reward} | {status:"WAITING_FOR_USER"}`；`provide_user_msg(session_id, text)`；`reward(session_id)`；`list_tools(session_id)`；`get_instruction(session_id) -> str`（纯数据查找，供 driver 喂 simulator）；`get_wiki(session_id) -> str`（env 政策文本，供 driver 替换 system prompt）。每 episode 独立 env 实例，db 状态按 session 隔离，episode 结束必须 reset 回原状（v1.0 约束 3 不变）。
- **工具生命周期（v1.4）**：`tau__*` 工具是 **per-session** 的——bridge 在每 episode `reset` 后动态注册、episode 结束注销（tool_registry 是进程级初始化，必须显式管理注册/注销，防止跨 episode 残留）。
- **user 注入纪律（v1.3 定稿，替代 v1.2 的死锁描述）**：env 构造后覆盖 `env.user = QueueUser()`（或子类化 env，探针里二选一确认——`Env.__init__` 内部会先 `load_user()`，构造后覆盖即可）；`QueueUser.step()` **抛 `WaitingForUser` 异常（非阻塞哨兵）**；sidecar 捕获 → step RPC 返回 `{status:"WAITING_FOR_USER"}`；driver 生成用户消息后经 `provide_user_msg` 推进队列，**原 step 不需要再完成返回观测**（worker 本来就有这条消息）。**sidecar 进程内任何代码路径不得发起 LLM 调用**（验收时可在 sidecar 侧打网络日志自证）。scoring 触发 replay 前把 user 替换为 `StubUser`（固定 `###STOP###`）。
- `requirements/adapters/tau/bridge.py`：从 sidecar `list_tools` 拉当前 env 的工具清单，**动态注册**为 simple-agent 的工具（命名 `tau__<tool_name>`），调用经 JSON-RPC 转发，返回原样回传。sidecar 不可达 → 工具调用立即返回结构化错误（不允许 hang 住 worker 循环）。
- 每次 τ 工具调用走现有 E 层埋点（effect_diff 对 tau 任务恒为空属正常——τ 的状态在 db.json 不在 workspace，**验收时只查 span 存在与参数留痕，不查 effect_diff 非空**）。
- τ 模式下 shell/file_ops 等本地工具**整体关闭**（τ 任务不需要，开着只会污染路由统计），关闭动作写 span `type="tool_scope", attributes={mode:"tau", disabled:[...]}`。
- **验收**：任一 τ 任务的 trace 中，工具调用 span 的 name 全部以 `tau__` 开头，无 shell 调用。

## 5. Phase 5a.3 — 评判翻译：evaluator → V 层（预估 1 天）

- `requirements/adapters/tau/scoring.py`：episode 结束后经 sidecar 调 τ-bench evaluator，把结果翻译成 V 层（v1.1 按源码实测修正——本版 evaluator 只有两类检查）：
  - db 终态比对 → assertion `db_final_state`（blocker）；
  - outputs/动作序列检查 → assertion `actions_match`（blocker）；
  - **nl_assertions 本版不存在，条款删除**；若探针发现个别任务带 LLM 判定项，默认降级 minor 且 `--cheap` 跳过；
  - **replay 注桩（v1.1，按探针结论落地）**：若 `calculate_reward()` 的 GT replay 会触发 user simulator，scoring 必须给 replay 路径注入桩 user（固定返回 `###STOP###`），replay LLM 成本 = 0 并写 span 证明；
  - 汇总 reward∈[0,1] → loss = 1 - reward，写 `type="verdict"` span + JudgeVerdict。
- 每条 τ 任务生成 REQ JSON（v1.3 口径修正）：`{req_id:"TAU-A-001", split, task:"你好，我需要帮助", tau_env:"airline", tau_task_id:3, assertions:[db_final_state, actions_match, ...], budget:{max_steps:30, max_tokens:100000, timeout_s:900}, source:"tau-bench/airline"}`。**task 字段是通用占位开场白（仅触发流程），不是首轮用户消息**——首轮真实用户消息由 driver 在 turn 0 经 `get_instruction(session_id)` 取回 hidden instruction 后由 simulator 生成（hidden instruction 不进 worker 对话历史，不违反约束 4）。
- **验收**：对 1 个故意做错的任务（agent 摆烂直接 STOP），loss>0 且 V 层 span 含 `db_final_state{passed:false}`；loss=0 路径用 **GT actions replay 驱动的完美 episode** 验证（v1.1 修正：不依赖 DeepSeek 真能完成任务——基线期它大概率完不成，评判链正确性必须独立于 agent 水平被验证）。

## 6. Phase 5a.4 — 批量入库与分族（预估 0.5 天）

- `scripts/tau_ingest.py`：解析 **test split** τ 任务（v1.1 锁口径：airline ~50 + retail ~115 ≈ 165；retail train ~500 只在报告中登记、本期不入库）→ REQ JSON 落 `requirements/tau/`；用现有 `signature.py` 去重（相似度 >0.85 视为同族，保留代表）；按 sig_family 分层抽样切 train/dev（**dev 占比 ≥15%，dev 集对 updater 不可见**的铁律不变）。
- 生成 `.agent/reports/tau-ingest.md`：任务总数、族数、去重丢弃数、train/dev 分布、预估总成本（v1.1 成本模型：**agent + user simulator 双模型 ≈ 单模型 2 倍**，按平均 15 轮 × 单轮 ~2k token × 2 估算；replay 注桩后该项为 0）。
- **验收**：报告数字与 `ls requirements/tau/ | wc -l` 一致；抽 3 条 REQ 人工可读懂；预估成本粘贴进 evidence 并等人确认后才许进 5a.5。

## 7. Phase 5a.5 — 首轮烧批 + 学习曲线 v1（预估 1 天，成本敏感）

- `--limit 10` 先跑一个 mini-epoch：验证链路 + 出第一份成本实测（对比 5a.4 预估值，偏差 >50% 要停下来查）。
- 确认后跑 train 集首个完整 epoch，走现有 eval_loop / epoch_gate 管线；**updater 本轮只出提案，人工审**（v1 铁律不变）。
- 产出 `.agent/reports/tau-epoch-1.md`：loss 分布、按 sig_family 的 token 均值、guard 熔断率、abstain 率、成本实测。
- **预期管理（v1.1）**：参照官方 gpt-4o airline Pass^1≈0.42，DeepSeek 基线 reward 大概率低（0.1~0.25 不意外）、方差大。**本期目标是学习信号（epoch 间相对改善 + 同族 token 下降），不是绝对 reward；epoch-1 的唯一职责是交出真实完整的基线。**
- **验收**：epoch-1.json 存在且每条 TAU REQ 有 loss；`precedents` 表新增行数 >0；`routes` 表出现 τ 族条目；报告粘贴进 evidence。

---

## 8. 总验收清单（全部通过 = P5a 完工）

| # | 项 | 检查 |
|---|---|---|
| 1 | 探针 | commit hash 锁定；sidecar venv pip list 入证据；replay 注桩零 LLM 实测；session_id 隔离流转；**mini-agent 环境 pip list 前后 diff 为空** |
| 2 | 多轮 | dialogue_turn span 正确；老 REQ 回归逐字段一致 |
| 3 | 工具桥 | sidecar 回路通；τ 任务工具全 `tau__` 前缀；无 shell 泄漏；sidecar 不可达时结构化报错不 hang |
| 4 | 评判 | 摆烂任务 loss>0 + blocker 断言 false；**GT replay 完美 episode loss=0**；replay 注桩零 LLM 成本有 span 证明 |
| 5 | 入库 | 仅 test split；ingest 报告数字与文件数一致；成本预估（双模型口径）经人工确认 |
| 6 | 烧批 | epoch-1 基线真实完整 + precedents/routes 有 τ 数据 + 成本实测入证据 |
| 7 | 元规则 | 每 Phase 证据文件齐、可重放；无源数据为零 |

## 9. 时间与人力

| Phase | 预估 | 卡点 |
|---|---|---|
| 5a.0 | 0.5 天 | 探针四问，尤其最小依赖集和 replay 成本 |
| 5a.1 | 1 天 | **唯一结构改动**；回归验收最严 |
| 5a.2 | 0.5 天 | sidecar 启停复用 shadow.sh 模式 |
| 5a.3 | 1 天 | 评判链正确性用 GT replay 独立验证 |
| 5a.4 | 0.5 天 | 成本预估（双模型口径）需人工确认才放行 |
| 5a.5 | 1 天 | 首个完整 epoch 的实测成本决定后续放量节奏 |
| 合计 | **约 4.5 个工作日** | 依赖隔离若探针不顺，预留 +0.5 天 buffer |

## 10. 明确不做（本期）

τ²/τ³-bench、GAIA、retail train ~500 条放量（等 165 条上烧出学习信号再议）、τ 任务的 skill 编译固化、任何前端。τ-bench 烧出的 precedents/routes 是后续 spec 数据飞轮的种子，飞轮本身（P5b）另立任务书。
