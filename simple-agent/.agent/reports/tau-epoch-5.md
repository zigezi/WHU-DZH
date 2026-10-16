# Epoch 5 评测报告

- 生成时间：2026-09-16T13:26:53.153279
- train loss：33.0

## 分桶（口径：混合/分桶三行并列）

| bucket | n | pass | pass_rate | avg_tokens |
|---|---|---|---|---|
| state-changing | 106 | 76 | 0.717 | 80492 |
| read-only | 29 | 26 | 0.8966 | 50152 |

## 明细

| req_id | split | bucket | status | assertion_loss | loss | tokens | failed |
|---|---|---|---|---|---|---|---|
| TAU-A-000 | train | state-changing | success | 0.0 | 0.0 | 61715 | - |
| TAU-A-002 | train | state-changing | success | 1.0 | 1.0 | 164252 | - |
| TAU-A-003 | train | state-changing | success | 1.0 | 1.0 | 94664 | db_final_state |
| TAU-A-005 | train | state-changing | success | 0.0 | 0.0 | 60302 | - |
| TAU-A-006 | train | state-changing | success | 1.0 | 1.0 | 58263 | db_final_state |
| TAU-A-007 | train | state-changing | success | 0.0 | 0.0 | 60164 | - |
| TAU-A-008 | train | state-changing | success | 1.0 | 1.0 | 102371 | actions_match |
| TAU-A-009 | train | state-changing | success | 1.0 | 1.0 | 78242 | actions_match |
| TAU-A-012 | train | read-only | success | 0.0 | 0.0 | 31587 | - |
| TAU-A-013 | train | read-only | success | 0.0 | 0.0 | 24103 | - |
| TAU-A-014 | train | state-changing | success | 0.0 | 0.0 | 54156 | - |
| TAU-A-015 | train | read-only | success | 0.0 | 0.0 | 60706 | - |
| TAU-A-016 | train | state-changing | success | 0.0 | 0.0 | 38704 | - |
| TAU-A-017 | train | read-only | success | 1.0 | 1.0 | 105490 | db_final_state |
| TAU-A-018 | train | read-only | success | 0.0 | 0.0 | 28679 | - |
| TAU-A-019 | train | state-changing | success | 1.0 | 1.0 | 59491 | db_final_state |
| TAU-A-020 | train | state-changing | success | 0.0 | 0.0 | 44723 | - |
| TAU-A-021 | train | read-only | success | 0.0 | 0.0 | 29693 | - |
| TAU-A-022 | train | state-changing | success | 0.0 | 0.0 | 32051 | - |
| TAU-A-023 | train | state-changing | success | 0.0 | 0.0 | 103872 | - |
| TAU-A-024 | train | read-only | success | 0.0 | 0.0 | 61936 | - |
| TAU-A-025 | train | state-changing | success | 0.0 | 0.0 | 31525 | - |
| TAU-A-026 | train | state-changing | success | 0.0 | 0.0 | 70969 | - |
| TAU-A-027 | train | state-changing | success | 0.0 | 0.0 | 29135 | - |
| TAU-A-028 | train | state-changing | success | 1.0 | 1.0 | 46593 | db_final_state |
| TAU-A-029 | train | read-only | success | 0.0 | 0.0 | 40618 | - |
| TAU-A-030 | train | state-changing | success | 0.0 | 0.0 | 51290 | - |
| TAU-A-033 | train | state-changing | success | 1.0 | 1.0 | 148024 | db_final_state |
| TAU-A-035 | train | read-only | success | 0.0 | 0.0 | 40662 | - |
| TAU-A-036 | train | read-only | success | 0.0 | 0.0 | 66336 | - |
| TAU-A-037 | train | read-only | success | 0.0 | 0.0 | 46895 | - |
| TAU-A-039 | train | read-only | success | 0.0 | 0.0 | 42898 | - |
| TAU-A-040 | train | read-only | success | 1.0 | 1.0 | 46730 | db_final_state |
| TAU-A-042 | train | read-only | success | 0.0 | 0.0 | 31450 | - |
| TAU-A-043 | train | state-changing | success | 0.0 | 0.0 | 34140 | - |
| TAU-A-044 | train | read-only | success | 0.0 | 0.0 | 23068 | - |
| TAU-A-045 | train | state-changing | success | 1.0 | 1.0 | 41589 | db_final_state |
| TAU-A-046 | train | state-changing | success | 1.0 | 1.0 | 45069 | db_final_state |
| TAU-A-047 | train | read-only | success | 0.0 | 0.0 | 45697 | - |
| TAU-A-048 | train | read-only | success | 0.0 | 0.0 | 22540 | - |
| TAU-A-049 | train | read-only | success | 0.0 | 0.0 | 26785 | - |
| TAU-R-000 | train | state-changing | success | 0.0 | 0.0 | 62920 | - |
| TAU-R-002 | train | state-changing | success | 0.0 | 0.0 | 64364 | - |
| TAU-R-003 | train | state-changing | success | 0.0 | 0.0 | 66657 | - |
| TAU-R-004 | train | state-changing | success | 0.0 | 0.0 | 83269 | - |
| TAU-R-005 | train | state-changing | success | 0.0 | 0.0 | 106317 | - |
| TAU-R-006 | train | state-changing | success | 1.0 | 1.0 | 75161 | db_final_state |
| TAU-R-010 | train | read-only | success | 0.0 | 0.0 | 31410 | - |
| TAU-R-011 | train | state-changing | success | 0.0 | 0.0 | 50219 | - |
| TAU-R-012 | train | read-only | success | 0.0 | 0.0 | 49668 | - |
| TAU-R-013 | train | state-changing | success | 0.0 | 0.0 | 45489 | - |
| TAU-R-016 | train | state-changing | success | 0.0 | 0.0 | 93454 | - |
| TAU-R-017 | train | state-changing | success | 0.0 | 0.0 | 39840 | - |
| TAU-R-019 | train | state-changing | success | 0.0 | 0.0 | 50443 | - |
| TAU-R-020 | train | state-changing | success | 1.0 | 1.0 | 72741 | db_final_state |
| TAU-R-021 | train | state-changing | success | 0.0 | 0.0 | 78211 | - |
| TAU-R-022 | train | state-changing | success | 0.0 | 0.0 | 65913 | - |
| TAU-R-023 | train | state-changing | success | 0.0 | 0.0 | 133760 | - |
| TAU-R-024 | train | read-only | success | 0.0 | 0.0 | 41483 | - |
| TAU-R-025 | train | read-only | success | 0.0 | 0.0 | 44938 | - |
| TAU-R-026 | train | state-changing | success | 0.0 | 0.0 | 45843 | - |
| TAU-R-027 | train | state-changing | success | 0.0 | 0.0 | 69736 | - |
| TAU-R-028 | train | state-changing | success | 0.0 | 0.0 | 101205 | - |
| TAU-R-029 | train | state-changing | success | 1.0 | 1.0 | 84629 | - |
| TAU-R-030 | train | state-changing | success | 0.0 | 0.0 | 118705 | - |
| TAU-R-031 | train | state-changing | success | 1.0 | 1.0 | 93805 | actions_match |
| TAU-R-032 | train | state-changing | success | 0.0 | 0.0 | 109535 | - |
| TAU-R-033 | train | state-changing | success | 0.0 | 0.0 | 98782 | - |
| TAU-R-034 | train | state-changing | success | 1.0 | 1.0 | 59678 | actions_match |
| TAU-R-035 | train | state-changing | success | 0.0 | 0.0 | 93709 | - |
| TAU-R-036 | train | state-changing | success | 0.0 | 0.0 | 88961 | - |
| TAU-R-038 | train | state-changing | success | 1.0 | 1.0 | 84916 | - |
| TAU-R-039 | train | state-changing | success | 1.0 | 1.0 | 81325 | - |
| TAU-R-040 | train | state-changing | success | 0.0 | 0.0 | 50494 | - |
| TAU-R-041 | train | state-changing | success | 0.0 | 0.0 | 81253 | - |
| TAU-R-042 | train | state-changing | success | 0.0 | 0.0 | 105362 | - |
| TAU-R-043 | train | state-changing | success | 0.0 | 0.0 | 83622 | - |
| TAU-R-044 | train | state-changing | success | 0.0 | 0.0 | 88637 | - |
| TAU-R-045 | train | state-changing | success | 0.0 | 0.0 | 76998 | - |
| TAU-R-048 | train | state-changing | success | 0.0 | 0.0 | 57875 | - |
| TAU-R-049 | train | state-changing | success | 0.0 | 0.0 | 60397 | - |
| TAU-R-050 | train | read-only | success | 0.0 | 0.0 | 31828 | - |
| TAU-R-051 | train | state-changing | success | 0.0 | 0.0 | 64744 | - |
| TAU-R-052 | train | state-changing | success | 1.0 | 1.0 | 40388 | db_final_state |
| TAU-R-053 | train | state-changing | success | 0.0 | 0.0 | 52636 | - |
| TAU-R-055 | train | state-changing | success | 0.0 | 0.0 | 90500 | - |
| TAU-R-056 | train | state-changing | success | 0.0 | 0.0 | 73485 | - |
| TAU-R-057 | train | read-only | success | 0.0 | 0.0 | 41542 | - |
| TAU-R-058 | train | state-changing | success | 0.0 | 0.0 | 81571 | - |
| TAU-R-059 | train | state-changing | success | 1.0 | 1.0 | 37307 | - |
| TAU-R-060 | train | state-changing | success | 0.0 | 0.0 | 41432 | - |
| TAU-R-061 | train | state-changing | success | 0.0 | 0.0 | 39461 | - |
| TAU-R-062 | train | read-only | success | 1.0 | 1.0 | 76632 | - |
| TAU-R-063 | train | state-changing | success | 1.0 | 1.0 | 85284 | actions_match |
| TAU-R-064 | train | state-changing | success | 0.0 | 0.0 | 64177 | - |
| TAU-R-065 | train | read-only | success | 0.0 | 0.0 | 18713 | - |
| TAU-R-067 | train | read-only | success | 0.0 | 0.0 | 55719 | - |
| TAU-R-068 | train | read-only | success | 0.0 | 0.0 | 53135 | - |
| TAU-R-069 | train | state-changing | success | 0.0 | 0.0 | 47960 | - |
| TAU-R-070 | train | state-changing | success | 0.0 | 0.0 | 65088 | - |
| TAU-R-071 | train | state-changing | success | 1.0 | 1.0 | 95985 | db_final_state |
| TAU-R-072 | train | state-changing | success | 0.0 | 0.0 | 122955 | - |
| TAU-R-073 | train | state-changing | success | 0.0 | 0.0 | 41541 | - |
| TAU-R-074 | train | state-changing | success | 0.0 | 0.0 | 107860 | - |
| TAU-R-075 | train | state-changing | success | 0.0 | 0.0 | 63531 | - |
| TAU-R-076 | train | state-changing | success | 1.0 | 1.0 | 111430 | - |
| TAU-R-077 | train | state-changing | success | 0.0 | 0.0 | 46482 | - |
| TAU-R-079 | train | state-changing | success | 1.0 | 1.0 | 67078 | db_final_state |
| TAU-R-080 | train | state-changing | success | 0.0 | 0.0 | 83136 | - |
| TAU-R-081 | train | state-changing | success | 0.0 | 0.0 | 67638 | - |
| TAU-R-082 | train | state-changing | success | 0.0 | 0.0 | 58385 | - |
| TAU-R-083 | train | state-changing | success | 0.0 | 0.0 | 65149 | - |
| TAU-R-084 | train | state-changing | success | 0.0 | 0.0 | 52575 | - |
| TAU-R-087 | train | state-changing | success | 0.0 | 0.0 | 67839 | - |
| TAU-R-088 | train | state-changing | success | 1.0 | 1.0 | 55407 | db_final_state |
| TAU-R-091 | train | state-changing | success | 1.0 | 1.0 | 75588 | db_final_state |
| TAU-R-092 | train | state-changing | success | 0.0 | 0.0 | 57362 | - |
| TAU-R-093 | train | state-changing | success | 0.0 | 0.0 | 56411 | - |
| TAU-R-094 | train | state-changing | success | 0.0 | 0.0 | 54960 | - |
| TAU-R-096 | train | state-changing | success | 0.0 | 0.0 | 82643 | - |
| TAU-R-097 | train | state-changing | success | 0.0 | 0.0 | 125270 | - |
| TAU-R-098 | train | state-changing | success | 0.0 | 0.0 | 55711 | - |
| TAU-R-099 | train | state-changing | success | 1.0 | 1.0 | 93972 | db_final_state |
| TAU-R-100 | train | state-changing | success | 1.0 | 1.0 | 62435 | db_final_state |
| TAU-R-101 | train | state-changing | success | 1.0 | 1.0 | 92789 | db_final_state |
| TAU-R-102 | train | state-changing | success | 0.0 | 0.0 | 133561 | - |
| TAU-R-105 | train | state-changing | success | 1.0 | 1.0 | 141873 | actions_match |
| TAU-R-106 | train | read-only | success | 0.0 | 0.0 | 97280 | - |
| TAU-R-107 | train | state-changing | success | 0.0 | 0.0 | 75970 | - |
| TAU-R-108 | train | state-changing | success | 1.0 | 1.0 | 89255 | db_final_state |
| TAU-R-110 | train | state-changing | success | 0.0 | 0.0 | 108245 | - |
| TAU-R-111 | train | state-changing | success | 0.0 | 0.0 | 97030 | - |
| TAU-R-112 | train | state-changing | success | 0.0 | 0.0 | 69625 | - |
| TAU-R-113 | train | state-changing | success | 0.0 | 0.0 | 144459 | - |
| TAU-R-114 | train | state-changing | success | 0.0 | 0.0 | 41485 | - |

---

## epoch-5 复制实验读数（P5a.11 Part 2）

### 0. 三样本总览
| epoch | 通过率 | loss | state-changing | read-only |
|---|---|---|---|---|
| e3 (POLICY off) | 99/135 (73.3%) | 36.0 | 69.8% (74/106) | 86.2% (25/29) |
| e4 (POLICY v1) | 102/135 (75.6%) | 33.0 | 75.5% (80/106) | 75.9% (22/29) |
| e5 (POLICY v1 复跑) | 102/135 (75.6%) | 33.0 | **71.7% (76/106)** | 89.7% (26/29) |

### 1. 双门
- `e4 -> e5`：**REJECT**（improvement 0.0）——复制严格义下 loss 持平（33=33）、dev 无退化；gate 的 MERGE 判据是"提升≥5%"，纯复制天然不满足，故 REJECT 在此表示"无变化"，**非退化**。
- `e3 -> e5`：**MERGE**（improvement +8.33%，dev_ok=true）——on/off 对照成立。

### 2. FP-4 复跑（token 尾部，e4 -> e5）
- e4：p90=122,837 p99=174,967 max=206,782 >150k=5
- e5：p90=116,085 p99=168,574 max=176,676 >150k=4 → **尾部继续收窄** ✅

### 3. 同族 token Δ（e5 - e4，同任务）
- n=135：mean **−2,089**、median −197 → 相对 e4 略降。

### 4. arm_value_delta（第三个样本点）
| epoch | direct | precedent-assisted |
|---|---|---|
| e3 | 71.2% / 71,606 | 75.4% / 81,576 |
| e4 | 81.5% / 70,557 | 70.0% / 81,177 |
| e5 | 76.8% / 75,320 | 74.2% / 72,569 |
- 三样本里 direct 赢 2 次；**臂差异属噪声，precedent 注入无稳定收益**。

### 5. cache hit_ratio（首对可比读数）
- e4：hit=8,760,446 / miss=568,827 → **93.9%**
- e5：hit=8,469,886 / miss=548,607 → **93.9%** → **持平**，POLICY 前缀被稳定缓存覆盖。

### 6. 成本
- e5 总 token = 9,986,663（e4 10,268,621），在 ¥50/日护栏内。

## 预注册判读
- epoch-5 state-changing = **71.7% ∈ [70%, 80%]** → 按 P5a.11 预注册规则：**效应复制成功，POLICY v1 坐实为确认资产**。
- 注意与 Part 1 的张力：Part 1 指纹 FP-1/FP-2/FP-5 弱或数据不足，故"**效应可复制**"成立，但"**归因到具体规则**"仍开放（预注册亦明确不做消融）。
