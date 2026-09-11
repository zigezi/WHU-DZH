# simple-agent 判断力机制 · 执行方案（opencode 实施版）

> **实施者**：opencode 调用 DeepSeek-V4 ｜ **目标仓库**：https://github.com/zigezi/WHU-DZH 分支 `simple-agent`，本次只改 `simple-agent/` 子目录
> **运行环境**：单台 8G 内存 CPU 服务器，推理全走 DeepSeek API，本机只做编排与确定性执行
> **总原则**：确定性语义全部落代码；LLM 只做提案，不做控制；每 Phase 结束必须能独立验收。

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
5. 每 Phase 单独 git commit，commit message 带结构化尾部：`Phase: PX | Loss-Before: n/a | Gate: manual`。
6. 不改 NL2EARS/，不动 8000 端口现有对外 API 的返回字段（只做加法）。

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
 "title": "工具连续失败告警", "ears_text": "WHEN 同一工具连续失败2次, THE SYSTEM SHALL 记录T001异常并终止任务",
 "assertions": [{"name": "t001_fired", "cmd": "sqlite3 logs/trace.db \"SELECT 1 FROM spans WHERE layer='G' AND json_extract(attributes,'$.rule')='T001' LIMIT 1\" | grep -q 1", "severity": "blocker"}],
 "budget": {"max_steps": 10, "max_tokens": 30000, "timeout_s": 600}}
```
- `requirements/loader.py`：加载时校验——**无 assertions 的需求直接拒绝入库**（绑定率 100% 门禁）；`split` 只允许 train/dev。
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

## 4. Phase 2 — G 层：刹车（预估 1.5 天）

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
- **验收**：构造任务"反复读取不存在的文件"，第 3 次重复后任务以 `g_halted` 终止，总 token < 预算的 40%。

### 4.3 shell 工具白名单
- `tools/shell.py`：执行前过白名单（正则列表，默认放行只读命令与 `python/pytest/npm/git status/git diff` 等），显式 deny 全局约束第 4 条命令；拦截写 span `layer="G", type="permission_check"`。
- **验收**：任务里让 agent 执行 `rm -rf /`（构造注入测试），被拦截且有 G 层 span。

---

## 5. Phase 3 — 记忆与路由（预估 2 天）

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

### 6.1 epoch 评测器
- 新建 `monitor/eval_loop.py`：对 `split=train` 全部需求依次 POST /task/submit 执行 → 全部完成后跑 `vlayer.verdict` → 计算 epoch loss（Σ加权失败 + 0.05×token/预算），输出 `.agent/reports/epoch-{N}.json` 与 markdown 摘要。
- **验收**：`python monitor/eval_loop.py --epoch 1` 产出完整报告，含每条需求的 loss 明细。

### 6.2 影子实例与灰度
- 新建 `scripts/shadow.sh {start|stop} {branch}`：git worktree 检出到 `.agent/worktrees/shadow`，端口 8002 起 uvicorn；PID 写入 `.agent/pidmap.json`；stop 前校验 pidmap 状态（防自杀三重校验的简化版：只杀 pidmap 里自己登记的 PID）。
- **验收**：start 后 `curl localhost:8002/` 正常；stop 后 `ss -tlnp | grep 8002` 为空，8000 不受影响。

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
| 1 | P0 冒烟 | py_compile 全绿；重启后 /tasks 数据在 |
| 2 | 尺子 | 故意失败需求 → V 层 span + loss>0；进度曲线数据可查 |
| 3 | 刹车 | 死循环任务第 3 次重复即 `g_halted`；`rm -rf` 被拦截 |
| 4 | 记忆 | 相似任务可召回先例；路由后验随结果偏移 |
| 5 | 弃权 | 新型任务 trace 含 `abstain_check{matched:false}` |
| 6 | 进化 | epoch 报告产出；影子实例 8002 启停不碰 8000；双门判据正确 |
| 7 | 回归 | P0 前的老功能（提交任务、/metrics、monitor 日志、前端）全部正常 |

## 8. 时间与人力

| Phase | 预估 | 卡点 |
|---|---|---|
| P0 | 1 天 | family_stats 结论决定 P3 深度 |
| P1 | 2 天 | **8 条需求的人工编写是唯一不可压缩项** |
| P2 | 1.5 天 | — |
| P3 | 2 天 | 签名相似度阈值需实测微调 |
| P4 | 2.5 天 | 提案首轮回填 loss 需完整跑两个 epoch |
| 合计 | **约 9 个工作日** | — |

## 9. 明确不做（本期）

技能编译固化（热路径零 LLM）、视觉测试 agent、多臂并发 A/B、NL2EARS 对接、多服务器。对应接口（`precedents`、`routes.arm`、`JudgeVerdict.form`）已预留，后续阶段直接扩展不返工。
