# E 门审查材料 v2（P5a.30–42；R1/R2 整改后）

> 用途：E 门复审。R1 形态再匹配 + R2 台账已补；R3 为 e8 并行附件。

## 1. 冻结矩阵与达标线
- seed=`e8-20260929` k=3 near_jaccard=0.6  **matrix_hash=`85fef79fe57a6f28`**

| 达标线 | 值 | 阈值 | 结果 |
|---|---|---|---|
| top-1 覆盖率 | 0.034 | ≤0.15 | OK |
| distinct | 55 | ≥20 | OK |
| 同域覆盖率 | 0.956 | ≥0.60 | OK |
| **R1 形态** bin_gap=1.5pp / end_gap=1.0pp / mean_gap=0.3 | ≤10/≤10/≤1.0 | OK |
| **all_pass** | True | — | OK |

## 2. R1 形态再匹配（两臂对齐后）
- 仅重抽 unrelated 臂；变更任务 **44** 条；任务↔臂分配未动。

| 维度 | sibling | unrelated |
|---|---|---|
| n | 43 | 44 |
| mean len | 7.9 | 7.6 |
| len_bin_pct | {'b3(11+)': 23.3, 'b1(4-6)': 32.6, 'b2(7-10)': 34.9, 'b0(1-3)': 9.3} | {'b2(7-10)': 36.4, 'b1(4-6)': 31.8, 'b3(11+)': 22.7, 'b0(1-3)': 9.1} |
| end_class_pct | {'state_change_end': 58.1, 'transfer_end': 30.2, 'query_end': 11.6} | {'state_change_end': 59.1, 'transfer_end': 29.5, 'query_end': 11.4} |

## 3. R2 分母台账（逐级可对账）
| 数字 | 值 | 快照/口径 |
|---|---|---|
| 快照 e7 原始行 | 705 | precedent_snapshots WHERE epoch=7（含非 τ） |
| 非 PASS 剔除行 | 185 | 源 run verdict≠PASS（P5a.40 D3） |
| τ 工具候选（去重前） | 491 | tau__ 工具计划行 |
| 合格候选（去重后） | 306 | 源 run=PASS ∧ 去重(deid_hash) |
| 使用 distinct 注入物 | 55 | 冻结矩阵内 |
| 矩阵行 | 135 | 135 任务 |
| 臂 | {'direct': 46, 'sibling': 45, 'unrelated': 44} | — |
| ineligible | 2 | {'sibling': 2, 'unrelated': 0}（k=3 耗尽/降级链终止） |

**组成分析口径**：任务集按 GT 动作；注入池按 (req,plan) 对——全池 {'query_end': 82, 'state_change_end': 259, 'transfer_end': 109}（450 对），PASS-only {'state_change_end': 151, 'transfer_end': 97, 'query_end': 52}（300 对）。distinct 计划数=443（含 1 条 τ 工具但非 TAU- 前缀）。

**ITT**：ITT：ineligible 任务按所分臂进入分析（assigned=analyzed），剔除会致脱落偏倚
**not_in_static_dict=122 成分**：被替换的、不在静态 DB dump 的实体值（运行中派生/修改的地址、email、订单/支付等），noninformational 不判 FAIL；机器④(文档内可解释性) 已独立通过。

## 4. R3 提取保真（并行，不挡门）
- 138 例：方向 {'plan<run(truncation)': 69, 'plan>run(expansion)': 69}；epoch 分布 {'3': 66, '6': 72}（集中在 e3/e6）。
- 性质：计划来源=run 事后抽取；69 扩张(plan>run) 不可能来自忠实抽取 → 疑溯源/计数口径缺陷，挂 B-3，随 e8 判读同呈。

## 5. 骨架组成（P5a.41）
- 任务集：SC 108 / RO 18 / refusal 9
- PASS-only 池 state_change_end 占比 50.3%；transfer_end 97 条

## 6. 脱敏库机检
- all_pass=True proof_fails=0 not_in_static_dict=122(informational)

## 7. 待签
- 复核 R1/R2 通过 → 签 e8 运行令（三臂；主终点 Δ2=sibling−unrelated 簇 wild bootstrap；Δ2 须附骨架分解）。