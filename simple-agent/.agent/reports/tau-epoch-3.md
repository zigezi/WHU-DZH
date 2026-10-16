# Epoch 3 评测报告

- 生成时间：2026-09-14T15:29:23.011697
- train loss：36.0

## 分桶（口径：混合/分桶三行并列）

| bucket | n | pass | pass_rate | avg_tokens |
|---|---|---|---|---|
| state-changing | 106 | 74 | 0.6981 | 81761 |
| read-only | 29 | 25 | 0.8621 | 58209 |

## 明细

| req_id | split | bucket | status | assertion_loss | loss | tokens | failed |
|---|---|---|---|---|---|---|---|
| TAU-A-000 | train | state-changing | success | 1.0 | 1.0 | 101106 | db_final_state |
| TAU-A-002 | train | state-changing | success | 1.0 | 1.0 | 195449 | - |
| TAU-A-003 | train | state-changing | success | 0.0 | 0.0 | 114393 | - |
| TAU-A-005 | train | state-changing | success | 0.0 | 0.0 | 56514 | - |
| TAU-A-006 | train | state-changing | success | 0.0 | 0.0 | 60295 | - |
| TAU-A-007 | train | state-changing | success | 1.0 | 1.0 | 86987 | db_final_state |
| TAU-A-008 | train | state-changing | success | 1.0 | 1.0 | 98419 | - |
| TAU-A-009 | train | state-changing | success | 1.0 | 1.0 | 176012 | actions_match |
| TAU-A-012 | train | read-only | success | 0.0 | 0.0 | 32233 | - |
| TAU-A-013 | train | read-only | success | 0.0 | 0.0 | 32053 | - |
| TAU-A-014 | train | state-changing | success | 1.0 | 1.0 | 29403 | db_final_state |
| TAU-A-015 | train | read-only | success | 1.0 | 1.0 | 69938 | db_final_state |
| TAU-A-016 | train | state-changing | success | 0.0 | 0.0 | 51752 | - |
| TAU-A-017 | train | read-only | success | 1.0 | 1.0 | 178178 | db_final_state |
| TAU-A-018 | train | read-only | success | 0.0 | 0.0 | 36787 | - |
| TAU-A-019 | train | state-changing | success | 1.0 | 1.0 | 39509 | db_final_state |
| TAU-A-020 | train | state-changing | success | 0.0 | 0.0 | 43574 | - |
| TAU-A-021 | train | read-only | success | 0.0 | 0.0 | 33617 | - |
| TAU-A-022 | train | state-changing | success | 1.0 | 1.0 | 59147 | db_final_state |
| TAU-A-023 | train | state-changing | success | 1.0 | 1.0 | 116490 | db_final_state |
| TAU-A-024 | train | read-only | success | 0.0 | 0.0 | 46829 | - |
| TAU-A-025 | train | state-changing | success | 0.0 | 0.0 | 30668 | - |
| TAU-A-026 | train | state-changing | success | 0.0 | 0.0 | 34349 | - |
| TAU-A-027 | train | state-changing | success | 0.0 | 0.0 | 27804 | - |
| TAU-A-028 | train | state-changing | success | 0.0 | 0.0 | 64784 | - |
| TAU-A-029 | train | read-only | success | 0.0 | 0.0 | 34166 | - |
| TAU-A-030 | train | state-changing | success | 0.0 | 0.0 | 59015 | - |
| TAU-A-033 | train | state-changing | success | 1.0 | 1.0 | 119076 | db_final_state |
| TAU-A-035 | train | read-only | success | 0.0 | 0.0 | 31922 | - |
| TAU-A-036 | train | read-only | success | 0.0 | 0.0 | 198602 | - |
| TAU-A-037 | train | read-only | success | 0.0 | 0.0 | 60241 | - |
| TAU-A-039 | train | read-only | success | 0.0 | 0.0 | 38477 | - |
| TAU-A-040 | train | read-only | success | 0.0 | 0.0 | 48483 | - |
| TAU-A-042 | train | read-only | success | 0.0 | 0.0 | 26469 | - |
| TAU-A-043 | train | state-changing | success | 0.0 | 0.0 | 26093 | - |
| TAU-A-044 | train | read-only | success | 0.0 | 0.0 | 31970 | - |
| TAU-A-045 | train | state-changing | success | 1.0 | 1.0 | 62014 | db_final_state |
| TAU-A-046 | train | state-changing | success | 1.0 | 1.0 | 48445 | db_final_state |
| TAU-A-047 | train | read-only | success | 1.0 | 1.0 | 40059 | db_final_state |
| TAU-A-048 | train | read-only | success | 0.0 | 0.0 | 23500 | - |
| TAU-A-049 | train | read-only | success | 0.0 | 0.0 | 28179 | - |
| TAU-R-000 | train | state-changing | success | 0.0 | 0.0 | 62017 | - |
| TAU-R-002 | train | state-changing | success | 0.0 | 0.0 | 68856 | - |
| TAU-R-003 | train | state-changing | success | 0.0 | 0.0 | 63722 | - |
| TAU-R-004 | train | state-changing | success | 0.0 | 0.0 | 86114 | - |
| TAU-R-005 | train | state-changing | success | 0.0 | 0.0 | 89827 | - |
| TAU-R-006 | train | state-changing | success | 0.0 | 0.0 | 82588 | - |
| TAU-R-010 | train | read-only | success | 0.0 | 0.0 | 40355 | - |
| TAU-R-011 | train | state-changing | success | 0.0 | 0.0 | 54182 | - |
| TAU-R-012 | train | read-only | success | 0.0 | 0.0 | 45986 | - |
| TAU-R-013 | train | state-changing | success | 1.0 | 1.0 | 55162 | db_final_state |
| TAU-R-016 | train | state-changing | success | 0.0 | 0.0 | 77776 | - |
| TAU-R-017 | train | state-changing | success | 0.0 | 0.0 | 42871 | - |
| TAU-R-019 | train | state-changing | success | 0.0 | 0.0 | 63703 | - |
| TAU-R-020 | train | state-changing | success | 1.0 | 1.0 | 61231 | db_final_state |
| TAU-R-021 | train | state-changing | success | 0.0 | 0.0 | 111674 | - |
| TAU-R-022 | train | state-changing | success | 1.0 | 1.0 | 93063 | db_final_state |
| TAU-R-023 | train | state-changing | success | 0.0 | 0.0 | 148739 | - |
| TAU-R-024 | train | read-only | success | 0.0 | 0.0 | 51560 | - |
| TAU-R-025 | train | read-only | success | 0.0 | 0.0 | 42403 | - |
| TAU-R-026 | train | state-changing | success | 0.0 | 0.0 | 52668 | - |
| TAU-R-027 | train | state-changing | success | 0.0 | 0.0 | 58163 | - |
| TAU-R-028 | train | state-changing | success | 0.0 | 0.0 | 69810 | - |
| TAU-R-029 | train | state-changing | success | 1.0 | 1.0 | 53300 | - |
| TAU-R-030 | train | state-changing | success | 0.0 | 0.0 | 146628 | - |
| TAU-R-031 | train | state-changing | success | 0.0 | 0.0 | 83825 | - |
| TAU-R-032 | train | state-changing | success | 0.0 | 0.0 | 116735 | - |
| TAU-R-033 | train | state-changing | success | 0.0 | 0.0 | 59793 | - |
| TAU-R-034 | train | state-changing | success | 0.0 | 0.0 | 81464 | - |
| TAU-R-035 | train | state-changing | success | 0.0 | 0.0 | 104210 | - |
| TAU-R-036 | train | state-changing | success | 0.0 | 0.0 | 82728 | - |
| TAU-R-038 | train | state-changing | success | 1.0 | 1.0 | 92663 | - |
| TAU-R-039 | train | state-changing | success | 1.0 | 1.0 | 72170 | - |
| TAU-R-040 | train | state-changing | success | 0.0 | 0.0 | 50701 | - |
| TAU-R-041 | train | state-changing | success | 0.0 | 0.0 | 74150 | - |
| TAU-R-042 | train | state-changing | success | 0.0 | 0.0 | 104549 | - |
| TAU-R-043 | train | state-changing | success | 0.0 | 0.0 | 74807 | - |
| TAU-R-044 | train | state-changing | success | 0.0 | 0.0 | 48048 | - |
| TAU-R-045 | train | state-changing | success | 0.0 | 0.0 | 65857 | - |
| TAU-R-048 | train | state-changing | success | 0.0 | 0.0 | 50740 | - |
| TAU-R-049 | train | state-changing | success | 1.0 | 1.0 | 64285 | db_final_state |
| TAU-R-050 | train | read-only | success | 0.0 | 0.0 | 29890 | - |
| TAU-R-051 | train | state-changing | success | 0.0 | 0.0 | 65084 | - |
| TAU-R-052 | train | state-changing | success | 1.0 | 1.0 | 80126 | db_final_state |
| TAU-R-053 | train | state-changing | success | 0.0 | 0.0 | 64445 | - |
| TAU-R-055 | train | state-changing | success | 0.0 | 0.0 | 79632 | - |
| TAU-R-056 | train | state-changing | success | 1.0 | 1.0 | 54361 | db_final_state |
| TAU-R-057 | train | read-only | success | 0.0 | 0.0 | 34812 | - |
| TAU-R-058 | train | state-changing | success | 0.0 | 0.0 | 73730 | - |
| TAU-R-059 | train | state-changing | success | 0.0 | 0.0 | 57237 | - |
| TAU-R-060 | train | state-changing | success | 0.0 | 0.0 | 41036 | - |
| TAU-R-061 | train | state-changing | success | 0.0 | 0.0 | 45708 | - |
| TAU-R-062 | train | read-only | success | 0.0 | 0.0 | 63603 | - |
| TAU-R-063 | train | state-changing | success | 0.0 | 0.0 | 65810 | - |
| TAU-R-064 | train | state-changing | success | 1.0 | 1.0 | 50049 | db_final_state |
| TAU-R-065 | train | read-only | success | 0.0 | 0.0 | 32889 | - |
| TAU-R-067 | train | read-only | success | 0.0 | 0.0 | 42907 | - |
| TAU-R-068 | train | read-only | success | 0.0 | 0.0 | 47267 | - |
| TAU-R-069 | train | state-changing | success | 0.0 | 0.0 | 41851 | - |
| TAU-R-070 | train | state-changing | success | 0.0 | 0.0 | 57139 | - |
| TAU-R-071 | train | state-changing | success | 0.0 | 0.0 | 117363 | - |
| TAU-R-072 | train | state-changing | success | 1.0 | 1.0 | 105306 | db_final_state |
| TAU-R-073 | train | state-changing | success | 0.0 | 0.0 | 40691 | - |
| TAU-R-074 | train | state-changing | success | 1.0 | 1.0 | 113416 | db_final_state |
| TAU-R-075 | train | state-changing | success | 0.0 | 0.0 | 56128 | - |
| TAU-R-076 | train | state-changing | success | 0.0 | 0.0 | 113438 | - |
| TAU-R-077 | train | state-changing | success | 0.0 | 0.0 | 43120 | - |
| TAU-R-079 | train | state-changing | success | 1.0 | 1.0 | 77700 | db_final_state |
| TAU-R-080 | train | state-changing | success | 0.0 | 0.0 | 58867 | - |
| TAU-R-081 | train | state-changing | success | 0.0 | 0.0 | 59531 | - |
| TAU-R-082 | train | state-changing | success | 0.0 | 0.0 | 58367 | - |
| TAU-R-083 | train | state-changing | success | 0.0 | 0.0 | 56060 | - |
| TAU-R-084 | train | state-changing | success | 0.0 | 0.0 | 55705 | - |
| TAU-R-087 | train | state-changing | success | 0.0 | 0.0 | 45680 | - |
| TAU-R-088 | train | state-changing | success | 1.0 | 1.0 | 49282 | db_final_state |
| TAU-R-091 | train | state-changing | success | 1.0 | 1.0 | 50762 | db_final_state |
| TAU-R-092 | train | state-changing | success | 0.0 | 0.0 | 52637 | - |
| TAU-R-093 | train | state-changing | success | 0.0 | 0.0 | 81317 | - |
| TAU-R-094 | train | state-changing | success | 0.0 | 0.0 | 56489 | - |
| TAU-R-096 | train | state-changing | success | 0.0 | 0.0 | 87422 | - |
| TAU-R-097 | train | state-changing | success | 0.0 | 0.0 | 79085 | - |
| TAU-R-098 | train | state-changing | success | 0.0 | 0.0 | 55053 | - |
| TAU-R-099 | train | state-changing | success | 1.0 | 1.0 | 103391 | db_final_state |
| TAU-R-100 | train | state-changing | success | 1.0 | 1.0 | 119163 | db_final_state |
| TAU-R-101 | train | state-changing | success | 0.0 | 0.0 | 100431 | - |
| TAU-R-102 | train | state-changing | success | 0.0 | 0.0 | 133044 | - |
| TAU-R-105 | train | state-changing | success | 1.0 | 1.0 | 167638 | - |
| TAU-R-106 | train | read-only | success | 1.0 | 1.0 | 72068 | db_final_state |
| TAU-R-107 | train | state-changing | success | 0.0 | 0.0 | 74556 | - |
| TAU-R-108 | train | state-changing | success | 1.0 | 1.0 | 102217 | db_final_state |
| TAU-R-110 | train | state-changing | success | 1.0 | 1.0 | 75635 | db_final_state |
| TAU-R-111 | train | state-changing | success | 0.0 | 0.0 | 41441 | - |
| TAU-R-112 | train | state-changing | success | 0.0 | 0.0 | 92492 | - |
| TAU-R-113 | train | state-changing | success | 0.0 | 0.0 | 168562 | - |
| TAU-R-114 | train | state-changing | success | 0.0 | 0.0 | 59525 | - |

---

## epoch-3 三读数（P5a.6）

### 1. 同族 token Δ（epoch-2 vs epoch-3，同任务）
- epoch-2 mean = 72,398 → epoch-3 mean = 76,702（n=135 共同任务）
- **mean Δ = +4,304 token（+5.9%），median Δ = +516** → **未下降，反而上升**
- 归因：precedent-assisted 臂注入了先例上下文（+约 10k token/任务），且两臂高方差，token 不降反升。

### 2. arm_value_delta（epoch-3，按 arm_choice 分组）
| arm | n | pass_rate | avg_tokens |
|---|---|---|---|
| direct | 66 | 71.2% | 71,606 |
| precedent-assisted | 69 | 75.4% | 81,576 |
- 先例辅助换来 **+4.2pp 成功率**，代价 **+9,970 token/任务**（允许 token 上升，看换来了什么）。

### 3. 分桶通过率（拆穿虚荣通过率）
| bucket | n | pass_rate | avg_tokens |
|---|---|---|---|
| state-changing | 106 | **69.8%** | 81,761 |
| read-only | 29 | 86.2% | 58,209 |
- read-only（86.2%）> state-changing（69.8%）→ 混合口径 73.3% 被纯查询任务抬高；
- **DeepSeek 真实水位 ≈ state-changing 69.8%**。

## 双门结论（epoch-2 → epoch-3）
```
{"decision": "REJECT", "improvement": -0.125, "train_ok": false, "dev_ok": true, "dev_regressions": []}
```
- train loss 32.0 → 36.0（恶化 12.5%）；本次无人工改动，唯一变量是补丁 1-3（测量修复 + 第二臂启用）。
- 解释：epoch-2 的 76.3% 是**单族塌缩 + 混合口径**下的虚高值；epoch-3 修好测量后回落到真实水位，且第二臂 token 上升，故 REJECT 属预期，非回退。
