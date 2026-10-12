# Epoch 8 评测报告

- 生成时间：2026-10-10T20:03:52.423725
- train loss：34.0

## 分桶（口径：混合/分桶三行并列）

| bucket | n | pass | pass_rate | avg_tokens |
|---|---|---|---|---|
| state-changing | 106 | 76 | 0.717 | 83661 |
| read-only | 29 | 25 | 0.8621 | 49013 |

## 明细

| req_id | split | bucket | status | assertion_loss | loss | tokens | failed |
|---|---|---|---|---|---|---|---|
| TAU-A-000 | train | state-changing | success | 1.0 | 1.0 | 64043 | db_final_state |
| TAU-A-002 | train | state-changing | success | 1.0 | 1.0 | 130637 | db_final_state |
| TAU-A-003 | train | state-changing | success | 0.0 | 0.0 | 111423 | - |
| TAU-A-005 | train | state-changing | success | 0.0 | 0.0 | 71852 | - |
| TAU-A-006 | train | state-changing | success | 0.0 | 0.0 | 66948 | - |
| TAU-A-007 | train | state-changing | success | 0.0 | 0.0 | 139579 | - |
| TAU-A-008 | train | state-changing | success | 1.0 | 1.0 | 91244 | db_final_state, actions_match |
| TAU-A-009 | train | state-changing | success | 1.0 | 1.0 | 105206 | db_final_state |
| TAU-A-012 | train | read-only | success | 0.0 | 0.0 | 28006 | - |
| TAU-A-013 | train | read-only | success | 0.0 | 0.0 | 18563 | - |
| TAU-A-014 | train | state-changing | success | 0.0 | 0.0 | 57311 | - |
| TAU-A-015 | train | read-only | success | 1.0 | 1.0 | 67901 | db_final_state |
| TAU-A-016 | train | state-changing | success | 0.0 | 0.0 | 39509 | - |
| TAU-A-017 | train | read-only | success | 0.0 | 0.0 | 115325 | - |
| TAU-A-018 | train | read-only | success | 0.0 | 0.0 | 24579 | - |
| TAU-A-019 | train | state-changing | success | 1.0 | 1.0 | 139085 | db_final_state |
| TAU-A-020 | train | state-changing | success | 0.0 | 0.0 | 53722 | - |
| TAU-A-021 | train | read-only | success | 0.0 | 0.0 | 36939 | - |
| TAU-A-022 | train | state-changing | success | 1.0 | 1.0 | 75470 | db_final_state |
| TAU-A-023 | train | state-changing | success | 1.0 | 1.0 | 97868 | db_final_state |
| TAU-A-024 | train | read-only | success | 0.0 | 0.0 | 63143 | - |
| TAU-A-025 | train | state-changing | success | 0.0 | 0.0 | 38436 | - |
| TAU-A-026 | train | state-changing | success | 0.0 | 0.0 | 32997 | - |
| TAU-A-027 | train | state-changing | success | 0.0 | 0.0 | 29434 | - |
| TAU-A-028 | train | state-changing | success | 0.0 | 0.0 | 44370 | - |
| TAU-A-029 | train | read-only | success | 0.0 | 0.0 | 36046 | - |
| TAU-A-030 | train | state-changing | success | 0.0 | 0.0 | 56430 | - |
| TAU-A-033 | train | state-changing | success | 1.0 | 1.0 | 148410 | db_final_state |
| TAU-A-035 | train | read-only | success | 0.0 | 0.0 | 38958 | - |
| TAU-A-036 | train | read-only | success | 0.0 | 0.0 | 49070 | - |
| TAU-A-037 | train | read-only | success | 0.0 | 0.0 | 38582 | - |
| TAU-A-039 | train | read-only | success | 1.0 | 1.0 | 28616 | db_final_state |
| TAU-A-040 | train | read-only | success | 0.0 | 0.0 | 53004 | - |
| TAU-A-042 | train | read-only | success | 0.0 | 0.0 | 23544 | - |
| TAU-A-043 | train | state-changing | success | 0.0 | 0.0 | 26958 | - |
| TAU-A-044 | train | read-only | success | 0.0 | 0.0 | 18249 | - |
| TAU-A-045 | train | state-changing | success | 1.0 | 1.0 | 58639 | db_final_state |
| TAU-A-046 | train | state-changing | success | 1.0 | 1.0 | 60681 | db_final_state |
| TAU-A-047 | train | read-only | success | 0.0 | 0.0 | 35439 | - |
| TAU-A-048 | train | read-only | success | 1.0 | 1.0 | 54374 | db_final_state |
| TAU-A-049 | train | read-only | success | 0.0 | 0.0 | 25463 | - |
| TAU-R-000 | train | state-changing | success | 0.0 | 0.0 | 109710 | - |
| TAU-R-002 | train | state-changing | success | 0.0 | 0.0 | 80110 | - |
| TAU-R-003 | train | state-changing | success | 0.0 | 0.0 | 67209 | - |
| TAU-R-004 | train | state-changing | success | 0.0 | 0.0 | 77932 | - |
| TAU-R-005 | train | state-changing | success | 0.0 | 0.0 | 105818 | - |
| TAU-R-006 | train | state-changing | success | 0.0 | 0.0 | 70669 | - |
| TAU-R-010 | train | read-only | success | 0.0 | 0.0 | 42334 | - |
| TAU-R-011 | train | state-changing | success | 0.0 | 0.0 | 55749 | - |
| TAU-R-012 | train | read-only | success | 0.0 | 0.0 | 46931 | - |
| TAU-R-013 | train | state-changing | success | 0.0 | 0.0 | 51480 | - |
| TAU-R-016 | train | state-changing | success | 0.0 | 0.0 | 108866 | - |
| TAU-R-017 | train | state-changing | success | 0.0 | 0.0 | 43547 | - |
| TAU-R-019 | train | state-changing | success | 0.0 | 0.0 | 80101 | - |
| TAU-R-020 | train | state-changing | success | 1.0 | 1.0 | 86526 | db_final_state |
| TAU-R-021 | train | state-changing | success | 0.0 | 0.0 | 108646 | - |
| TAU-R-022 | train | state-changing | success | 1.0 | 1.0 | 67749 | db_final_state |
| TAU-R-023 | train | state-changing | success | 0.0 | 0.0 | 138987 | - |
| TAU-R-024 | train | read-only | success | 0.0 | 0.0 | 43336 | - |
| TAU-R-025 | train | read-only | success | 0.0 | 0.0 | 41127 | - |
| TAU-R-026 | train | state-changing | success | 0.0 | 0.0 | 75306 | - |
| TAU-R-027 | train | state-changing | success | 0.0 | 0.0 | 83851 | - |
| TAU-R-028 | train | state-changing | success | 0.0 | 0.0 | 92213 | - |
| TAU-R-029 | train | state-changing | success | 1.0 | 1.0 | 79875 | db_final_state |
| TAU-R-030 | train | state-changing | success | 0.0 | 0.0 | 118179 | - |
| TAU-R-031 | train | state-changing | success | 0.0 | 0.0 | 62983 | - |
| TAU-R-032 | train | state-changing | success | 0.0 | 0.0 | 102106 | - |
| TAU-R-033 | train | state-changing | success | 0.0 | 0.0 | 58643 | - |
| TAU-R-034 | train | state-changing | success | 1.0 | 1.0 | 57438 | actions_match |
| TAU-R-035 | train | state-changing | success | 0.0 | 0.0 | 96318 | - |
| TAU-R-036 | train | state-changing | success | 0.0 | 0.0 | 65715 | - |
| TAU-R-038 | train | state-changing | success | 0.0 | 0.0 | 92104 | - |
| TAU-R-039 | train | state-changing | success | 0.0 | 0.0 | 62901 | - |
| TAU-R-040 | train | state-changing | success | 0.0 | 0.0 | 50681 | - |
| TAU-R-041 | train | state-changing | success | 0.0 | 0.0 | 109215 | - |
| TAU-R-042 | train | state-changing | success | 0.0 | 0.0 | 118352 | - |
| TAU-R-043 | train | state-changing | success | 0.0 | 0.0 | 71140 | - |
| TAU-R-044 | train | state-changing | success | 0.0 | 0.0 | 56898 | - |
| TAU-R-045 | train | state-changing | success | 0.0 | 0.0 | 64974 | - |
| TAU-R-048 | train | state-changing | success | 0.0 | 0.0 | 59878 | - |
| TAU-R-049 | train | state-changing | success | 1.0 | 1.0 | 74467 | db_final_state |
| TAU-R-050 | train | read-only | success | 0.0 | 0.0 | 19323 | - |
| TAU-R-051 | train | state-changing | success | 0.0 | 0.0 | 62828 | - |
| TAU-R-052 | train | state-changing | success | 0.0 | 0.0 | 52556 | - |
| TAU-R-053 | train | state-changing | success | 0.0 | 0.0 | 56499 | - |
| TAU-R-055 | train | state-changing | success | 0.0 | 0.0 | 44585 | - |
| TAU-R-056 | train | state-changing | success | 0.0 | 0.0 | 73749 | - |
| TAU-R-057 | train | read-only | success | 0.0 | 0.0 | 40055 | - |
| TAU-R-058 | train | state-changing | success | 0.0 | 0.0 | 70291 | - |
| TAU-R-059 | train | state-changing | success | 1.0 | 1.0 | 85700 | db_final_state |
| TAU-R-060 | train | state-changing | success | 0.0 | 0.0 | 39882 | - |
| TAU-R-061 | train | state-changing | success | 0.0 | 0.0 | 42046 | - |
| TAU-R-062 | train | read-only | success | 0.0 | 0.0 | 57384 | - |
| TAU-R-063 | train | state-changing | success | 0.0 | 0.0 | 94878 | - |
| TAU-R-064 | train | state-changing | success | 1.0 | 1.0 | 58299 | db_final_state |
| TAU-R-065 | train | read-only | success | 0.0 | 0.0 | 44992 | - |
| TAU-R-067 | train | read-only | success | 0.0 | 0.0 | 75265 | - |
| TAU-R-068 | train | read-only | success | 0.0 | 0.0 | 50497 | - |
| TAU-R-069 | train | state-changing | success | 0.0 | 0.0 | 52303 | - |
| TAU-R-070 | train | state-changing | success | 0.0 | 0.0 | 56997 | - |
| TAU-R-071 | train | state-changing | success | 0.0 | 0.0 | 99088 | - |
| TAU-R-072 | train | state-changing | success | 1.0 | 1.0 | 93875 | db_final_state |
| TAU-R-073 | train | state-changing | success | 0.0 | 0.0 | 44505 | - |
| TAU-R-074 | train | state-changing | success | 1.0 | 1.0 | 92000 | db_final_state |
| TAU-R-075 | train | state-changing | success | 0.0 | 0.0 | 50873 | - |
| TAU-R-076 | train | state-changing | success | 0.0 | 0.0 | 80267 | - |
| TAU-R-077 | train | state-changing | success | 0.0 | 0.0 | 46918 | - |
| TAU-R-079 | train | state-changing | success | 1.0 | 1.0 | 72551 | db_final_state |
| TAU-R-080 | train | state-changing | success | 0.0 | 0.0 | 62273 | - |
| TAU-R-081 | train | state-changing | success | 0.0 | 0.0 | 55213 | - |
| TAU-R-082 | train | state-changing | success | 0.0 | 0.0 | 51580 | - |
| TAU-R-083 | train | state-changing | success | 0.0 | 0.0 | 60469 | - |
| TAU-R-084 | train | state-changing | success | 0.0 | 0.0 | 45592 | - |
| TAU-R-087 | train | state-changing | success | 0.0 | 0.0 | 48831 | - |
| TAU-R-088 | train | state-changing | success | 1.0 | 1.0 | 54040 | db_final_state |
| TAU-R-091 | train | state-changing | success | 1.0 | 1.0 | 81196 | db_final_state |
| TAU-R-092 | train | state-changing | success | 0.0 | 0.0 | 57734 | - |
| TAU-R-093 | train | state-changing | success | 0.0 | 0.0 | 56756 | - |
| TAU-R-094 | train | state-changing | success | 0.0 | 0.0 | 75478 | - |
| TAU-R-096 | train | state-changing | success | 0.0 | 0.0 | 95298 | - |
| TAU-R-097 | train | state-changing | success | 0.0 | 0.0 | 76423 | - |
| TAU-R-098 | train | state-changing | success | 1.0 | 1.0 | 65820 | db_final_state |
| TAU-R-099 | train | state-changing | success | 1.0 | 1.0 | 85092 | db_final_state |
| TAU-R-100 | train | state-changing | success | 1.0 | 1.0 | 138210 | db_final_state |
| TAU-R-101 | train | state-changing | success | 1.0 | 1.0 | 113689 | db_final_state |
| TAU-R-102 | train | state-changing | success | 0.0 | 0.0 | 145936 | - |
| TAU-R-105 | train | state-changing | success | 1.0 | 1.0 | 160402 | db_final_state, actions_match |
| TAU-R-106 | train | read-only | success | 1.0 | 1.0 | 79594 | db_final_state |
| TAU-R-107 | train | state-changing | success | 1.0 | 1.0 | 51552 | db_final_state |
| TAU-R-108 | train | state-changing | success | 1.0 | 1.0 | 143576 | db_final_state |
| TAU-R-110 | train | state-changing | success | 1.0 | 1.0 | 88973 | db_final_state |
| TAU-R-111 | train | state-changing | success | 0.0 | 0.0 | 101105 | - |
| TAU-R-112 | train | state-changing | success | 0.0 | 0.0 | 99857 | - |
| TAU-R-113 | train | state-changing | success | 0.0 | 0.0 | 120551 | - |
| TAU-R-114 | train | state-changing | success | 0.0 | 0.0 | 56228 | - |
