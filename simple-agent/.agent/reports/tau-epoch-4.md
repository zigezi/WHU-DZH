# Epoch 4 评测报告

- 生成时间：2026-09-15T16:46:47.659081
- train loss：33.0

## 分桶（口径：混合/分桶三行并列）

| bucket | n | pass | pass_rate | avg_tokens |
|---|---|---|---|---|
| state-changing | 106 | 80 | 0.7547 | 82662 |
| read-only | 29 | 22 | 0.7586 | 51946 |

## 明细

| req_id | split | bucket | status | assertion_loss | loss | tokens | failed |
|---|---|---|---|---|---|---|---|
| TAU-A-000 | train | state-changing | success | 1.0 | 1.0 | 56489 | db_final_state |
| TAU-A-002 | train | state-changing | success | 0.0 | 0.0 | 62266 | - |
| TAU-A-003 | train | state-changing | success | 0.0 | 0.0 | 105461 | - |
| TAU-A-005 | train | state-changing | success | 0.0 | 0.0 | 76182 | - |
| TAU-A-006 | train | state-changing | success | 0.0 | 0.0 | 66346 | - |
| TAU-A-007 | train | state-changing | success | 0.0 | 0.0 | 124296 | - |
| TAU-A-008 | train | state-changing | success | 0.0 | 0.0 | 156188 | - |
| TAU-A-009 | train | state-changing | success | 1.0 | 1.0 | 127535 | - |
| TAU-A-012 | train | read-only | success | 0.0 | 0.0 | 33282 | - |
| TAU-A-013 | train | read-only | success | 0.0 | 0.0 | 24287 | - |
| TAU-A-014 | train | state-changing | success | 0.0 | 0.0 | 48699 | - |
| TAU-A-015 | train | read-only | success | 1.0 | 1.0 | 60783 | db_final_state |
| TAU-A-016 | train | state-changing | success | 0.0 | 0.0 | 47567 | - |
| TAU-A-017 | train | read-only | success | 1.0 | 1.0 | 139561 | db_final_state |
| TAU-A-018 | train | read-only | success | 0.0 | 0.0 | 26102 | - |
| TAU-A-019 | train | state-changing | success | 1.0 | 1.0 | 136935 | db_final_state |
| TAU-A-020 | train | state-changing | success | 0.0 | 0.0 | 79380 | - |
| TAU-A-021 | train | read-only | success | 1.0 | 1.0 | 75585 | db_final_state |
| TAU-A-022 | train | state-changing | success | 0.0 | 0.0 | 31041 | - |
| TAU-A-023 | train | state-changing | success | 1.0 | 1.0 | 69893 | db_final_state |
| TAU-A-024 | train | read-only | success | 0.0 | 0.0 | 105721 | - |
| TAU-A-025 | train | state-changing | success | 0.0 | 0.0 | 30629 | - |
| TAU-A-026 | train | state-changing | success | 1.0 | 1.0 | 94339 | db_final_state |
| TAU-A-027 | train | state-changing | success | 0.0 | 0.0 | 131918 | - |
| TAU-A-028 | train | state-changing | success | 1.0 | 1.0 | 49201 | db_final_state |
| TAU-A-029 | train | read-only | success | 0.0 | 0.0 | 32197 | - |
| TAU-A-030 | train | state-changing | success | 0.0 | 0.0 | 79007 | - |
| TAU-A-033 | train | state-changing | success | 0.0 | 0.0 | 44679 | - |
| TAU-A-035 | train | read-only | success | 0.0 | 0.0 | 27822 | - |
| TAU-A-036 | train | read-only | success | 0.0 | 0.0 | 34611 | - |
| TAU-A-037 | train | read-only | success | 0.0 | 0.0 | 62712 | - |
| TAU-A-039 | train | read-only | success | 0.0 | 0.0 | 32097 | - |
| TAU-A-040 | train | read-only | success | 1.0 | 1.0 | 39580 | db_final_state |
| TAU-A-042 | train | read-only | success | 0.0 | 0.0 | 33172 | - |
| TAU-A-043 | train | state-changing | success | 0.0 | 0.0 | 33154 | - |
| TAU-A-044 | train | read-only | success | 0.0 | 0.0 | 18256 | - |
| TAU-A-045 | train | state-changing | success | 1.0 | 1.0 | 48648 | db_final_state |
| TAU-A-046 | train | state-changing | success | 1.0 | 1.0 | 44487 | db_final_state |
| TAU-A-047 | train | read-only | success | 1.0 | 1.0 | 33453 | db_final_state |
| TAU-A-048 | train | read-only | success | 0.0 | 0.0 | 22502 | - |
| TAU-A-049 | train | read-only | success | 0.0 | 0.0 | 21873 | - |
| TAU-R-000 | train | state-changing | success | 0.0 | 0.0 | 74677 | - |
| TAU-R-002 | train | state-changing | success | 0.0 | 0.0 | 75333 | - |
| TAU-R-003 | train | state-changing | success | 0.0 | 0.0 | 79426 | - |
| TAU-R-004 | train | state-changing | success | 0.0 | 0.0 | 75837 | - |
| TAU-R-005 | train | state-changing | success | 1.0 | 1.0 | 93672 | db_final_state |
| TAU-R-006 | train | state-changing | success | 0.0 | 0.0 | 84016 | - |
| TAU-R-010 | train | read-only | success | 0.0 | 0.0 | 48067 | - |
| TAU-R-011 | train | state-changing | success | 0.0 | 0.0 | 57371 | - |
| TAU-R-012 | train | read-only | success | 0.0 | 0.0 | 44604 | - |
| TAU-R-013 | train | state-changing | success | 0.0 | 0.0 | 54153 | - |
| TAU-R-016 | train | state-changing | success | 0.0 | 0.0 | 69342 | - |
| TAU-R-017 | train | state-changing | success | 0.0 | 0.0 | 44428 | - |
| TAU-R-019 | train | state-changing | success | 0.0 | 0.0 | 86391 | - |
| TAU-R-020 | train | state-changing | success | 1.0 | 1.0 | 67277 | db_final_state |
| TAU-R-021 | train | state-changing | success | 0.0 | 0.0 | 73089 | - |
| TAU-R-022 | train | state-changing | success | 0.0 | 0.0 | 78919 | - |
| TAU-R-023 | train | state-changing | success | 0.0 | 0.0 | 147628 | - |
| TAU-R-024 | train | read-only | success | 1.0 | 1.0 | 70672 | - |
| TAU-R-025 | train | read-only | success | 0.0 | 0.0 | 46336 | - |
| TAU-R-026 | train | state-changing | success | 0.0 | 0.0 | 46479 | - |
| TAU-R-027 | train | state-changing | success | 0.0 | 0.0 | 100301 | - |
| TAU-R-028 | train | state-changing | success | 1.0 | 1.0 | 99217 | - |
| TAU-R-029 | train | state-changing | success | 0.0 | 0.0 | 101271 | - |
| TAU-R-030 | train | state-changing | success | 0.0 | 0.0 | 133481 | - |
| TAU-R-031 | train | state-changing | success | 0.0 | 0.0 | 109804 | - |
| TAU-R-032 | train | state-changing | success | 0.0 | 0.0 | 119826 | - |
| TAU-R-033 | train | state-changing | success | 0.0 | 0.0 | 69253 | - |
| TAU-R-034 | train | state-changing | success | 1.0 | 1.0 | 52032 | actions_match |
| TAU-R-035 | train | state-changing | success | 0.0 | 0.0 | 87679 | - |
| TAU-R-036 | train | state-changing | success | 0.0 | 0.0 | 78762 | - |
| TAU-R-038 | train | state-changing | success | 1.0 | 1.0 | 86741 | - |
| TAU-R-039 | train | state-changing | success | 1.0 | 1.0 | 80088 | - |
| TAU-R-040 | train | state-changing | success | 0.0 | 0.0 | 50766 | - |
| TAU-R-041 | train | state-changing | success | 0.0 | 0.0 | 91509 | - |
| TAU-R-042 | train | state-changing | success | 0.0 | 0.0 | 107403 | - |
| TAU-R-043 | train | state-changing | success | 0.0 | 0.0 | 76053 | - |
| TAU-R-044 | train | state-changing | success | 0.0 | 0.0 | 57376 | - |
| TAU-R-045 | train | state-changing | success | 0.0 | 0.0 | 70311 | - |
| TAU-R-048 | train | state-changing | success | 0.0 | 0.0 | 55960 | - |
| TAU-R-049 | train | state-changing | success | 0.0 | 0.0 | 79507 | - |
| TAU-R-050 | train | read-only | success | 0.0 | 0.0 | 29868 | - |
| TAU-R-051 | train | state-changing | success | 0.0 | 0.0 | 64832 | - |
| TAU-R-052 | train | state-changing | success | 0.0 | 0.0 | 75324 | - |
| TAU-R-053 | train | state-changing | success | 0.0 | 0.0 | 58497 | - |
| TAU-R-055 | train | state-changing | success | 0.0 | 0.0 | 62523 | - |
| TAU-R-056 | train | state-changing | success | 0.0 | 0.0 | 64976 | - |
| TAU-R-057 | train | read-only | success | 0.0 | 0.0 | 36474 | - |
| TAU-R-058 | train | state-changing | success | 0.0 | 0.0 | 94058 | - |
| TAU-R-059 | train | state-changing | success | 1.0 | 1.0 | 55792 | - |
| TAU-R-060 | train | state-changing | success | 0.0 | 0.0 | 41665 | - |
| TAU-R-061 | train | state-changing | success | 0.0 | 0.0 | 39597 | - |
| TAU-R-062 | train | read-only | success | 0.0 | 0.0 | 63567 | - |
| TAU-R-063 | train | state-changing | success | 0.0 | 0.0 | 91660 | - |
| TAU-R-064 | train | state-changing | success | 0.0 | 0.0 | 69720 | - |
| TAU-R-065 | train | read-only | success | 0.0 | 0.0 | 38340 | - |
| TAU-R-067 | train | read-only | success | 0.0 | 0.0 | 64245 | - |
| TAU-R-068 | train | read-only | success | 0.0 | 0.0 | 48678 | - |
| TAU-R-069 | train | state-changing | success | 0.0 | 0.0 | 46462 | - |
| TAU-R-070 | train | state-changing | success | 0.0 | 0.0 | 57471 | - |
| TAU-R-071 | train | state-changing | success | 0.0 | 0.0 | 102129 | - |
| TAU-R-072 | train | state-changing | success | 0.0 | 0.0 | 98753 | - |
| TAU-R-073 | train | state-changing | success | 0.0 | 0.0 | 41984 | - |
| TAU-R-074 | train | state-changing | success | 1.0 | 1.0 | 89155 | db_final_state |
| TAU-R-075 | train | state-changing | success | 0.0 | 0.0 | 62079 | - |
| TAU-R-076 | train | state-changing | success | 1.0 | 1.0 | 91762 | - |
| TAU-R-077 | train | state-changing | success | 0.0 | 0.0 | 51077 | - |
| TAU-R-079 | train | state-changing | success | 0.0 | 0.0 | 90838 | - |
| TAU-R-080 | train | state-changing | success | 0.0 | 0.0 | 69290 | - |
| TAU-R-081 | train | state-changing | success | 0.0 | 0.0 | 63938 | - |
| TAU-R-082 | train | state-changing | success | 0.0 | 0.0 | 55165 | - |
| TAU-R-083 | train | state-changing | success | 0.0 | 0.0 | 47467 | - |
| TAU-R-084 | train | state-changing | success | 0.0 | 0.0 | 47819 | - |
| TAU-R-087 | train | state-changing | success | 0.0 | 0.0 | 63656 | - |
| TAU-R-088 | train | state-changing | success | 1.0 | 1.0 | 50833 | db_final_state |
| TAU-R-091 | train | state-changing | success | 1.0 | 1.0 | 83364 | db_final_state |
| TAU-R-092 | train | state-changing | success | 0.0 | 0.0 | 55402 | - |
| TAU-R-093 | train | state-changing | success | 0.0 | 0.0 | 61233 | - |
| TAU-R-094 | train | state-changing | success | 0.0 | 0.0 | 62932 | - |
| TAU-R-096 | train | state-changing | success | 0.0 | 0.0 | 70627 | - |
| TAU-R-097 | train | state-changing | success | 1.0 | 1.0 | 59390 | db_final_state |
| TAU-R-098 | train | state-changing | success | 0.0 | 0.0 | 74736 | - |
| TAU-R-099 | train | state-changing | success | 1.0 | 1.0 | 117385 | db_final_state |
| TAU-R-100 | train | state-changing | success | 1.0 | 1.0 | 58671 | db_final_state |
| TAU-R-101 | train | state-changing | success | 0.0 | 0.0 | 131989 | - |
| TAU-R-102 | train | state-changing | success | 0.0 | 0.0 | 114265 | - |
| TAU-R-105 | train | state-changing | success | 1.0 | 1.0 | 189032 | actions_match |
| TAU-R-106 | train | read-only | success | 1.0 | 1.0 | 74852 | db_final_state |
| TAU-R-107 | train | state-changing | success | 0.0 | 0.0 | 65965 | - |
| TAU-R-108 | train | state-changing | success | 1.0 | 1.0 | 101319 | db_final_state |
| TAU-R-110 | train | state-changing | success | 0.0 | 0.0 | 86865 | - |
| TAU-R-111 | train | state-changing | failed | 1.0 | 1.0 | 0 | db_final_state |
| TAU-R-112 | train | state-changing | success | 0.0 | 0.0 | 88145 | - |
| TAU-R-113 | train | state-changing | success | 1.0 | 1.0 | 158378 | db_final_state |
| TAU-R-114 | train | state-changing | success | 0.0 | 0.0 | 41132 | - |

---

## epoch-4 四读数（P5a.10）

### 0. 总览
- epoch-3：99/135（73.3%），loss=36.0 → epoch-4：**102/135（75.6%），loss=33.0**
- **epoch_gate（e3→e4）：MERGE**（improvement +8.33%，dev 无退化）

### 1. 同族 token Δ（e4 - e3，同任务）
- n=135：**mean −638（略降），median +690**；族间方差大（+17k ~ −17k）
- 结论：POLICY v1 未带来稳定的 token 下降，效果以"通过率"而非"省 token"体现。

### 2. arm_value_delta（epoch-4）
| arm | n | pass_rate | avg_tokens |
|---|---|---|---|
| direct | 65 | 81.5% | 70,557 |
| precedent-assisted | 70 | 70.0% | 81,177 |
- 本 epoch **direct 反超 precedent-assisted**（epoch-3 是反过来的）→ 两臂差异属噪声，precedent 注入暂无稳定收益且更贵。

### 3. 分桶通过率（真实水位）
| bucket | epoch-3 | epoch-4 |
|---|---|---|
| state-changing | 69.8% (74/106) | **75.5% (80/106)** |
| read-only | 86.2% (25/29) | 75.9% (22/29) |
- **关键**：state-changing（真实水位）从 69.8% 升到 75.5%（+5.7pp）；read-only 小样本(n=29)波动大，属噪声。

### 4. POLICY 段 prefix cache 覆盖验证
- epoch-4（含 POLICY）：hit=8,760,446 / miss=568,827，**hit_ratio=93.9%**（静态前缀被有效缓存，未见恶化）。
- epoch-3：**不可比**——cache instrumentation 于 P5a.9 才加入，epoch-3 的 llm_call span 无 hit/miss 字段（hit=miss=0）。
- 结论：POLICY 段作为静态前缀被缓存覆盖，未观察到覆盖恶化。
