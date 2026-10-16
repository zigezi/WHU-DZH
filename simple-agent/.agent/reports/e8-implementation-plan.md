# e8 实施计划 v2（code-mapped，规格以 P5a.30–33 终版 v4 为准）

**基线代码**：`precedent_select.select`（同族最早 id）、`routing.choose_measurement(task_id, arms)`（blake2b % len）、
`worker._inject_precedent`（读 `precedent_snapshots`）、`trace_store`、`requirements/tau/*.json`（tau_env/sig/tau_task_id）。

## 相对 v1 的 4 处修改（a33）

| # | v1 | v2（a33 终裁） |
|---|---|---|
| 1 | 脱敏用 `ZZZ` 通用命名空间 | **类型前缀伪真值**：`RES_0x1A2B`、`FLT_0x3C4D`、`ORD_`/`USR_`/`PAY_`/`NAME_`…（类型在 token 层可见） |
| 2 | 日期"保序假日期" | **全体日期加同一固定偏移**（保先后/差值/相对今日；"保留月份随机日"被驳回=关系毒药） |
| 3 | 映射表未规定作用域/密级 | 强制**注入物内共指一致**；全局表**须单射**；**本地未跟踪**存（`.agent/local/`，gitignore）；证据链只记**映射表哈希**；生成用**带种子确定性 RNG**，种子入证据 |
| 4 | 均衡只有形态平衡表 | **臂分配永远纯随机**（再分配机制**驳回**）；k=3 只作用于**臂内注入物选择**；冻结时打印**量化达标线**：top-1 覆盖率 ≤15% ∧ distinct ≥20 ∧ 同域覆盖 ≥60%，**不达标不开工（回报不自改）**；CopyGuard 改**全参数扫描**（所有字符串参数 × 注入物实体全集，归一化） |

## 工作项（A–G，零 token）

**A. 伪真值脱敏库** — 新 `deident.py` + `scripts/e8_build_deident.py`
- 类型锚点 `RES_/FLT_/ORD_/USR_/PAY_/NAME_` + `_0x` hex；日期=**单一固定偏移**；金额保序保量级；姓名保留名单。
- 注入物内共指一致（同原值→同假值）+ 关系保持；全局表单射（可选）。
- **映射表 → `.agent/local/`（未跟踪）**；`seed` 与 `mapping_sha256` 入证据；lint **三检**（无残余真值 ∧ JSON 合法 ∧ 假值 DB 非成员）。

**B. 三臂分配** — `worker` 臂块：`arms=["direct","sibling","unrelated"]`（`choose_measurement` 不改，只传 3 元列表）；**分配纯随机，不受任何配额/k 影响**。

**C. 臂内选择器** — 扩 `precedent_select.select_for_arm(candidates, *, task_sig, task_env, arm, rng, used, k=3)`：
- direct→None；sibling=同域同族→（空）同域近族→ineligible；unrelated=异族形态匹配；**k=3 仅臂内；池尽 → ineligible，不跨臂/跨域递补**。
- "同域近族"：GT 动作类型序列 Jaccard ≥0.6 ∧ 同 `tau_env`（预计算 `family_actiontypes`）。

**D. unrelated 形态匹配 + 平衡表**（并入 `e8_freeze.py`）：|len 差|≤2 ∧ 工具类型多重集近似；出两臂形态平衡表。

**E. 矩阵冻结 + 量化达标线** — 新 `scripts/e8_freeze.py`
- 冻结 `e8-matrix-freeze.json`：task×arm×injectant(content_hash)×reason×ineligible。
- 打印并断言：**top-1 ≤15% ∧ distinct ≥20 ∧ 同域 ≥60%**；不达标 → **回报仲裁，不改臂**（a33 §二 法定）。

**F. CopyGuard 审计版** — 新 `backend/monitor/copyguard.py`
- **全参数扫描**：agent 所有字符串参数 × 注入物实体全集，归一化（去 `#` 等）比对；豁免="该值已在本 run 先前工具结果出现"。
- 命中 → 审计旗标 + 隔离开案，**永不改结局**；伪真值下预期 0；e7 回放（真值）命中过豁免后即抄答案证据。

**G. 沙盒 shakedown + e7 全样本审计** — `scripts/e8_sandbox.py`、`scripts/e7_copyguard_audit.py`
- 机械清单：lint3 ∧ 矩阵可冻结+达标线 ∧ 平衡表 ∧ CopyGuard e7 回放 ∧ 10 任务烟跑无 crash。**拒绝"S 比例上升"作门**。

## 顺序
`A → B → C → D → E → F → G`；F 并行出 e7 全样本审计；Path B' 拦截器 → e9（不进 e8）。

## 需预裁 / 高风险
1. **达标线可能天然不达标**：a31 预测零售同域覆盖 <60%；且 distinct 注入物 e7 仅 **13**（门槛 ≥20）。→ 计划含"计算后回报"路径，不擅自放宽。
2. "同域近族" Jaccard 阈值 0.6 需用实际族距离分布校准。
3. 脱敏不改 reward（τ DB 哈希 + output 匹配），仅改注入文本——仪器不动。
