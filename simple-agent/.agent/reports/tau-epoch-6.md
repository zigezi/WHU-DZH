# Epoch 6 评测报告

- 生成时间：2026-09-29T14:27:28.591956
- train loss：42.0

## 分桶（口径：混合/分桶三行并列）

| bucket | n | pass | pass_rate | avg_tokens |
|---|---|---|---|---|
| state-changing | 106 | 70 | 0.6604 | 79803 |
| read-only | 29 | 23 | 0.7931 | 58596 |

## 明细

| req_id | split | bucket | status | assertion_loss | loss | tokens | failed |
|---|---|---|---|---|---|---|---|
| TAU-A-000 | train | state-changing | success | 1.0 | 1.0 | 74981 | db_final_state |
| TAU-A-002 | train | state-changing | success | 0.0 | 0.0 | 68628 | - |
| TAU-A-003 | train | state-changing | success | 0.0 | 0.0 | 118384 | - |
| TAU-A-005 | train | state-changing | success | 0.0 | 0.0 | 70676 | - |
| TAU-A-006 | train | state-changing | success | 0.0 | 0.0 | 43266 | - |
| TAU-A-007 | train | state-changing | success | 0.0 | 0.0 | 95984 | - |
| TAU-A-008 | train | state-changing | success | 1.0 | 1.0 | 77551 | db_final_state |
| TAU-A-009 | train | state-changing | success | 1.0 | 1.0 | 95324 | db_final_state |
| TAU-A-012 | train | read-only | success | 0.0 | 0.0 | 28906 | - |
| TAU-A-013 | train | read-only | success | 0.0 | 0.0 | 27314 | - |
| TAU-A-014 | train | state-changing | success | 0.0 | 0.0 | 54875 | - |
| TAU-A-015 | train | read-only | success | 1.0 | 1.0 | 76443 | db_final_state |
| TAU-A-016 | train | state-changing | success | 0.0 | 0.0 | 61979 | - |
| TAU-A-017 | train | read-only | success | 1.0 | 1.0 | 144553 | db_final_state |
| TAU-A-018 | train | read-only | success | 0.0 | 0.0 | 22054 | - |
| TAU-A-019 | train | state-changing | success | 1.0 | 1.0 | 46144 | db_final_state |
| TAU-A-020 | train | state-changing | success | 0.0 | 0.0 | 57374 | - |
| TAU-A-021 | train | read-only | success | 1.0 | 1.0 | 76868 | db_final_state |
| TAU-A-022 | train | state-changing | success | 1.0 | 1.0 | 88561 | db_final_state |
| TAU-A-023 | train | state-changing | success | 1.0 | 1.0 | 74815 | db_final_state |
| TAU-A-024 | train | read-only | success | 0.0 | 0.0 | 92980 | - |
| TAU-A-025 | train | state-changing | success | 1.0 | 1.0 | 87560 | db_final_state |
| TAU-A-026 | train | state-changing | success | 0.0 | 0.0 | 29280 | - |
| TAU-A-027 | train | state-changing | success | 0.0 | 0.0 | 62079 | - |
| TAU-A-028 | train | state-changing | success | 1.0 | 1.0 | 50729 | db_final_state |
| TAU-A-029 | train | read-only | success | 0.0 | 0.0 | 32982 | - |
| TAU-A-030 | train | state-changing | success | 1.0 | 1.0 | 58668 | db_final_state |
| TAU-A-033 | train | state-changing | success | 0.0 | 0.0 | 32127 | - |
| TAU-A-035 | train | read-only | success | 0.0 | 0.0 | 32623 | - |
| TAU-A-036 | train | read-only | success | 0.0 | 0.0 | 142730 | - |
| TAU-A-037 | train | read-only | success | 1.0 | 1.0 | 69368 | db_final_state |
| TAU-A-039 | train | read-only | success | 0.0 | 0.0 | 31561 | - |
| TAU-A-040 | train | read-only | success | 0.0 | 0.0 | 38910 | - |
| TAU-A-042 | train | read-only | success | 0.0 | 0.0 | 27679 | - |
| TAU-A-043 | train | state-changing | success | 0.0 | 0.0 | 26898 | - |
| TAU-A-044 | train | read-only | success | 0.0 | 0.0 | 23170 | - |
| TAU-A-045 | train | state-changing | success | 1.0 | 1.0 | 59034 | db_final_state |
| TAU-A-046 | train | state-changing | success | 1.0 | 1.0 | 34926 | db_final_state |
| TAU-A-047 | train | read-only | success | 1.0 | 1.0 | 67952 | db_final_state |
| TAU-A-048 | train | read-only | success | 0.0 | 0.0 | 28797 | - |
| TAU-A-049 | train | read-only | success | 0.0 | 0.0 | 27656 | - |
| TAU-R-000 | train | state-changing | success | 0.0 | 0.0 | 47514 | - |
| TAU-R-002 | train | state-changing | success | 1.0 | 1.0 | 81504 | actions_match |
| TAU-R-003 | train | state-changing | success | 0.0 | 0.0 | 63970 | - |
| TAU-R-004 | train | state-changing | success | 0.0 | 0.0 | 75955 | - |
| TAU-R-005 | train | state-changing | success | 0.0 | 0.0 | 88759 | - |
| TAU-R-006 | train | state-changing | success | 1.0 | 1.0 | 65512 | db_final_state |
| TAU-R-010 | train | read-only | success | 0.0 | 0.0 | 42229 | - |
| TAU-R-011 | train | state-changing | success | 0.0 | 0.0 | 61883 | - |
| TAU-R-012 | train | read-only | success | 0.0 | 0.0 | 41775 | - |
| TAU-R-013 | train | state-changing | success | 0.0 | 0.0 | 48767 | - |
| TAU-R-016 | train | state-changing | success | 0.0 | 0.0 | 78438 | - |
| TAU-R-017 | train | state-changing | success | 0.0 | 0.0 | 44416 | - |
| TAU-R-019 | train | state-changing | success | 1.0 | 1.0 | 67514 | actions_match |
| TAU-R-020 | train | state-changing | success | 1.0 | 1.0 | 72968 | db_final_state |
| TAU-R-021 | train | state-changing | success | 0.0 | 0.0 | 70540 | - |
| TAU-R-022 | train | state-changing | success | 1.0 | 1.0 | 81527 | db_final_state |
| TAU-R-023 | train | state-changing | success | 0.0 | 0.0 | 114809 | - |
| TAU-R-024 | train | read-only | success | 0.0 | 0.0 | 31542 | - |
| TAU-R-025 | train | read-only | success | 0.0 | 0.0 | 44476 | - |
| TAU-R-026 | train | state-changing | success | 0.0 | 0.0 | 55827 | - |
| TAU-R-027 | train | state-changing | success | 0.0 | 0.0 | 77927 | - |
| TAU-R-028 | train | state-changing | success | 1.0 | 1.0 | 82465 | db_final_state, actions_match |
| TAU-R-029 | train | state-changing | success | 1.0 | 1.0 | 40673 | db_final_state |
| TAU-R-030 | train | state-changing | success | 0.0 | 0.0 | 113694 | - |
| TAU-R-031 | train | state-changing | success | 0.0 | 0.0 | 88375 | - |
| TAU-R-032 | train | state-changing | success | 0.0 | 0.0 | 95612 | - |
| TAU-R-033 | train | state-changing | success | 0.0 | 0.0 | 69504 | - |
| TAU-R-034 | train | state-changing | success | 1.0 | 1.0 | 64464 | actions_match |
| TAU-R-035 | train | state-changing | success | 0.0 | 0.0 | 98852 | - |
| TAU-R-036 | train | state-changing | success | 0.0 | 0.0 | 70027 | - |
| TAU-R-038 | train | state-changing | success | 1.0 | 1.0 | 95074 | db_final_state |
| TAU-R-039 | train | state-changing | success | 1.0 | 1.0 | 40507 | db_final_state |
| TAU-R-040 | train | state-changing | success | 0.0 | 0.0 | 50450 | - |
| TAU-R-041 | train | state-changing | success | 1.0 | 1.0 | 80262 | db_final_state |
| TAU-R-042 | train | state-changing | success | 0.0 | 0.0 | 96669 | - |
| TAU-R-043 | train | state-changing | success | 0.0 | 0.0 | 56046 | - |
| TAU-R-044 | train | state-changing | success | 0.0 | 0.0 | 73772 | - |
| TAU-R-045 | train | state-changing | success | 0.0 | 0.0 | 67878 | - |
| TAU-R-048 | train | state-changing | success | 0.0 | 0.0 | 56256 | - |
| TAU-R-049 | train | state-changing | success | 0.0 | 0.0 | 66882 | - |
| TAU-R-050 | train | read-only | success | 0.0 | 0.0 | 30221 | - |
| TAU-R-051 | train | state-changing | success | 0.0 | 0.0 | 54817 | - |
| TAU-R-052 | train | state-changing | success | 0.0 | 0.0 | 95876 | - |
| TAU-R-053 | train | state-changing | success | 0.0 | 0.0 | 65814 | - |
| TAU-R-055 | train | state-changing | success | 1.0 | 1.0 | 81768 | db_final_state |
| TAU-R-056 | train | state-changing | success | 0.0 | 0.0 | 60099 | - |
| TAU-R-057 | train | read-only | success | 0.0 | 0.0 | 29551 | - |
| TAU-R-058 | train | state-changing | success | 0.0 | 0.0 | 97633 | - |
| TAU-R-059 | train | state-changing | success | 1.0 | 1.0 | 70810 | db_final_state |
| TAU-R-060 | train | state-changing | success | 0.0 | 0.0 | 39716 | - |
| TAU-R-061 | train | state-changing | success | 0.0 | 0.0 | 39321 | - |
| TAU-R-062 | train | read-only | success | 0.0 | 0.0 | 78042 | - |
| TAU-R-063 | train | state-changing | success | 0.0 | 0.0 | 91253 | - |
| TAU-R-064 | train | state-changing | success | 1.0 | 1.0 | 89462 | db_final_state |
| TAU-R-065 | train | read-only | success | 0.0 | 0.0 | 35125 | - |
| TAU-R-067 | train | read-only | success | 0.0 | 0.0 | 64944 | - |
| TAU-R-068 | train | read-only | success | 1.0 | 1.0 | 42799 | actions_match |
| TAU-R-069 | train | state-changing | success | 0.0 | 0.0 | 49368 | - |
| TAU-R-070 | train | state-changing | success | 1.0 | 1.0 | 48383 | db_final_state |
| TAU-R-071 | train | state-changing | success | 0.0 | 0.0 | 119134 | - |
| TAU-R-072 | train | state-changing | success | 1.0 | 1.0 | 93531 | db_final_state |
| TAU-R-073 | train | state-changing | success | 0.0 | 0.0 | 35721 | - |
| TAU-R-074 | train | state-changing | success | 0.0 | 0.0 | 96444 | - |
| TAU-R-075 | train | state-changing | success | 0.0 | 0.0 | 67784 | - |
| TAU-R-076 | train | state-changing | success | 1.0 | 1.0 | 106645 | db_final_state |
| TAU-R-077 | train | state-changing | success | 0.0 | 0.0 | 48340 | - |
| TAU-R-079 | train | state-changing | success | 0.0 | 0.0 | 63175 | - |
| TAU-R-080 | train | state-changing | success | 0.0 | 0.0 | 79078 | - |
| TAU-R-081 | train | state-changing | success | 0.0 | 0.0 | 68153 | - |
| TAU-R-082 | train | state-changing | success | 0.0 | 0.0 | 53215 | - |
| TAU-R-083 | train | state-changing | success | 0.0 | 0.0 | 64143 | - |
| TAU-R-084 | train | state-changing | success | 0.0 | 0.0 | 45900 | - |
| TAU-R-087 | train | state-changing | success | 0.0 | 0.0 | 59315 | - |
| TAU-R-088 | train | state-changing | success | 0.0 | 0.0 | 50475 | - |
| TAU-R-091 | train | state-changing | success | 1.0 | 1.0 | 83971 | db_final_state |
| TAU-R-092 | train | state-changing | success | 0.0 | 0.0 | 45793 | - |
| TAU-R-093 | train | state-changing | success | 1.0 | 1.0 | 49601 | db_final_state |
| TAU-R-094 | train | state-changing | success | 0.0 | 0.0 | 64714 | - |
| TAU-R-096 | train | state-changing | success | 0.0 | 0.0 | 71821 | - |
| TAU-R-097 | train | state-changing | success | 0.0 | 0.0 | 90994 | - |
| TAU-R-098 | train | state-changing | success | 0.0 | 0.0 | 56098 | - |
| TAU-R-099 | train | state-changing | success | 1.0 | 1.0 | 116074 | db_final_state |
| TAU-R-100 | train | state-changing | success | 0.0 | 0.0 | 107493 | - |
| TAU-R-101 | train | state-changing | success | 1.0 | 1.0 | 104219 | db_final_state |
| TAU-R-102 | train | state-changing | success | 0.0 | 0.0 | 134220 | - |
| TAU-R-105 | train | state-changing | success | 1.0 | 1.0 | 188631 | db_final_state |
| TAU-R-106 | train | read-only | success | 0.0 | 0.0 | 75866 | - |
| TAU-R-107 | train | state-changing | success | 0.0 | 0.0 | 70328 | - |
| TAU-R-108 | train | state-changing | success | 1.0 | 1.0 | 122711 | db_final_state |
| TAU-R-110 | train | state-changing | success | 1.0 | 1.0 | 96461 | db_final_state |
| TAU-R-111 | train | state-changing | success | 0.0 | 0.0 | 82733 | - |
| TAU-R-112 | train | state-changing | success | 1.0 | 1.0 | 112932 | db_final_state |
| TAU-R-113 | train | state-changing | success | 0.0 | 0.0 | 135862 | - |
| TAU-R-114 | train | state-changing | success | 0.0 | 0.0 | 51713 | - |
