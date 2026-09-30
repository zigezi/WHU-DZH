# Epoch 7 评测报告

- 生成时间：2026-09-29T18:49:58.505259
- train loss：38.0

## 分桶（口径：混合/分桶三行并列）

| bucket | n | pass | pass_rate | avg_tokens |
|---|---|---|---|---|
| state-changing | 106 | 73 | 0.6887 | 81741 |
| read-only | 29 | 24 | 0.8276 | 51976 |

## 明细

| req_id | split | bucket | status | assertion_loss | loss | tokens | failed |
|---|---|---|---|---|---|---|---|
| TAU-A-000 | train | state-changing | success | 1.0 | 1.0 | 67828 | db_final_state |
| TAU-A-002 | train | state-changing | success | 0.0 | 0.0 | 83929 | - |
| TAU-A-003 | train | state-changing | success | 1.0 | 1.0 | 160962 | db_final_state |
| TAU-A-005 | train | state-changing | success | 0.0 | 0.0 | 35751 | - |
| TAU-A-006 | train | state-changing | success | 0.0 | 0.0 | 78038 | - |
| TAU-A-007 | train | state-changing | success | 0.0 | 0.0 | 101861 | - |
| TAU-A-008 | train | state-changing | success | 1.0 | 1.0 | 153754 | db_final_state, actions_match |
| TAU-A-009 | train | state-changing | success | 1.0 | 1.0 | 124884 | db_final_state, actions_match |
| TAU-A-012 | train | read-only | success | 0.0 | 0.0 | 29739 | - |
| TAU-A-013 | train | read-only | success | 0.0 | 0.0 | 33785 | - |
| TAU-A-014 | train | state-changing | success | 1.0 | 1.0 | 30488 | db_final_state |
| TAU-A-015 | train | read-only | success | 1.0 | 1.0 | 59568 | db_final_state |
| TAU-A-016 | train | state-changing | success | 0.0 | 0.0 | 39817 | - |
| TAU-A-017 | train | read-only | success | 0.0 | 0.0 | 96861 | - |
| TAU-A-018 | train | read-only | success | 0.0 | 0.0 | 24638 | - |
| TAU-A-019 | train | state-changing | success | 1.0 | 1.0 | 49349 | db_final_state |
| TAU-A-020 | train | state-changing | success | 0.0 | 0.0 | 51083 | - |
| TAU-A-021 | train | read-only | success | 1.0 | 1.0 | 55855 | db_final_state |
| TAU-A-022 | train | state-changing | success | 0.0 | 0.0 | 56970 | - |
| TAU-A-023 | train | state-changing | success | 0.0 | 0.0 | 92347 | - |
| TAU-A-024 | train | read-only | success | 0.0 | 0.0 | 83868 | - |
| TAU-A-025 | train | state-changing | success | 0.0 | 0.0 | 30594 | - |
| TAU-A-026 | train | state-changing | success | 1.0 | 1.0 | 56640 | db_final_state |
| TAU-A-027 | train | state-changing | success | 1.0 | 1.0 | 40518 | db_final_state |
| TAU-A-028 | train | state-changing | success | 1.0 | 1.0 | 57767 | db_final_state |
| TAU-A-029 | train | read-only | success | 0.0 | 0.0 | 36306 | - |
| TAU-A-030 | train | state-changing | success | 1.0 | 1.0 | 51088 | db_final_state |
| TAU-A-033 | train | state-changing | success | 1.0 | 1.0 | 97009 | db_final_state |
| TAU-A-035 | train | read-only | success | 0.0 | 0.0 | 30924 | - |
| TAU-A-036 | train | read-only | success | 0.0 | 0.0 | 42097 | - |
| TAU-A-037 | train | read-only | success | 1.0 | 1.0 | 124340 | db_final_state |
| TAU-A-039 | train | read-only | success | 0.0 | 0.0 | 29085 | - |
| TAU-A-040 | train | read-only | success | 0.0 | 0.0 | 52097 | - |
| TAU-A-042 | train | read-only | success | 0.0 | 0.0 | 34427 | - |
| TAU-A-043 | train | state-changing | success | 0.0 | 0.0 | 31438 | - |
| TAU-A-044 | train | read-only | success | 0.0 | 0.0 | 23070 | - |
| TAU-A-045 | train | state-changing | success | 1.0 | 1.0 | 49052 | db_final_state |
| TAU-A-046 | train | state-changing | success | 1.0 | 1.0 | 51768 | db_final_state |
| TAU-A-047 | train | read-only | success | 1.0 | 1.0 | 54173 | db_final_state |
| TAU-A-048 | train | read-only | success | 0.0 | 0.0 | 23558 | - |
| TAU-A-049 | train | read-only | success | 0.0 | 0.0 | 24612 | - |
| TAU-R-000 | train | state-changing | success | 0.0 | 0.0 | 60988 | - |
| TAU-R-002 | train | state-changing | success | 0.0 | 0.0 | 81780 | - |
| TAU-R-003 | train | state-changing | success | 0.0 | 0.0 | 67180 | - |
| TAU-R-004 | train | state-changing | success | 0.0 | 0.0 | 63321 | - |
| TAU-R-005 | train | state-changing | success | 0.0 | 0.0 | 75247 | - |
| TAU-R-006 | train | state-changing | success | 0.0 | 0.0 | 92326 | - |
| TAU-R-010 | train | read-only | success | 0.0 | 0.0 | 35899 | - |
| TAU-R-011 | train | state-changing | success | 0.0 | 0.0 | 51023 | - |
| TAU-R-012 | train | read-only | success | 0.0 | 0.0 | 46318 | - |
| TAU-R-013 | train | state-changing | success | 1.0 | 1.0 | 92124 | db_final_state |
| TAU-R-016 | train | state-changing | success | 0.0 | 0.0 | 64819 | - |
| TAU-R-017 | train | state-changing | success | 0.0 | 0.0 | 40328 | - |
| TAU-R-019 | train | state-changing | success | 0.0 | 0.0 | 45925 | - |
| TAU-R-020 | train | state-changing | success | 1.0 | 1.0 | 67652 | db_final_state |
| TAU-R-021 | train | state-changing | success | 0.0 | 0.0 | 81167 | - |
| TAU-R-022 | train | state-changing | success | 1.0 | 1.0 | 78829 | db_final_state |
| TAU-R-023 | train | state-changing | success | 1.0 | 1.0 | 141693 | db_final_state |
| TAU-R-024 | train | read-only | success | 0.0 | 0.0 | 36614 | - |
| TAU-R-025 | train | read-only | success | 0.0 | 0.0 | 45387 | - |
| TAU-R-026 | train | state-changing | success | 0.0 | 0.0 | 46941 | - |
| TAU-R-027 | train | state-changing | success | 0.0 | 0.0 | 80306 | - |
| TAU-R-028 | train | state-changing | success | 0.0 | 0.0 | 78776 | - |
| TAU-R-029 | train | state-changing | success | 0.0 | 0.0 | 93023 | - |
| TAU-R-030 | train | state-changing | success | 0.0 | 0.0 | 122394 | - |
| TAU-R-031 | train | state-changing | success | 0.0 | 0.0 | 93053 | - |
| TAU-R-032 | train | state-changing | success | 0.0 | 0.0 | 110631 | - |
| TAU-R-033 | train | state-changing | success | 0.0 | 0.0 | 55715 | - |
| TAU-R-034 | train | state-changing | success | 1.0 | 1.0 | 80585 | actions_match |
| TAU-R-035 | train | state-changing | success | 0.0 | 0.0 | 78248 | - |
| TAU-R-036 | train | state-changing | success | 0.0 | 0.0 | 80594 | - |
| TAU-R-038 | train | state-changing | success | 0.0 | 0.0 | 84319 | - |
| TAU-R-039 | train | state-changing | success | 1.0 | 1.0 | 40952 | db_final_state |
| TAU-R-040 | train | state-changing | success | 0.0 | 0.0 | 51187 | - |
| TAU-R-041 | train | state-changing | success | 0.0 | 0.0 | 71811 | - |
| TAU-R-042 | train | state-changing | success | 0.0 | 0.0 | 104842 | - |
| TAU-R-043 | train | state-changing | success | 0.0 | 0.0 | 51092 | - |
| TAU-R-044 | train | state-changing | success | 1.0 | 1.0 | 46664 | actions_match |
| TAU-R-045 | train | state-changing | success | 0.0 | 0.0 | 64584 | - |
| TAU-R-048 | train | state-changing | success | 0.0 | 0.0 | 68785 | - |
| TAU-R-049 | train | state-changing | success | 1.0 | 1.0 | 74665 | db_final_state |
| TAU-R-050 | train | read-only | success | 0.0 | 0.0 | 40179 | - |
| TAU-R-051 | train | state-changing | success | 0.0 | 0.0 | 50597 | - |
| TAU-R-052 | train | state-changing | success | 0.0 | 0.0 | 58308 | - |
| TAU-R-053 | train | state-changing | success | 0.0 | 0.0 | 55972 | - |
| TAU-R-055 | train | state-changing | success | 0.0 | 0.0 | 130894 | - |
| TAU-R-056 | train | state-changing | success | 0.0 | 0.0 | 72498 | - |
| TAU-R-057 | train | read-only | success | 0.0 | 0.0 | 35260 | - |
| TAU-R-058 | train | state-changing | success | 0.0 | 0.0 | 101287 | - |
| TAU-R-059 | train | state-changing | success | 1.0 | 1.0 | 97418 | db_final_state |
| TAU-R-060 | train | state-changing | success | 0.0 | 0.0 | 39434 | - |
| TAU-R-061 | train | state-changing | success | 0.0 | 0.0 | 40668 | - |
| TAU-R-062 | train | read-only | success | 0.0 | 0.0 | 49344 | - |
| TAU-R-063 | train | state-changing | success | 0.0 | 0.0 | 90953 | - |
| TAU-R-064 | train | state-changing | success | 1.0 | 1.0 | 76322 | db_final_state |
| TAU-R-065 | train | read-only | success | 0.0 | 0.0 | 29502 | - |
| TAU-R-067 | train | read-only | success | 0.0 | 0.0 | 57518 | - |
| TAU-R-068 | train | read-only | success | 0.0 | 0.0 | 56481 | - |
| TAU-R-069 | train | state-changing | success | 0.0 | 0.0 | 42922 | - |
| TAU-R-070 | train | state-changing | success | 0.0 | 0.0 | 72477 | - |
| TAU-R-071 | train | state-changing | success | 0.0 | 0.0 | 94801 | - |
| TAU-R-072 | train | state-changing | success | 0.0 | 0.0 | 113029 | - |
| TAU-R-073 | train | state-changing | success | 0.0 | 0.0 | 49854 | - |
| TAU-R-074 | train | state-changing | success | 0.0 | 0.0 | 106652 | - |
| TAU-R-075 | train | state-changing | success | 1.0 | 1.0 | 62753 | db_final_state |
| TAU-R-076 | train | state-changing | success | 0.0 | 0.0 | 68857 | - |
| TAU-R-077 | train | state-changing | success | 0.0 | 0.0 | 51370 | - |
| TAU-R-079 | train | state-changing | success | 0.0 | 0.0 | 62500 | - |
| TAU-R-080 | train | state-changing | success | 0.0 | 0.0 | 57161 | - |
| TAU-R-081 | train | state-changing | success | 0.0 | 0.0 | 59686 | - |
| TAU-R-082 | train | state-changing | success | 0.0 | 0.0 | 71514 | - |
| TAU-R-083 | train | state-changing | success | 0.0 | 0.0 | 55403 | - |
| TAU-R-084 | train | state-changing | success | 0.0 | 0.0 | 55344 | - |
| TAU-R-087 | train | state-changing | success | 0.0 | 0.0 | 75906 | - |
| TAU-R-088 | train | state-changing | success | 0.0 | 0.0 | 50751 | - |
| TAU-R-091 | train | state-changing | success | 1.0 | 1.0 | 80718 | db_final_state |
| TAU-R-092 | train | state-changing | success | 0.0 | 0.0 | 50489 | - |
| TAU-R-093 | train | state-changing | success | 0.0 | 0.0 | 87705 | - |
| TAU-R-094 | train | state-changing | success | 0.0 | 0.0 | 66242 | - |
| TAU-R-096 | train | state-changing | success | 0.0 | 0.0 | 85530 | - |
| TAU-R-097 | train | state-changing | success | 0.0 | 0.0 | 77113 | - |
| TAU-R-098 | train | state-changing | success | 1.0 | 1.0 | 95531 | db_final_state |
| TAU-R-099 | train | state-changing | success | 1.0 | 1.0 | 79377 | db_final_state |
| TAU-R-100 | train | state-changing | success | 0.0 | 0.0 | 84022 | - |
| TAU-R-101 | train | state-changing | success | 1.0 | 1.0 | 120692 | db_final_state |
| TAU-R-102 | train | state-changing | success | 1.0 | 1.0 | 142718 | db_final_state |
| TAU-R-105 | train | state-changing | success | 1.0 | 1.0 | 173877 | db_final_state |
| TAU-R-106 | train | read-only | success | 1.0 | 1.0 | 86262 | db_final_state |
| TAU-R-107 | train | state-changing | success | 1.0 | 1.0 | 57030 | db_final_state |
| TAU-R-108 | train | state-changing | success | 1.0 | 1.0 | 106366 | db_final_state |
| TAU-R-110 | train | state-changing | success | 0.0 | 0.0 | 86538 | - |
| TAU-R-111 | train | state-changing | success | 1.0 | 1.0 | 83633 | db_final_state |
| TAU-R-112 | train | state-changing | success | 0.0 | 0.0 | 109195 | - |
| TAU-R-113 | train | state-changing | success | 0.0 | 0.0 | 141124 | - |
| TAU-R-114 | train | state-changing | success | 0.0 | 0.0 | 62165 | - |
