# P5a.76 §二 建设段：E2 设施事实（opencode 侧输入，供注册段）

日期：2026-10-14
性质：E2「建设—注册—开门」三段令之**建设段事实清单**（§二.2 要求"opencode 补设施事实"）。
边界：**只报设施事实与缺口；不跑任何任务**（无 E 门不跑，§二.1）。

## 一、可逐字复用（已建成、已验证）

| 面 | 组件 | 位置 | 现状 |
|---|---|---|---|
| A 段观测 | `effect_diff`（created/modified/deleted） | `backend/tools/registry.py`、`monitor/guard.py`、`monitor/report.py` | 在役 |
| A 段观测 | `feedback_injected` / `feedback_response`（纠偏链路） | `monitor/guard.py`、`monitor/plan_observer.py` | 在役 |
| B/C 段观测 | `record_plan`（L 层 plan span）、`decomposition_report`（owns_conflicts/rework/token_cv…） | `monitor/plan_observer.py`、`monitor.py`、`worker.py`（plan_node_id） | 在役 |
| V 层尺子 | `run_assertions` / `verdict`（断言→loss、V verdict span） | `monitor/vlayer.py`；判决接口 `monitor/judges.py`（JudgeVerdict） | 在役 |
| 评测器 | epoch 评测（train 跑批 + dev 回归 → epoch-{N}.json/md） | `monitor/eval_loop.py` | 在役 |
| 多臂 harness | 随机化 / 矩阵冻结 / 形态对齐 / wild bootstrap / CopyGuard / 运行表 / ITT | `scripts/e8_freeze.py`、`e8_analysis.py`、`e7_copyguard_audit.py`、`harness_screen.py`；规格 `.agent/reports/e9-harness-spec.md` | 在役（域无关） |
| 域包 | `DomainPack` 注册表（tau 已落地；code 为 stub） | `backend/domains/__init__.py`、`domains/tau.py`、`domains/code.py` | tau 在役 / code stub |
| 生成器官 | 五环骨架 + 影子出生路径 + 宪法边界 | `monitor/organ.py` | 在役（自检 3/3） |
| 溯源 | `asset×validated_domain×credit_level×last_revalidated×evidence` | `monitor/provenance.py` | 在役（11 资产全 tau） |
| 金丝雀门 | v1.1 四门（含隐式语义故障） | `scripts/canary_gate_v11.py` | 在役（4/4 GREEN） |

设施自检：`e3_substrate_check.py` → `all_pass=true`（域包 tau/code 加载、11 资产登记、规则与拦截器一致）；`organ_selftest.py` → 3/3。

## 二、E2 专属缺口（建设段剩余、须三方输入）

1. **E2 域包**（对标 `domains/tau.py`）：`mutating_tools / transfer_tool / read_prefixes / entity_field_class / interceptor_rules / lock_scope_key`——**投标文件域**的实体类（如 标段号/投标人/报价项/资质字段）与写类工具须定义。**域事实待用户补**（§二.2）。
2. **任务集（最小 30–50，含长程多步）**：对标 R-105 类长程；来源与规模**待用户补**。
3. **评测器来源**：投标任务的"对/错"由谁/何器判（领域规则 or 人工金标准）——**待用户补**；评测器须在开门段冻结。
4. **E2 任务书（注册段，裁者起草）**：研究问题 / 基线设计 / 预算 / 成功判据。
5. 开门段预注册：任务集冻结、评测器冻结、分母、主指标、ITT。

## 三、建设段可即刻推进项（零 token，不跑任务）
- 校准/复核 A 段 `effect_diff` 与 `feedback_response` 的写入路径在长程下的完整性（静态 + 合成事件，非任务运行）；
- 起草 **E2 域包骨架** `backend/domains/<e2>.py`（占位实体类与写工具，待用户域事实填充）；
- 验证 harness 的 DomainPack 接口对 E2 的适配面（`e9-harness-spec.md` §域无关化清单）。

## 四、收割接管
本回合真实代码操作失败按 a66 回合末收割并入 `code_corpses`（零 token，不伪造）。当前尸体 7/30、4 类。
