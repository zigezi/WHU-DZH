# P5a.11 — 机制指纹查询（先行）+ epoch-5 复制实验

> 目标命题：**命题一（效应存在性）**——POLICY v1 的 +5.7pp 是资产效应还是单 epoch 噪声。
> 顺序强制：先做 Part 1（零成本，用现有 spans），再烧 Part 2。

---

## Part 0：运维修复（顺手，不单独验收）

- 所有脚本固定显式解释器路径 `/root/miniconda3/envs/mini-agent/bin/python`（修掉 shell python 解析到 base conda 导致 backend 重启失败的问题）。

## Part 1：四条机制指纹查询（¥0，对 epoch-3 / epoch-4 现有 spans 跑）

> 原则：门读数只回答"有没有用"，指纹回答"是否通过规则宣称的机制起作用"。
> 每条：给出真实 SQL + 原始数字 + 归一化到每任务比率，贴入 `.agent/evidence/phase-P5a11-evidence.md`（MR-1）。
> schema 以实际为准自行适配，但禁止改数。

| 指纹 | 验证的规则 | 计算内容 | 期望方向（epoch-4 vs epoch-3） |
|---|---|---|---|
| FP-4 | P4 结束即止 | per-task 总 token 的 p90 / p99 / max；>150k token 的任务数 | 尾部收窄（对话爆炸减少） |
| FP-5 | P5 失败换策略 | guard 熔断/HALT 触发次数；同一工具连续失败 ≥3 次的片段数及其中自愈（未 HALT）占比 | HALT 次数下降；自愈占比上升 |
| FP-1 | P1 修正版 | 纯文本 RESPOND 轮（无 tool_call）总数；其中"确认型"（首个工具调用前的单独复述轮）数量；平均每任务轮数 | 确认型单独轮 ≈0；平均轮数不升 |
| FP-2 | P2 不臆造信息 | 失败任务中，工具参数值在对话历史与工具返回中均未出现过的调用数（字符串匹配启发式） | 占比下降 |

- FP-2 为启发式检测器，存在误报（模型合理推断格式），须附 3 条人工抽查样例说明。
- **判读规则（预注册，看到数据前定死）**：
  - 指纹齐 + 门绿 → 资产效应有机制支撑，沉积可信；
  - 指纹缺 + 门绿 → 效应可能来自别处（运气/环境漂移），资产标记"归因存疑"，不晋升；
  - 指纹齐 + 门红 → 规则机制起效但未转化为通过率，仍是有信息量的读数，如实报告。

## Part 2：epoch-5 复制实验（Part 1 报告交齐后启动）

**配置冻结（复制的全部价值在于零变量）**：

- 与 epoch-4 完全同构：`eval_loop.py --epoch 5 --tau-only --split train --tag tau-`；
- POLICY v1 冻结：evidence 中须证明 policy_id 仍为 `174e4c5dfd45`；
- 双臂不变（direct / precedent-assisted），dev 继续锁 direct；
- epoch-4 commit（482b629）到 epoch-5 开跑之间，`backend/` 不允许有任何代码 diff（Part 0 的脚本解释器修复除外，须单独 commit 并在证据中声明）；有任何 diff 则 epoch-5 作废重跑。

**双门跑两次**：

1. `epoch_gate.py tau-epoch-4.json tau-epoch-5.json` —— 复制严格义：期望是**无显著退化**，不是提升；
2. `epoch_gate.py tau-epoch-3.json tau-epoch-5.json` —— on/off 对照：epoch-3 是天然的 POLICY-off 样本。

**报告必含**：state-changing 通过率、read-only、arm_value_delta（第三个样本点）、cache hit_ratio（与 epoch-4 的 93.9% 是首对可比读数，期望持平）、同族 token Δ、成本（护栏 ¥50/日，预估 ¥20±5）。

**判读规则（预注册）**：

| epoch-5 state-changing | 结论 | 后续 |
|---|---|---|
| ∈ [70%, 80%] | 效应复制成功，POLICY v1 坐实为确认资产 | 解锁第 2 代资产生命周期（updater 消化 epoch-4+5 失败） |
| 回落至 ~69%（epoch-3 水位） | epoch-4 大概率为噪声；MERGE 判决保留但资产降级为"未确认" | **不做消融**，再跑一个同配置 epoch-6 攒第三样本 |
| > 80% 或异常低 | 检查环境漂移（模型版本、cache、sidecar），如实报告，不得选择性解释 | 视漂移源决定 |

## 明确不做（维持）

不做消融（理由见裁决记录：效应尺寸拆不开、规则零成本、复制优先）；不换模型（终局证明，等命题一二三坐实）；不动 guard 阈值与 reward 权重；不应用任何新提案；threshold_patch 类继续冻结；不引入新依赖。
