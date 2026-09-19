# simple-agent 判断力机制 · 执行方案（opencode 实施版）v2.3

> **实施者**：opencode 调用 DeepSeek-V4 ｜ **目标仓库**：https://github.com/zigezi/WHU-DZH 分支 `simple-agent`，本次只改 `simple-agent/` 子目录
> **运行环境**：单台 8G 内存 CPU 服务器，推理全走 DeepSeek API，本机只做编排与确定性执行
> **总原则**：确定性语义全部落代码；LLM 只做提案，不做控制；每 Phase 结束必须能独立验收。

---

## ⛔ 元规则（先于一切，最高优先级，违反 = 本 Phase 作废重来）

> **历史教训：上一版允许 opencode 跳过 monitor 观测升级直接跑 P4 判断力测试，产出了 effect_diff=NULL 的假测试报告。以下规则不可协商、不可解释、不可绕开。**

**MR-1　交付 = 代码 + 证据，缺一不收。**
每个 Phase 的交付物 = 代码改动 **加上** 该 Phase 全部"验收"命令的**真实终端输出原文粘贴**（写入 `.agent/evidence/phase-PX-evidence.md`）。只交代码不交证据 = 未完成；证据与代码不一致 = 造假，该 Phase 全部作废。

**MR-2　Phase 是闸门，不是建议。**
严格按 P0 → P1 → P2（含 A 段）→ P3（含 B/C 段）→ P4 顺序执行。**禁止跳号、禁止并行、禁止"先做后面的简单项"。** 进入 P(N) 的唯一条件是 P(N-1) 的证据文件存在且全部验收项通过。

**MR-3　P4 的两条前置硬条件（单独列出，因为上次就是在这里翻的车）：**
- 进入 P4 前，必须已存在证据：`sqlite3 logs/trace.db "SELECT json_extract(attributes,'$.effect_diff') FROM spans WHERE layer='E' AND json_extract(attributes,'$.effect_diff') IS NOT NULL LIMIT 3"` 返回**非空**（A 段验收，见 §4.0）；
- 且 `.agent/reports/decomposition-report.md` 已生成且非模板（C 段验收，见 §5.0）。
- 两条缺任何一条，P4 一行代码都不许写。评测器造不出观测数据的判断力测试 = 测了个寂寞。

**MR-4　禁止伪造验收。**
禁止为了"让验收通过"而：手写假 span 进库、篡改 SQL 输出、用 echo 伪造日志、跳过命令直接写结论。每条验收证据必须可重放（同一命令再跑一遍结果一致）。

**MR-5　卡住就停，不许绕。**
任何验收命令失败：先修到通过，再继续。修了 3 次仍失败 → 停下来把失败输出原样写入 evidence 文件并在 commit message 标记 `BLOCKED: <原因>`，**等待人工裁决**，不允许自行降低验收标准或跳过该项。

**MR-6　报告溯源（2026-09-11 增补）。**
`.agent/reports/` 下只允许存在由 `eval_loop.py` / `epoch_gate.py` / `plan_observer.py` 实际运行产出、且有对应原始数据（epoch-*.json / trace.db 记录）的文件。**现存 `convergence.md`（epoch 6/7/8 loss=9.5/9.6/9.7 但无任何 epoch-*.json）是无源数据，开工前第一件事：删除并写入 evidence 说明**。今后任何无源报告 = 违反 MR-4。

---

## 作者裁决 v2.1（2026-09-11，针对 opencode 服务端评审的三个问题）

**评审属实，三条硬阻塞全部承认。裁决如下：**

**裁决 1（B/C 段死结）——批"极简真实规划器"方案，不批 MR-4 豁免。**
评审正确：原书要求 plan span 但规划器未落地，是循环依赖，属本书作者的设计错误。解法**不是**手工伪造 plan span（永远不许），而是在 P3 新增 §5.0.0：一个**确定性的极简线性规划器**——把任务真实切为单链计划（节点=预期步骤），`record_plan()` 被真实调用，`plan_node_id` 真实下传。它是真实代码而非伪造数据，因此**无需豁免 MR-4**。副作用说明：线性计划下 `owns_conflicts=0`、`rework_edges=0` 是**真实值**（当前确实无并行、无返工），如实报告即为合格；等未来真多分支规划器落地，这些指标自然长出意义。

**裁决 2（P0–P3 追溯）——接受"补跑并补证据"，不认作废。**
代码已经评审确认可行，推倒重来是浪费。规则：MR-1 自此向后严格生效；已提交的 P0–P3，每 Phase 把所有验收命令**真实重跑一遍**（含状态型验收如 kill 重启查 /tasks、构造死循环触发 g_halted），输出原文粘贴进对应 evidence 文件，每个 Phase 一个 `evidence-backfill` commit（尾部 `Phase: PX | Evidence-Backfill: true`）。注意评审实测 V/G 层 span 与 effect_diff 均为 0 条——说明代码写了但从未真跑过任务，补证据时必须真跑，不是补写。

**裁决 3（convergence.md）——删除重来，按 MR-6 执行。**

**缺陷清单处置（评审第三节逐条）：**

| 缺陷 | 裁决 |
|---|---|
| shadow.sh 仍用 `$!`+`sleep 2` | §6.2 两处修复本来就是强制项，P4 验收时以证据卡死，不解释 |
| worker.py:195 写死 `range(MAX_STEPS=10)` | 真 bug，改：循环上界 = `min(需求 budget.max_steps, MAX_STEPS)`，已并入 §4.2 |
| shell.py 放行 rm/cp/mv/git commit/curl/wget | 原书"默认只读"表述有误（任务本就需要写 workspace）。按 §4.3 修订后的白名单执行 |
| REQ-*.json 的 task 字段未提交 | requirements/ 必须随 P1 commit 入库；§1.1 已增补：`task` 字段为必填，loader 无 task 拒绝入库；eval_loop 只许用 `task` 字段当任务，禁止拿 ears_text 喂模型 |
| eval_loop 真实调用 API 有成本 | 属实，这是设计本意（真评测才真烧钱）。加 `--limit N` 调试开关；工期表已加 1 天 |
| P4 四个文件 untracked 先行 | 不清除也不追认。处置：保持 untracked 隔离，P4 闸门通过后**逐行对照 §6 复审**，合格的代码在 P4 内正式 commit；任何抄近路逻辑（如伪造 epoch）必须删除。P4 的"工作"（跑 epoch、出提案）在闸门通过前一律禁止 |

---

## 作者裁决 v2.2（2026-09-11，针对第二轮评审的五条硬问题）

**五条全部接受。裁决与修订如下：**

1. **API key（阻断·环境）** → 新增 **P-1 前置**（见 §1.5）：由人工注入 `DEEPSEEK_API_KEY` 到 `backend/.env`（禁止入库、禁止写进任何代码/证据文件），验收冒烟任务真实跑通后才允许开工。worker 启动时 key 缺失要**大声报错退出**，禁止 `api_key="missing"` 静默建 client。
2. **.gitignore 吃掉 .agent/** → 开例外：`!.agent/evidence/`、`!.agent/reports/`、`!.agent/proposals/` 必须可被 git 跟踪（证据/报告/提案是交付物）；`worktrees/`、`logs/`、`pidmap.json` 保持忽略。MR-1 的 commit 尾部指向未跟踪文件 = 验收不通过。
3. **规划器三处补设计** → 全部写入 §5.0：接口对齐（`record_plan` 必填参数填 `planner_model="deterministic-linear-v1"`、`prompt_version="n/a"`；`decomposition_report` 公开签名统一为 `(trace_id)`）、step→node 映射规则（纯时间序对齐，见 §5.0.0）、md 写入者（`plan_observer.write_decomposition_report()`）。**附带说明记录在案：线性计划下 owns_conflicts/rework_edges 恒为 0，区分度为零——C 段本期定位是观测脚手架，不是 P4 的奖励信号；P4 奖励信号只来自 epoch loss（断言体系）。**
4. **shell 白名单** → 按评审意见重写 §4.3：shlex 解析 + 管道/分号/逻辑符逐段校验、`$()` 与反引号一律拒绝、`find -exec/-delete` 拒绝、**sqlite3 必须带 `-readonly`**（堵死篡改 trace.db 违反 MR-4 的通道）、重定向目标路径纳入 workspace 检查。并如实标注：**白名单是审计与熔断层，不是沙箱**；python -c 等残余风险由"G 层全量留痕 + MR-4 可重放 + 人工复审"兜底。
5. **A 段验收 2 措辞 bug** → 修正 §4.0：改用重复失败任务（喂同一失败命令 ≥2 次）触发 feedback 链；feedback span 层级统一为 **G 层**（与代码及规格书 A.2 一致），任务书原文"L 层"系笔误。

---

## 作者裁决 v2.3（2026-09-11，针对第三轮评审：四条实测对齐问题）

**全部接受，无一驳回。这四条都是"文档 vs 代码/工具链现实"的对齐错误，责任在任务书作者：**

1. **`.gitignore` 例外写法不生效（git 规则：父目录被 ignore 后子路径 `!` 例外无效）** → 修订约束第 5 条：必须把 `.agent/` 改为 `.agent/*`（忽略内容、不忽略目录本身）再开 `!.agent/evidence/` 等例外。开工前用 `git check-ignore -v .agent/evidence/x.md` 自证例外生效，输出入 P-1 证据。
2. **§4.0 验收 1 的 SQL 引用了不存在的列 `id`**（spans 主键是 span_id）→ 改 `ORDER BY rowid DESC`。此命令在 MR-5 下会直接 BLOCKED，属任务书放错雷。
3. **`backend/.env` 根本不会被读取**（全仓库无 dotenv，worker 只读 os.getenv）→ §1.5 增补：worker.py 加一个 10 行内的极简 .env 解析（不设新依赖；或批准 `python-dotenv` 作为轻量例外，二选一），否则 P-1 冒烟跑不起来。
4. **`owns_conflicts/rework_edges` 定义与实现矛盾** → 采纳"改实现贴合规格本意"：`owns_conflicts` = **无依赖关系**的节点对之间的 effect_diff 文件交集（线性链所有节点对都有上下游依赖 → 恒 0，这才是"恒为 0"成立的正确前提）；`rework_edges` = 节点失败后重做次数（feedback_injected 触发的同节点重入），**故意失败任务必然非 0，这是真实信号不是 bug**。任务书 v2.2"两者恒为 0"的表述作废。

**小问题一并修**：§4.3 验收改为 `echo hi > a.txt`（cwd=workspace，与 SYSTEM_PROMPT 禁止加 workspace/ 前缀一致）；§5.0.1 删去"main.py `_submit` 链路同步改"（规划器在 run_task 内部生成，main 无需感知）；§1.5 注明本机只有一个 key 时与 opencode 共用可接受（隔离管理让位于现实，禁止入库的红线不变）。

---

## 0. 现有代码认知（实施前先读这些文件）

```
simple-agent/
├── backend/
│   ├── main.py          # FastAPI：/task/submit(GET,改POST) /task/{id} /tasks /metrics
│   ├── worker.py        # agent 主循环：MAX_STEPS=10，L/C/T 层 span + O 层自检
│   ├── schema.py        # TaskRequest/TaskStatus
│   ├── monitor.py       # 独立轮询进程（5s）：全局指标 + Shapley 诊断日志
│   ├── monitor/         # collector/trace_store(SQLite WAL)/metrics/anomaly(10规则)/diagnosis(Shapley)/report/server
│   └── tools/           # registry(E层埋点)/file_ops/shell/init
├── frontend/src/        # 本期仅在 P0 改提交接口时同步改调用方式
├── workspace/           # 任务产物目录
├── docker-compose.yml   # backend:8000 / monitor / frontend:3000
└── requirement.txt
```

**先跑冒烟**：`cd backend && python -m py_compile main.py worker.py monitor.py schema.py monitor/*.py tools/*.py`。`tools/registry.py` 中 `exec_span.error = result.error or None` 一行疑似残缺，如编译报错则补全为合法赋值。

---

## 1. 全局约束（违反任何一条 = 返工）

1. 不引入重型依赖：**禁止 torch/transformers**；新增依赖仅限 `numpy`（签名相似度用，可选）。默认签名用哈希特征，不强制 embedding 模型。
2. 所有持久化走现有 `monitor/trace_store.py` 的 SQLite（WAL），新增表用 `_ensure_column`/建表迁移模式，**禁止再建内存 dict 当数据源**。
3. 所有新判决类输出统一走 `JudgeVerdict` schema（P2 定义）。
4. `kill*/pkill*/systemctl*/shutdown*` 命令在所有 agent 可触达的 shell 工具中永久 deny。
5. 每 Phase 单独 git commit，commit message 带结构化尾部：`Phase: PX | Loss-Before: n/a | Gate: manual | Evidence: .agent/evidence/phase-PX-evidence.md`。**`.gitignore` 处理（v2.3 修正写法）：把 `.agent/` 改为 `.agent/*`**（父目录被整体 ignore 时子路径 `!` 例外无效——只忽略内容、不忽略目录本身，例外才生效），再开 `!.agent/evidence/`、`!.agent/reports/`、`!.agent/proposals/`；`!.agent/worktrees/`、`!.agent/logs/`、`pidmap.json` 不开例外。改完后必须用 `git check-ignore -v .agent/evidence/x.md` 自证例外生效，输出粘进 P-1 证据。
6. 不改 NL2EARS/，不动 8000 端口现有对外 API 的返回字段（只做加法）。
7. `DEEPSEEK_API_KEY` 只经 `backend/.env` 注入（.env 必须在 .gitignore）；**key 禁止出现在代码、commit、evidence 文件、日志中**（粘贴终端输出前先脱敏）。

---

## 1.5 Phase -1 — 环境前置（人工执行，半小时，开工闸门）

> 没有 key 就没有任何真实数据，整本任务书停在闸门外。此项由**人**完成，不委托 agent。

1. 将 DeepSeek key 写入 `backend/.env`：`DEEPSEEK_API_KEY=sk-...`。本机只有一个可用 key 时，与 opencode 共用可接受（隔离管理让位于现实，v2.3 注明）；**禁止入库的红线不变**。
2. **先修读取链再谈注入（v2.3）**：全仓库无任何 dotenv 加载，`.env` 当前写了也白写。`worker.py` 启动时加载 `backend/.env`——二选一：手写 10 行内极简解析（`KEY=VALUE` 逐行、跳过注释与空行，`os.environ.setdefault`），**或**批准 `python-dotenv` 作为全局约束第 1 条的轻量例外。推荐前者。
3. `worker.py` 启动校验：读不到 key → 打印明确错误并退出，**删除 `api_key="missing"` 静默兜底**。
4. **验收（人工粘贴）**：`curl localhost:8000/` 正常 + 提交一条真实任务（"在 workspace 创建 smoke.txt 写入 ok"）成功完成、trace 含真实 tool_call span。证据写入 `.agent/evidence/phase-P-1-evidence.md` 并 commit（注意脱敏）。

---

## 2. Phase 0 — 测量地基（预估 1 天）

### 0.1 code_version 埋点
- 新建 `backend/version.py`：`get_code_version()` 返回 `git rev-parse --short HEAD`（失败回退 `"unknown"`）。
- `monitor/trace_store.py`：`_ensure_column("traces", "code_version", "TEXT")`。
- `worker.py::run_task`：创建 Trace 时写入 `code_version=get_code_version()`；`monitor/schema.py::Trace` 加同名字段。
- **验收**：`sqlite3 logs/trace.db "SELECT code_version FROM traces ORDER BY start_time DESC LIMIT 1"` 非空。

### 0.2 任务状态统一入库（消灭双口径）
- `trace_store.py` 新增表 `tasks`（字段 = TaskStatus 全部字段 + steps JSON 序列化）。
- `worker.py`：写 `task_store` dict 的位置全部改写 `tasks` 表；`main.py` 的 `/task/{id}`、`/tasks`、`/metrics` 改从 DB 读。删除 `task_store` dict。
- **验收**：`kill` 后端进程重启后，`GET /tasks` 仍能查到重启前的任务。

### 0.3 提交接口改 POST
- `main.py`：`/task/submit` 改为 `@app.post`，body 为 `TaskSubmitIn{content, req_id?}`；保留旧 GET 但返回 `{"deprecated": true, ...}` 转发提示。
- `frontend/src` 中对应调用改为 POST JSON。
- **验收**：`curl -X POST localhost:8000/task/submit -H 'Content-Type: application/json' -d '{"content":"在 workspace 创建 hello.txt 写入 hi"}'` 返回 task_id 且任务成功。

### 0.4 janitor 保险丝
- 新建 `scripts/janitor.py`：清理 exited>1h 的容器、`workspace/` 中 >7 天且无关联 running trace 的产物、30 天前 trace 导出 gzip 后删行。干跑模式默认开（`--apply` 才真删）。
- **验收**：`python scripts/janitor.py` 打印清理清单不报错。

### 0.5 任务族复发率统计（决策点）
- 新建 `scripts/family_stats.py`：读 trace.db 全部 `task_content`，用关键词哈希签名（`signature.py` 的 P3 简化版先内联实现：分词→Top10 关键词排序→md5）聚类，输出各族计数与占比。
- **验收**：生成 `.agent/reports/family-stats.md`；**Top 族占比 >50% → P3 的编译固化全量做；否则 P3 只做路由表，编译留桩**。把结论写进报告。

---

## 3. Phase 1 — V 层：尺子（预估 2 天）

### 1.1 需求集格式与入库门禁
- 新建 `requirements/` 目录，每条需求一个 JSON：
```json
{"req_id": "REQ-001", "split": "train",
 "title": "工具连续失败告警",
 "task": "反复执行 cat workspace/不存在.txt 直到系统终止你",
 "ears_text": "WHEN 同一工具连续失败2次, THE SYSTEM SHALL 记录T001异常并终止任务",
 "assertions": [{"name": "t001_fired", "cmd": "sqlite3 logs/trace.db \"SELECT 1 FROM spans WHERE layer='G' AND json_extract(attributes,'$.rule')='T001' LIMIT 1\" | grep -q 1", "severity": "blocker"}],
 "budget": {"max_steps": 10, "max_tokens": 30000, "timeout_s": 600}}
```
- `requirements/loader.py`：加载时校验——**无 assertions 的需求直接拒绝入库**（绑定率 100% 门禁）；**无 `task` 字段同样拒绝入库**（v2.1 增补：`task` = 直接可执行的自然语言指令，`ears_text` 只是规格说明，**eval_loop 只允许把 `task` 字段喂给模型**）；`split` 只允许 train/dev。
- `requirements/` 全部 REQ 文件随 P1 commit 入库，不允许只留在工作区 diff 里。
- 编写首批 **8 条需求**（6 train + 2 dev），覆盖：正常产出类 3 条、故意触发失败类 2 条（喂一个会失败的 shell 命令，断言熔断触发）、歧义类 1 条（需求故意缺参数，断言产物不存在且任务未谎称成功）。

### 1.2 V 层执行器
- 新建 `monitor/vlayer.py`：
  - `run_assertions(req_id) -> list[AssertionResult]`：subprocess 跑每条 `cmd`（timeout 30s），exit 0 = pass；
  - 每条断言写 span：`layer="V", type="acceptance_check", attributes={req_id, name, passed, severity}`；
  - `verdict(req_id)`：按 severity 加权（blocker3/major2/minor1）算 loss，写 `type="verdict"` span，返回 `JudgeVerdict`。
- **验收**：对一条故意失败的需求执行，`sqlite3` 能查到 V 层 span 且 loss>0。

### 1.3 每步进度曲线
- `worker.py`：任务带 `req_id` 时，每步结束调用 `vlayer.run_assertions` 中标记 `cheap: true` 的断言子集，写 span `type="progress", attributes={step:k, passed:n, total:m, tokens_so_far:x}`。
- **验收**：monitor 日志或 SQL 能画出单任务 passed(k) 随 step 的曲线数据。

---

## 4. Phase 2 — G 层：刹车 + A 段观测（预估 2 天）

> ⚠️ **本 Phase 含两段，缺一不算完成**：4.0（A 段观测，来自《monitor三段观测扩展规格》）是 4.1–4.3 的**前置**——没有 effect_diff，熔断归因和后续 P4 全部失去证据源。先做 4.0。

### 4.0 【前置·阻断项】monitor A 段：执行效果与反馈链观测

- **4.0.1 效果快照**：`tools/registry.py` 的 E 层埋点中，工具执行前/后各做一次 `_manifest()`（workspace 文件路径→md5 的映射快照），diff 后写入执行 span：`attributes.effect_diff = {"created": [...], "modified": [...], "deleted": [...]}`（无变化则为三个空数组，**字段必须存在，不允许 NULL**）。
- **4.0.2 shell 结果留痕**：`tools/shell.py` 执行 span 增补 `attributes.exit_code`、`stdout_tail`（末 500 字符）、`stderr_tail`（末 500 字符）。
- **4.0.3 反馈链 span**（v2.2 修正：层级统一为 **G 层**，与规格书 A.2 及代码一致，旧文"L 层"系笔误）：agent 因失败/异常收到纠正性反馈时，写 span `layer="G", type="feedback_injected", attributes={source_span_id, reason}`；反馈后模型下一步响应写 `layer="G", type="feedback_response", attributes={corrected: bool}`。触发时机与 guard 一致：**同一失败签名第 2 次出现时注入**（单次失败不产生反馈链）。
- **验收（全部输出粘贴进 evidence 文件）**：
  1. 执行一个"创建文件+跑失败 shell"的任务后，`sqlite3 -readonly logs/trace.db "SELECT json_extract(attributes,'$.effect_diff') FROM spans WHERE layer='E' AND json_extract(attributes,'$.effect_diff') IS NOT NULL ORDER BY rowid DESC LIMIT 3"` 返回**非空且 created/modified/deleted 键齐全**（v2.3 修正：spans 主键是 span_id，无 `id` 列，用 `rowid`）；
  2. **用重复失败任务验收反馈链**（v2.2 修正，如 REQ-004：反复执行同一会失败的命令 ≥2 次）：该任务中 `type='feedback_injected'` 与 `type='feedback_response'` 的 span 均存在；
  3. shell span 含非空 `exit_code`。

### 4.1 统一判决接口
- 新建 `monitor/judges.py`：
```python
class JudgeVerdict(BaseModel):
    decision: str            # PASS/FAIL/PARTIAL/HALT/ABSTAIN
    confidence: float
    domain_check: bool       # False = 出适用域，弃权升级
    evidence_refs: list[str] # span_id / trace_id / 文件路径
    form: str                # rule | table | llm
```
- V 层 verdict、G 层熔断、后续路由判决全部改为此类型返回值。

### 4.2 熔断状态机 + 无进展检测
- 新建 `monitor/guard.py`：
```python
class Guard:
    def __init__(self, max_steps=10, max_tokens=30000, timeout_s=600, repeat_threshold=3): ...
    def before_step(self, trace_id, step, tokens_used) -> JudgeVerdict   # 预算三阈值
    def after_tool(self, trace_id, tool_name, args, error) -> JudgeVerdict  # sha1(tool+json(args)+error) 连续重复 >= repeat_threshold → HALT
    # 状态机 CLOSED/OPEN/HALF_OPEN；OPEN 后冷却 60s 允许一次试探
```
- 每次熔断写 span `layer="G", type="circuit_break", attributes={reason, evidence}`。
- `worker.py` 主循环接入：`before_step` 返回 HALT → 任务状态 `g_halted`，跳出循环，不再调 LLM。
- **预算一致性（v2.1 修 bug）**：`worker.py` 循环上界不得写死 `range(MAX_STEPS)`，改为 `min(需求 budget.max_steps, MAX_STEPS)`——MAX_STEPS=10 是系统安全天花板，需求预算在其内生效，需求 max_steps>10 时以 10 为准并写日志。
- **验收**：构造任务"反复读取不存在的文件"，第 3 次重复后任务以 `g_halted` 终止，总 token < 预算的 40%。

### 4.3 shell 工具白名单（v2.2 重写）

> **定位诚实声明：白名单是审计与熔断层，不是沙箱。** 它挡不住决意绕过的模型（`python -c` 残余风险存在），真正的安全边界是：G 层全量留痕 + MR-4 证据可重放 + 人工复审。本节目标是"意外与偷懒进不来"，不是"恶意出不去"。

- **解析规则（先解析后判定，v2.2 增补）**：
  1. `shlex` 分词；按 `|`、`;`、`&&`、`||` 切段，**每一段独立过白名单**，任一不过则整条拒绝；
  2. 命令替换 `$()` 与反引号：**一律拒绝**（解析前检测原文）；
  3. 重定向 `>`、`>>`、`tee` 的目标路径：与写命令同等检查（必须落在 `workspace/` 内）；
  4. 所有路径参数经 `os.path.realpath`（相对路径以任务 workspace 为 cwd）规范化后判定，`..` 穿越出 workspace 一律拒绝。
- **三层名单**：
  1. **只读命令**（ls/cat/grep/find/git status/git diff 等）：放行。特例：`find` 带 `-exec`/`-delete` 拒绝；**`sqlite3` 必须带 `-readonly` 标志才放行**（可写库的 sqlite3 能 DELETE/UPDATE/ATTACH 篡改 trace.db，与 MR-4 直接冲突，堵死）；
  2. **写命令**（rm/cp/mv/touch/mkdir/重定向）：仅当所有路径 realpath 后均在 `workspace/` 内放行；`python/pytest/npm install` 放行（残余风险见上）；
  3. **显式 deny**：全局约束第 4 条（`kill*/pkill*/systemctl*/shutdown*`）；`git commit/git push`（版本控制只归人工与 opencode）；`curl/wget`（网络出口默认关闭）。
- 拦截写 span `layer="G", type="permission_check", attributes={cmd, verdict, reason}`。
- **验收（五条全过，G 层 span 齐全）**：`rm -rf /` 拦截；`rm ../backend/main.py`（cwd=workspace，realpath 穿越）拦截；`sqlite3 logs/trace.db "DELETE FROM traces"`（无 -readonly）拦截；`cat $(pwd)/x`（命令替换）拦截；`echo hi > a.txt`（cwd=workspace，v2.3 修正：与 SYSTEM_PROMPT 禁止加 workspace/ 前缀一致）放行。

---

## 5. Phase 3 — 记忆与路由 + B/C 段观测（预估 2.5 天）

> ⚠️ **本 Phase 含两段**：5.0（B/C 段观测，来自《monitor三段观测扩展规格》）与 5.1–5.4 同阶段交付。C 段产物 `decomposition-report` 是 **P4 前置硬条件 MR-3 之二**，不做完不许进 P4。

### 5.0 monitor B/C 段：规划过程与切分质量观测

- **5.0.0【前置·作者裁决 v2.1/v2.2】极简线性规划器（解 B/C 死结，禁止伪造 plan span）**：新建 `backend/planner.py`，确定性代码、不调 LLM：`make_plan(req) -> Plan`，把任务切为单链节点序列（解析 `task` 文本中的动作动词序列，上限 10 节点，解析不出动作则退化为单节点 `{node_id:"n0", owns:["workspace/"]}`）。它是真实规划器（当前为退化形态），不是数据伪造。`worker.run_task` 开头调用它。**本期 C 段定位是观测脚手架，不是 P4 奖励信号（P4 奖励只来自 epoch loss）。**
- **step→node 映射规则（v2.2 增补，纯时间序对齐，不假装语义归因）**：第 k 步（0 起）→ `node_id = "n{min(k, node_count-1)}"`；同一步内的多个 tool_call 全部继承该步节点；无 tool_call 的步不产生 E span。此为粗粒度时间对齐，真实的语义归因等未来规划器落地后再升级，映射函数必须集中定义在 `planner.py` 里以便届时单点替换。
- **5.0.1（B 段）规划留痕**：新建 `monitor/plan_observer.py`。`record_plan(trace_id, req_id, plan_json, planner_model, prompt_version, ...)` 写 span `layer="L", type="plan", attributes={plan_id, node_count, max_depth, schema_valid, owns_disjoint}`；必填参数取值：`planner_model="deterministic-linear-v1"`，`prompt_version="n/a"`（确定性规划器无 prompt，如实填写）。`worker.py` 每个执行 span 增补 `attributes.plan_node_id`（按上述映射规则真实下传；v2.3 修正：规划器在 `run_task` 内部生成，`main.py` 无需感知 plan 节点，删掉"_submit 链路同步改"）。
- **5.0.2（C 段）切分质量报告**：`plan_observer.py` 提供 `decomposition_report(trace_id) -> dict`（**公开签名统一为 trace_id**，v2.2 对齐）：聚合 `{node_success_rate, rework_edges, owns_conflicts, token_cv, critical_path, replan_count}`。指标定义（v2.3 修正，实现须贴合规格本意）：
  - `owns_conflicts` = **无依赖关系的节点对**之间 `effect_diff`（来自 4.0，这就是 A 段必须先做的原因）的文件交集。线性链中所有节点对都有上下游依赖 → 恒为 0 是真实值；**不得**用"被 ≥2 节点碰过的文件数"的算法（那会把正常的上游→下游交接误判成冲突）；
  - `rework_edges` = 节点失败后重做次数（feedback_injected 触发的同节点重入）。**故意失败任务（如 REQ-004）必然非 0——这是真实信号，不是 bug**（v2.2"恒为 0"的表述作废）。
  - **写入者明确为 `write_decomposition_report(trace_id)`**（v2.2 增补，此前全仓库只有返回 dict 没有写盘者）：生成/追加 `.agent/reports/decomposition-report.md`（含 planner 排行表）。
- **验收**：
  1. 任一任务完成后，`sqlite3 -readonly logs/trace.db "SELECT 1 FROM spans WHERE type='plan' LIMIT 1"` 非空，且该任务的 E 层 span 均含 `plan_node_id`；
  2. `.agent/reports/decomposition-report.md` 由 `write_decomposition_report()` 真实生成且含真实数值（线性计划下 0 值合法，占位符非法），粘贴进 evidence 文件。

### 5.1 任务签名器
- 新建 `backend/signature.py`：`sign(text) -> str` = 分词（简单正则切分即可）→ 去停用词 → Top10 关键词排序拼接 → md5 前 12 位；`similarity(a,b) -> float` = 关键词集合 Jaccard。**不引入 embedding 依赖**（接口预留）。
- **验收**：两条语义相近任务（"创建文件写内容A"/"新建文件写入内容B"）similarity > 0.3；无关任务 < 0.1。

### 5.2 路由后验表（判断力的权重）
- `trace_store.py` 新表 `routes(sig_family TEXT, arm TEXT, alpha REAL, beta REAL, total_tokens REAL, n INTEGER, env_fp TEXT, PRIMARY KEY(sig_family, arm, env_fp))`；`env_fp` = `{MODEL_NAME}`。
- 新建 `monitor/routing.py`：`choose(sig_family, arms) -> arm`（Beta 后验 Thompson 采样，ε=0.1 随机探索）；`update(sig_family, arm, success, tokens)`（成功 α+1 否则 β+1）。
- `worker.py`：任务完成/熔断时按 signature 调 `update`。arm 初值：`["direct"]`（P4 后扩展 `["direct","precedent-assisted"]`）。
- **验收**：人为让某 arm 连续成功 5 次，`SELECT alpha,beta FROM routes` 后验正确偏移。

### 5.3 先例库（冷路径回流）
- 新表 `precedents(sig, req_id, plan_json, assertions_ref, tokens, duration_ms, created_at)`。
- `worker.py`：任务 success 时入库（plan = 工具调用序列摘要）。
- `main.py` 新增 `GET /precedents/similar?content=...` 返回 Top3 相似先例（调 `signature.similarity`）。
- **验收**：完成一个任务后，用相似文本查询能召回它。

### 5.4 弃权机制
- `worker.py`：提交带 `req_id` 的任务开始时，查相似先例；最高 similarity < 0.2 → 写 span `layer="L", type="abstain_check", attributes={matched:false}`，任务标记走"冷路径"（仅日志标记，行为不变——P4 才接路由臂）。
- **验收**：全新类型任务的 trace 中存在 `abstain_check` span 且 `matched=false`。

---

## 6. Phase 4 — 进化闭环 v1：半自动（预估 2.5 天）

> ⛔ **闸门复查（MR-3）**：动手前先把两条前置硬条件的验收证据粘贴到本 Phase 的 evidence 文件开头——A 段 effect_diff 非空的 SQL 输出 + C 段 decomposition-report 真实生成。缺任何一条，回到对应 Phase 补完，本 Phase 禁止开始。

### 6.1 epoch 评测器
- 新建 `monitor/eval_loop.py`：对 `split=train` 全部需求依次 POST /task/submit（**body 用需求的 `task` 字段，禁止用 `ears_text`**）执行 → 全部完成后跑 `vlayer.verdict` → 计算 epoch loss（Σ加权失败 + 0.05×token/预算），输出 `.agent/reports/epoch-{N}.json` 与 markdown 摘要。
- 提供 `--limit N` 调试开关（只跑前 N 条需求）。**注意：正式 epoch 会真实消耗 DeepSeek API token，这是设计本意；调试用 `--limit 1` 先验证链路。**
- **验收**：`python monitor/eval_loop.py --epoch 1 --limit 1` 产出完整报告，含该需求的 loss 明细与 epoch-1.json。

### 6.2 影子实例与灰度
- 新建 `scripts/shadow.sh {start|stop} {branch}`：git worktree 检出到 `.agent/worktrees/shadow`，端口 8002 起 uvicorn；PID 写入 `.agent/pidmap.json`；stop 前校验 pidmap 状态（防自杀三重校验的简化版：只杀 pidmap 里自己登记的 PID）。
- **已知缺陷修复（上次实测翻车点，必须改掉）**：
  1. **PID 采集错误**：uvicorn 启动存在 re-exec/子进程，`$!` 拿到的父 PID（如 90860）与实际监听进程（90862）不一致。启动后必须用 `ss -tlnp | grep :8002` 反查**真实监听 PID** 写入 pidmap，禁止直接信任 `$!`。
  2. **健康检查竞态**：上次日志显示 `Application startup complete` 正常但脚本报 health check failed——curl 打得太早。改为**等待循环**：每 1s curl 一次 `localhost:8002/`，最多 30 次，超时才算失败；判定成功后再写 pidmap。
- **验收**：start 后 `curl localhost:8002/` 正常且 pidmap 中的 PID 与 `ss -tlnp | grep :8002` 显示的 PID **一致**（粘贴两条输出对比）；stop 后 `ss -tlnp | grep 8002` 为空，8000 不受影响。

### 6.3 更新器（数据更新包，不动代码）
- 新建 `monitor/updater.py`：读 epoch 报告中 loss>0 的需求 → 调现有 `diagnosis.shapley_diagnosis` 归因 → 产出 `.agent/proposals/epoch-{N}-proposal.json`：
```json
{"type": "threshold_patch | precedent_update | prompt_hint",
 "target": "monitor/guard.py:timeout_s | precedents#REQ-003 | SYSTEM_PROMPT",
 "evidence": ["trace_id..."], "suggested_value": ..., "confidence": 0.0}
```
- **v1 铁律：本文件只生成提案，由人工审阅后手动应用**（代码修改一律人工执行并单独 commit，message 尾部 `Epoch: N | Loss-Before: X | Loss-After: 待回填`）。

### 6.4 双门 merge + 早停
- 新建 `scripts/epoch_gate.py`：输入两个 epoch 报告 → 判据「train loss 降 ≥5% 且 dev 集无 PASS→FAIL 退化」→ 输出 MERGE/REJECT 结论；连续 3 epoch 不改善 → 生成《收敛报告》（loss 曲线、Shapley 层均值、残留失败模式）。
- **验收**：手工构造两份报告（一升一退），MERGE/REJECT 判定正确。

---

## 7. 总验收清单（全部通过 = 本阶段完工）

| # | 项 | 命令/检查 |
|---|---|---|
| 0 | **元规则** | `.agent/evidence/` 下 P0–P4 每份证据文件齐全，每条验收命令输出为原文粘贴且可重放 |
| 1 | P0 冒烟 | py_compile 全绿；重启后 /tasks 数据在 |
| 2 | 尺子 | 故意失败需求 → V 层 span + loss>0；进度曲线数据可查 |
| 3 | A 段观测 | effect_diff 非空且三键齐全；feedback_injected/feedback_response 存在；shell span 含 exit_code |
| 4 | 刹车 | 死循环任务第 3 次重复即 `g_halted`；`rm -rf` 被拦截 |
| 5 | B/C 段观测 | plan span 存在；E 层 span 含 plan_node_id；decomposition-report.md 真实生成 |
| 6 | 记忆 | 相似任务可召回先例；路由后验随结果偏移 |
| 7 | 弃权 | 新型任务 trace 含 `abstain_check{matched:false}` |
| 8 | 进化 | epoch 报告产出；影子实例 8002 启停不碰 8000 且 pidmap PID 与监听 PID 一致；双门判据正确 |
| 9 | 回归 | P0 前的老功能（提交任务、/metrics、monitor 日志、前端）全部正常 |

## 8. 时间与人力

| Phase | 预估 | 卡点 |
|---|---|---|
| P-1 | 0.5 天（人工） | **注入 DEEPSEEK_API_KEY + 冒烟任务真实跑通，否则一切免谈** |
| P0 | 1 天 | family_stats 结论决定 P3 深度 |
| P1 | 2 天 | **8 条需求的人工编写是唯一不可压缩项** |
| P2 | 2.5 天 | 含 A 段观测（4.0 前置阻断项）+ shell 白名单按 v2.2 重写（解析层是新工作量） |
| P3 | 3 天 | 含 B/C 段观测 + 极简线性规划器（5.0.0）；签名相似度阈值需实测微调 |
| P4 | 2.5 天 | **开始前复查 MR-3 两条硬条件**；提案首轮回填 loss 需完整跑两个 epoch（真实 API 成本） |
| — | +0.5 天 | v2.1 一次性事项：删 convergence.md 无源数据、P0–P3 补跑证据、REQ task 字段入库 |
| 合计 | **约 12 个工作日** | 评审指出 11 天偏乐观已采纳：真实 API 执行时间不可压缩 |

## 9. 明确不做（本期）

技能编译固化（热路径零 LLM）、视觉测试 agent、多臂并发 A/B、NL2EARS 对接、多服务器。对应接口（`precedents`、`routes.arm`、`JudgeVerdict.form`）已预留，后续阶段直接扩展不返工。
