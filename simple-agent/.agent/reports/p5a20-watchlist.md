# P5a.20 watchlist — 邻近学习注入对 + 上批失败任务

> 用途：修复测量路径后重测时，优先核对这批任务的注入内容与结局是否变化。
> 机器可读全量：`.agent/reports/p5a20-watchlist.json`

## A. 上批失败（已深审关卷 / 线束或任务缺陷）

| req | e4 | e5 | 备注 |
|---|---|---|---|
| TAU-A-008 | PASS | **FAIL** | 线束：GT 3 乘客 vs 模拟器 1 人 |
| TAU-A-019 | FAIL | FAIL | 线束：GT 05-19/JFK vs 模拟器 5/20、LGA |
| TAU-R-105 | FAIL | FAIL | 任务缺陷(jigsaw⊄GT)+锁序常量 |

## B. 邻近学习（precedent 臂注入=上一任务）

| epoch | req | trace | arm | expl | injected_sig | tok | **neighbor(=真实注入)** | verdict |
|---|---|---|---|---|---|---|---|---|
| 4 | TAU-A-000 | 7dea12c2 | direct | False | None | None | None | FAIL |
| 4 | TAU-A-000 | d06bc321 | precedent-assisted | True | 1932cfe427b1 | 208 | TAU-A-000 | FAIL |
| 4 | TAU-A-002 | 361e45de | precedent-assisted | False | 1932cfe427b1 | 209 | TAU-A-000 | PASS |
| 4 | TAU-A-003 | fbd2a8fa | precedent-assisted | False | 1932cfe427b1 | 500 | TAU-A-002 | PASS |
| 4 | TAU-A-005 | a755919f | direct | False | None | None | TAU-A-003 | PASS |
| 4 | TAU-A-006 | c7d4474b | precedent-assisted | False | 3d05a416ea71 | 300 | TAU-A-005 | PASS |
| 4 | TAU-A-007 **←** | 79ef7552 | precedent-assisted | False | 1932cfe427b1 | 177 | TAU-A-006 | PASS |
| 4 | TAU-A-008 **←** | 2b4917e1 | precedent-assisted | False | 1932cfe427b1 | 436 | TAU-A-007 | PASS |
| 4 | TAU-A-009 | 1a79c86c | precedent-assisted | False | e2040fc7e9c2 | 500 | TAU-A-008 | FAIL |
| 4 | TAU-A-012 | 5292d26c | precedent-assisted | False | 77f18e2446b6 | 500 | TAU-A-009 | PASS |
| 4 | TAU-A-013 | 9992f17b | direct | False | None | None | TAU-A-012 | PASS |
| 4 | TAU-A-014 | 2af8c045 | direct | False | None | None | TAU-A-013 | PASS |
| 4 | TAU-A-015 | 86ac4539 | direct | False | None | None | TAU-A-014 | FAIL |
| 4 | TAU-A-016 | 09fc3608 | precedent-assisted | False | a77091a4c3ce | 260 | TAU-A-015 | PASS |
| 4 | TAU-A-017 | b90671b3 | precedent-assisted | False | 033f435f3aab | 485 | TAU-A-016 | FAIL |
| 4 | TAU-A-018 **←** | ffff0229 | precedent-assisted | False | a77091a4c3ce | 358 | TAU-A-017 | PASS |
| 4 | TAU-A-019 **←** | f80ea911 | precedent-assisted | True | a77091a4c3ce | 175 | TAU-A-018 | FAIL |
| 4 | TAU-A-020 | a733d4af | direct | True | None | None | TAU-A-019 | PASS |
| 4 | TAU-A-021 | cfbbc455 | precedent-assisted | False | 033f435f3aab | 500 | TAU-A-020 | FAIL |
| 4 | TAU-A-022 | b3ad57bf | direct | True | None | None | TAU-A-021 | PASS |
| 4 | TAU-A-023 | a6247074 | precedent-assisted | True | 033f435f3aab | 221 | TAU-A-022 | FAIL |
| 4 | TAU-A-024 | 677ffebf | precedent-assisted | False | 033f435f3aab | 219 | TAU-A-023 | PASS |
| 4 | TAU-A-025 | 3e283f39 | direct | False | None | None | TAU-A-024 | PASS |
| 4 | TAU-A-026 **←** | 033dbfd2 | precedent-assisted | False | 1932cfe427b1 | 235 | TAU-A-025 | FAIL |
| 4 | TAU-A-027 **←** | a6199f2b | direct | False | None | None | TAU-A-026 | PASS |
| 4 | TAU-A-028 | 60bdcb1c | direct | True | None | None | TAU-A-027 | FAIL |
| 4 | TAU-A-029 | dce448ca | direct | False | None | None | TAU-A-028 | PASS |
| 4 | TAU-A-030 | b480350b | precedent-assisted | False | bb1218f84fd2 | 159 | TAU-A-029 | PASS |
| 4 | TAU-A-033 | 911f9505 | precedent-assisted | False | 033f435f3aab | 197 | TAU-A-030 | PASS |
| 4 | TAU-A-035 | ca22b0ed | direct | False | None | None | TAU-A-033 | PASS |
| 4 | TAU-A-036 | 5c579b9d | direct | False | None | None | TAU-A-035 | PASS |
| 4 | TAU-A-037 | 3574e71e | precedent-assisted | False | bb1218f84fd2 | 39 | TAU-A-036 | PASS |
| 4 | TAU-A-039 | 9a6d8480 | direct | False | None | None | TAU-A-037 | PASS |
| 4 | TAU-A-040 | 4beb763d | precedent-assisted | False | bb1218f84fd2 | 20 | TAU-A-039 | FAIL |
| 4 | TAU-A-042 | ca0a101a | direct | False | None | None | TAU-A-040 | PASS |
| 4 | TAU-A-043 | ae59abb5 | precedent-assisted | False | bb1218f84fd2 | 178 | TAU-A-042 | PASS |
| 4 | TAU-A-044 | 62ca01ae | direct | False | None | None | TAU-A-043 | PASS |
| 4 | TAU-A-045 | e824229b | direct | False | None | None | TAU-A-044 | FAIL |
| 4 | TAU-A-046 | fe2443d2 | direct | False | None | None | TAU-A-045 | FAIL |
| 4 | TAU-A-047 | 1cbe8a45 | precedent-assisted | False | 00c673ea4796 | 39 | TAU-A-046 | FAIL |
| 4 | TAU-A-048 | f71b4c88 | direct | False | None | None | TAU-A-047 | PASS |
| 4 | TAU-A-049 | d4f5a50e | direct | False | None | None | TAU-A-048 | PASS |
| 4 | TAU-R-000 | 868560f1 | direct | False | None | None | TAU-A-049 | PASS |
| 4 | TAU-R-002 | 38f1af4c | direct | False | None | None | TAU-R-000 | PASS |
| 4 | TAU-R-003 | df2903d4 | precedent-assisted | False | 033f435f3aab | 214 | TAU-R-002 | PASS |
| 4 | TAU-R-004 | ca4dd8b2 | direct | False | None | None | TAU-R-003 | PASS |
| 4 | TAU-R-005 | a38bda35 | precedent-assisted | False | 033f435f3aab | 260 | TAU-R-004 | FAIL |
| 4 | TAU-R-006 | 6bc260fa | direct | True | None | None | TAU-R-005 | PASS |
| 4 | TAU-R-010 | 72623d72 | direct | False | None | None | TAU-R-006 | PASS |
| 4 | TAU-R-011 | 604af691 | precedent-assisted | False | bb1218f84fd2 | 189 | TAU-R-010 | PASS |
| 4 | TAU-R-012 | 5ec8d353 | precedent-assisted | False | 2246f912173d | 162 | TAU-R-011 | PASS |
| 4 | TAU-R-013 | d94f9186 | direct | False | None | None | TAU-R-012 | PASS |
| 4 | TAU-R-016 | b5aa6efa | direct | False | None | None | TAU-R-013 | PASS |
| 4 | TAU-R-017 | 8a8dad7c | direct | False | None | None | TAU-R-016 | PASS |
| 4 | TAU-R-019 | fd4cb81d | precedent-assisted | False | 033f435f3aab | 98 | TAU-R-017 | PASS |
| 4 | TAU-R-020 | 38ee9d5c | direct | False | None | None | TAU-R-019 | FAIL |
| 4 | TAU-R-021 | 3dbf83c0 | precedent-assisted | False | 033f435f3aab | 243 | TAU-R-020 | PASS |
| 4 | TAU-R-022 | eb8c57dd | precedent-assisted | True | 721224ebfcc1 | 191 | TAU-R-021 | PASS |
| 4 | TAU-R-023 | b0e4d077 | direct | False | None | None | TAU-R-022 | PASS |
| 4 | TAU-R-024 | 2b99987a | precedent-assisted | False | 033f435f3aab | 339 | TAU-R-023 | FAIL |
| 4 | TAU-R-025 | d3a5f083 | precedent-assisted | False | a77091a4c3ce | 164 | TAU-R-024 | PASS |
| 4 | TAU-R-026 | a603cfc5 | direct | False | None | None | TAU-R-025 | PASS |
| 4 | TAU-R-027 | 5fb514e4 | precedent-assisted | False | 033f435f3aab | 162 | TAU-R-026 | PASS |
| 4 | TAU-R-028 | cc086638 | direct | False | None | None | TAU-R-027 | FAIL |
| 4 | TAU-R-029 | 5cae99f5 | precedent-assisted | False | 721224ebfcc1 | 267 | TAU-R-028 | PASS |
| 4 | TAU-R-030 | 8138eac1 | precedent-assisted | False | 2246f912173d | 251 | TAU-R-029 | PASS |
| 4 | TAU-R-031 | c6c9e036 | direct | False | None | None | TAU-R-030 | PASS |
| 4 | TAU-R-032 | a46d2be0 | direct | False | None | None | TAU-R-031 | PASS |
| 4 | TAU-R-033 | e3aa4675 | precedent-assisted | False | 033f435f3aab | 226 | TAU-R-032 | PASS |
| 4 | TAU-R-034 | ca2c6f10 | direct | False | None | None | TAU-R-033 | FAIL |
| 4 | TAU-R-035 | 33ecf687 | direct | False | None | None | TAU-R-034 | PASS |
| 4 | TAU-R-036 | 2efa6774 | direct | False | None | None | TAU-R-035 | PASS |
| 4 | TAU-R-038 | 0dbfbff6 | precedent-assisted | False | 033f435f3aab | 268 | TAU-R-036 | FAIL |
| 4 | TAU-R-039 | e9d129b8 | precedent-assisted | False | 721224ebfcc1 | 210 | TAU-R-038 | FAIL |
| 4 | TAU-R-040 | e3cb805d | direct | False | None | None | TAU-R-039 | PASS |
| 4 | TAU-R-041 | 536c5bb2 | precedent-assisted | False | 00c673ea4796 | 92 | TAU-R-040 | PASS |
| 4 | TAU-R-042 | b5309c16 | precedent-assisted | False | 033f435f3aab | 445 | TAU-R-041 | PASS |
| 4 | TAU-R-043 | 6d4e4352 | direct | True | None | None | TAU-R-042 | PASS |
| 4 | TAU-R-044 | 10728e66 | direct | False | None | None | TAU-R-043 | PASS |
| 4 | TAU-R-045 | d47591a2 | direct | False | None | None | TAU-R-044 | PASS |
| 4 | TAU-R-048 | 2f359bd1 | direct | False | None | None | TAU-R-045 | PASS |
| 4 | TAU-R-049 | 01d26623 | direct | True | None | None | TAU-R-048 | PASS |
| 4 | TAU-R-050 | 9bf0b987 | direct | False | None | None | TAU-R-049 | PASS |
| 4 | TAU-R-051 | f98a0eb9 | precedent-assisted | False | 1932cfe427b1 | 198 | TAU-R-050 | PASS |
| 4 | TAU-R-052 | 43e9777c | direct | True | None | None | TAU-R-051 | PASS |
| 4 | TAU-R-053 | e84ae70f | direct | False | None | None | TAU-R-052 | PASS |
| 4 | TAU-R-055 | 94eb6fd0 | direct | False | None | None | TAU-R-053 | PASS |
| 4 | TAU-R-056 | 83c9b011 | precedent-assisted | False | 033f435f3aab | 308 | TAU-R-055 | PASS |
| 4 | TAU-R-057 | d49545e2 | precedent-assisted | False | f18452329f5c | 166 | TAU-R-056 | PASS |
| 4 | TAU-R-058 | d66a57c6 | direct | False | None | None | TAU-R-057 | PASS |
| 4 | TAU-R-059 | 768eaeaf | direct | False | None | None | TAU-R-058 | FAIL |
| 4 | TAU-R-060 | 11856a3b | precedent-assisted | False | 721224ebfcc1 | 139 | TAU-R-059 | PASS |
| 4 | TAU-R-061 | 390cbb5c | direct | False | None | None | TAU-R-060 | PASS |
| 4 | TAU-R-062 | 4036ad99 | precedent-assisted | False | 721224ebfcc1 | 110 | TAU-R-061 | PASS |
| 4 | TAU-R-063 | e0aa3613 | direct | False | None | None | TAU-R-062 | PASS |
| 4 | TAU-R-064 | f53e6eb8 | precedent-assisted | False | 721224ebfcc1 | 187 | TAU-R-063 | PASS |
| 4 | TAU-R-065 | 2ce8df56 | direct | False | None | None | TAU-R-064 | PASS |
| 4 | TAU-R-067 | 10ef8f31 | direct | False | None | None | TAU-R-065 | PASS |
| 4 | TAU-R-068 | 8759ab30 | precedent-assisted | False | bb1218f84fd2 | 300 | TAU-R-067 | PASS |
| 4 | TAU-R-069 | 462824f7 | precedent-assisted | False | bb1218f84fd2 | 289 | TAU-R-068 | PASS |
| 4 | TAU-R-070 | f810216e | direct | False | None | None | TAU-R-069 | PASS |
| 4 | TAU-R-071 | 74edda92 | precedent-assisted | False | 1932cfe427b1 | 186 | TAU-R-070 | PASS |
| 4 | TAU-R-072 | ea12605b | precedent-assisted | False | e2040fc7e9c2 | 252 | TAU-R-071 | PASS |
| 4 | TAU-R-073 | ef898931 | direct | False | None | None | TAU-R-072 | PASS |
| 4 | TAU-R-074 | 94b82b6a | precedent-assisted | False | 1932cfe427b1 | 109 | TAU-R-073 | FAIL |
| 4 | TAU-R-075 | 08b1ebe5 | direct | False | None | None | TAU-R-074 | PASS |
| 4 | TAU-R-076 | 101ce1e1 | precedent-assisted | False | 1932cfe427b1 | 123 | TAU-R-075 | FAIL |
| 4 | TAU-R-077 | 48492fe0 | precedent-assisted | False | e2040fc7e9c2 | 218 | TAU-R-076 | PASS |
| 4 | TAU-R-079 | 291c783f | direct | False | None | None | TAU-R-077 | PASS |
| 4 | TAU-R-080 | 0367c73b | direct | False | None | None | TAU-R-079 | PASS |
| 4 | TAU-R-081 | a66d3192 | precedent-assisted | False | 1932cfe427b1 | 124 | TAU-R-080 | PASS |
| 4 | TAU-R-082 | f5859e89 | precedent-assisted | False | e2040fc7e9c2 | 163 | TAU-R-081 | PASS |
| 4 | TAU-R-083 | cff1a539 | precedent-assisted | False | 1932cfe427b1 | 166 | TAU-R-082 | PASS |
| 4 | TAU-R-084 | b7c88318 | precedent-assisted | False | 1932cfe427b1 | 156 | TAU-R-083 | PASS |
| 4 | TAU-R-087 | 0dbe64ef | precedent-assisted | False | 1932cfe427b1 | 156 | TAU-R-084 | PASS |
| 4 | TAU-R-088 | 92ebb5b8 | direct | False | None | None | TAU-R-087 | FAIL |
| 4 | TAU-R-091 | d2977e14 | precedent-assisted | False | 1932cfe427b1 | 122 | TAU-R-088 | FAIL |
| 4 | TAU-R-092 | 2e48ddd5 | precedent-assisted | False | e2040fc7e9c2 | 211 | TAU-R-091 | PASS |
| 4 | TAU-R-093 | fc54feab | direct | False | None | None | TAU-R-092 | PASS |
| 4 | TAU-R-094 | 5dd67122 | direct | False | None | None | TAU-R-093 | PASS |
| 4 | TAU-R-096 | 1e45db21 | precedent-assisted | False | 1932cfe427b1 | 166 | TAU-R-094 | PASS |
| 4 | TAU-R-097 | c24af858 | precedent-assisted | False | e2040fc7e9c2 | 237 | TAU-R-096 | FAIL |
| 4 | TAU-R-098 | 03e78b32 | precedent-assisted | False | e2040fc7e9c2 | 152 | TAU-R-097 | PASS |
| 4 | TAU-R-099 | ad833e41 | direct | False | None | None | TAU-R-098 | FAIL |
| 4 | TAU-R-100 | 7a40890b | precedent-assisted | False | 3d05a416ea71 | 321 | TAU-R-099 | FAIL |
| 4 | TAU-R-101 | 39bcfcd0 | precedent-assisted | False | e2040fc7e9c2 | 301 | TAU-R-100 | PASS |
| 4 | TAU-R-102 **←** | 06779ef0 | direct | False | None | None | TAU-R-101 | PASS |
| 4 | TAU-R-105 **←** | ca1ff8d1 | precedent-assisted | False | 3d05a416ea71 | 281 | TAU-R-102 | FAIL |
| 4 | TAU-R-106 | 7dd7b5e0 | direct | False | None | None | TAU-R-105 | FAIL |
| 4 | TAU-R-107 | 7b16cf85 | precedent-assisted | False | 1932cfe427b1 | 132 | TAU-R-106 | PASS |
| 4 | TAU-R-108 | 6511679b | precedent-assisted | False | 1932cfe427b1 | 182 | TAU-R-107 | FAIL |
| 4 | TAU-R-110 | 38cd6ceb | precedent-assisted | True | e2040fc7e9c2 | 238 | TAU-R-108 | PASS |
| 4 | TAU-R-111 | 5a1749ac | precedent-assisted | False | 3d05a416ea71 | 245 | TAU-R-110 | FAIL |
| 4 | TAU-R-112 | 80786b2f | direct | False | None | None | TAU-R-111 | PASS |
| 4 | TAU-R-113 | 618293da | direct | False | None | None | TAU-R-112 | FAIL |
| 4 | TAU-R-114 | 169b2e20 | precedent-assisted | False | 3d05a416ea71 | 247 | TAU-R-113 | PASS |
| 5 | TAU-A-000 | 047c1440 | direct | False | None | None | None | PASS |
| 5 | TAU-A-002 | 45a50df1 | direct | False | None | None | TAU-A-000 | FAIL |
| 5 | TAU-A-003 | 4bd5ab22 | precedent-assisted | False | 1932cfe427b1 | 500 | TAU-A-002 | FAIL |
| 5 | TAU-A-005 | b5d7b0a8 | precedent-assisted | False | e2040fc7e9c2 | 234 | TAU-A-003 | PASS |
| 5 | TAU-A-006 | 6a5e61b1 | precedent-assisted | False | 3d05a416ea71 | 500 | TAU-A-005 | FAIL |
| 5 | TAU-A-007 **←** | 40e626cd | direct | False | None | None | TAU-A-006 | PASS |
| 5 | TAU-A-008 **←** | f854dfb5 | precedent-assisted | False | 1932cfe427b1 | 213 | TAU-A-007 | FAIL |
| 5 | TAU-A-009 | ed6e885e | precedent-assisted | False | e2040fc7e9c2 | 328 | TAU-A-008 | FAIL |
| 5 | TAU-A-012 | 7c56db78 | precedent-assisted | False | 77f18e2446b6 | 341 | TAU-A-009 | PASS |
| 5 | TAU-A-013 | b51cdcaa | direct | False | None | None | TAU-A-012 | PASS |
| 5 | TAU-A-014 | 734cff5d | direct | False | None | None | TAU-A-013 | PASS |
| 5 | TAU-A-015 | b7286a7e | precedent-assisted | False | 721224ebfcc1 | 134 | TAU-A-014 | PASS |
| 5 | TAU-A-016 | 986eebe6 | precedent-assisted | False | a77091a4c3ce | 316 | TAU-A-015 | PASS |
| 5 | TAU-A-017 | 4a6edd87 | precedent-assisted | False | 033f435f3aab | 326 | TAU-A-016 | FAIL |
| 5 | TAU-A-018 **←** | 6bb5290d | direct | False | None | None | TAU-A-017 | PASS |
| 5 | TAU-A-019 **←** | 594bcfc2 | direct | False | None | None | TAU-A-018 | FAIL |
| 5 | TAU-A-020 | 2a1653b5 | precedent-assisted | False | 033f435f3aab | 203 | TAU-A-019 | PASS |
| 5 | TAU-A-021 | 43b252fd | precedent-assisted | False | 033f435f3aab | 130 | TAU-A-020 | PASS |
| 5 | TAU-A-022 | a7ffce1b | precedent-assisted | False | a77091a4c3ce | 78 | TAU-A-021 | PASS |
| 5 | TAU-A-023 | 4df6c0bf | direct | False | None | None | TAU-A-022 | PASS |
| 5 | TAU-A-024 | c635c5ac | precedent-assisted | False | 033f435f3aab | 458 | TAU-A-023 | PASS |
| 5 | TAU-A-025 | 6b5c6903 | precedent-assisted | False | a77091a4c3ce | 110 | TAU-A-024 | PASS |
| 5 | TAU-A-026 **←** | 5745f3da | precedent-assisted | False | 1932cfe427b1 | 231 | TAU-A-025 | PASS |
| 5 | TAU-A-027 **←** | ccd381e9 | precedent-assisted | False | 721224ebfcc1 | 216 | TAU-A-026 | PASS |
| 5 | TAU-A-028 | c92def96 | precedent-assisted | False | 721224ebfcc1 | 182 | TAU-A-027 | FAIL |
| 5 | TAU-A-029 | 810148cf | direct | False | None | None | TAU-A-028 | PASS |
| 5 | TAU-A-030 | 0b9f32df | direct | False | None | None | TAU-A-029 | PASS |
| 5 | TAU-A-033 | 36204b64 | direct | False | None | None | TAU-A-030 | FAIL |
| 5 | TAU-A-035 | af99766e | precedent-assisted | False | 033f435f3aab | 411 | TAU-A-033 | PASS |
| 5 | TAU-A-036 | 62148cf7 | direct | False | None | None | TAU-A-035 | PASS |
| 5 | TAU-A-037 | c311fcf1 | direct | False | None | None | TAU-A-036 | PASS |
| 5 | TAU-A-039 | 4200919a | direct | False | None | None | TAU-A-037 | PASS |
| 5 | TAU-A-040 | 2c95f528 | precedent-assisted | False | bb1218f84fd2 | 20 | TAU-A-039 | FAIL |
| 5 | TAU-A-042 | 3163dd34 | direct | False | None | None | TAU-A-040 | PASS |
| 5 | TAU-A-043 | bc0c57fc | precedent-assisted | True | bb1218f84fd2 | 149 | TAU-A-042 | PASS |
| 5 | TAU-A-044 | 7403f669 | direct | False | None | None | TAU-A-043 | PASS |
| 5 | TAU-A-045 | 8542a3ba | direct | False | None | None | TAU-A-044 | FAIL |
| 5 | TAU-A-046 | d65eda89 | direct | False | None | None | TAU-A-045 | FAIL |
| 5 | TAU-A-047 | fa1339f8 | precedent-assisted | False | 00c673ea4796 | 39 | TAU-A-046 | PASS |
| 5 | TAU-A-048 | dd9a0696 | direct | False | None | None | TAU-A-047 | PASS |
| 5 | TAU-A-049 | e6f7f84f | precedent-assisted | False | bb1218f84fd2 | 20 | TAU-A-048 | PASS |
| 5 | TAU-R-000 | 9b2dad1f | direct | False | None | None | TAU-A-049 | PASS |
| 5 | TAU-R-002 | 564ed93a | direct | True | None | None | TAU-R-000 | PASS |
| 5 | TAU-R-003 | 2410cba6 | precedent-assisted | False | 033f435f3aab | 214 | TAU-R-002 | PASS |
| 5 | TAU-R-004 | 5f14114f | direct | False | None | None | TAU-R-003 | PASS |
| 5 | TAU-R-005 | ee9dc941 | direct | False | None | None | TAU-R-004 | PASS |
| 5 | TAU-R-006 | 69211817 | direct | False | None | None | TAU-R-005 | FAIL |
| 5 | TAU-R-010 | 2809aee0 | precedent-assisted | False | 033f435f3aab | 184 | TAU-R-006 | PASS |
| 5 | TAU-R-011 | 08dfa824 | precedent-assisted | False | bb1218f84fd2 | 76 | TAU-R-010 | PASS |
| 5 | TAU-R-012 | 61523a67 | direct | False | None | None | TAU-R-011 | PASS |
| 5 | TAU-R-013 | cd0f25c7 | precedent-assisted | False | 033f435f3aab | 263 | TAU-R-012 | PASS |
| 5 | TAU-R-016 | b535c9cf | direct | False | None | None | TAU-R-013 | PASS |
| 5 | TAU-R-017 | 3ed316fe | direct | False | None | None | TAU-R-016 | PASS |
| 5 | TAU-R-019 | 42609dc3 | precedent-assisted | False | 033f435f3aab | 98 | TAU-R-017 | PASS |
| 5 | TAU-R-020 | bccd1c30 | direct | False | None | None | TAU-R-019 | FAIL |
| 5 | TAU-R-021 | ddac5213 | direct | False | None | None | TAU-R-020 | PASS |
| 5 | TAU-R-022 | 309b5573 | direct | False | None | None | TAU-R-021 | PASS |
| 5 | TAU-R-023 | bad2c7ce | direct | False | None | None | TAU-R-022 | PASS |
| 5 | TAU-R-024 | 3b09e509 | precedent-assisted | False | 033f435f3aab | 317 | TAU-R-023 | PASS |
| 5 | TAU-R-025 | 31f51495 | precedent-assisted | False | a77091a4c3ce | 120 | TAU-R-024 | PASS |
| 5 | TAU-R-026 | 94f0c5b1 | direct | False | None | None | TAU-R-025 | PASS |
| 5 | TAU-R-027 | ac78f571 | direct | False | None | None | TAU-R-026 | PASS |
| 5 | TAU-R-028 | b8e616a6 | direct | False | None | None | TAU-R-027 | PASS |
| 5 | TAU-R-029 | 9f16d429 | direct | False | None | None | TAU-R-028 | FAIL |
| 5 | TAU-R-030 | 1d066c0f | precedent-assisted | False | 2246f912173d | 251 | TAU-R-029 | PASS |
| 5 | TAU-R-031 | 304f7605 | precedent-assisted | False | 033f435f3aab | 257 | TAU-R-030 | FAIL |
| 5 | TAU-R-032 | d791f634 | precedent-assisted | False | 033f435f3aab | 200 | TAU-R-031 | PASS |
| 5 | TAU-R-033 | e7b812f7 | precedent-assisted | False | 033f435f3aab | 226 | TAU-R-032 | PASS |
| 5 | TAU-R-034 | 82c586b2 | direct | False | None | None | TAU-R-033 | FAIL |
| 5 | TAU-R-035 | be22394b | direct | False | None | None | TAU-R-034 | PASS |
| 5 | TAU-R-036 | 0fdcc0fd | precedent-assisted | False | 033f435f3aab | 201 | TAU-R-035 | PASS |
| 5 | TAU-R-038 | f68ead0e | direct | False | None | None | TAU-R-036 | FAIL |
| 5 | TAU-R-039 | df1fa06d | direct | True | None | None | TAU-R-038 | FAIL |
| 5 | TAU-R-040 | 54ad0258 | direct | True | None | None | TAU-R-039 | PASS |
| 5 | TAU-R-041 | f83157f8 | precedent-assisted | False | 00c673ea4796 | 92 | TAU-R-040 | PASS |
| 5 | TAU-R-042 | 628c8853 | precedent-assisted | True | 033f435f3aab | 482 | TAU-R-041 | PASS |
| 5 | TAU-R-043 | 8666ef2b | precedent-assisted | False | 033f435f3aab | 301 | TAU-R-042 | PASS |
| 5 | TAU-R-044 | d0e3efdb | direct | False | None | None | TAU-R-043 | PASS |
| 5 | TAU-R-045 | 78c51878 | precedent-assisted | False | 721224ebfcc1 | 129 | TAU-R-044 | PASS |
| 5 | TAU-R-048 | cac4d763 | precedent-assisted | False | 721224ebfcc1 | 148 | TAU-R-045 | PASS |
| 5 | TAU-R-049 | 3d1eb481 | precedent-assisted | True | 033f435f3aab | 139 | TAU-R-048 | PASS |
| 5 | TAU-R-050 | 7cea9a02 | precedent-assisted | True | 721224ebfcc1 | 203 | TAU-R-049 | PASS |
| 5 | TAU-R-051 | 101cc6da | precedent-assisted | False | 1932cfe427b1 | 188 | TAU-R-050 | PASS |
| 5 | TAU-R-052 | a05a5679 | direct | False | None | None | TAU-R-051 | FAIL |
| 5 | TAU-R-053 | 8c8b156a | precedent-assisted | False | 7aad7aef32f1 | 136 | TAU-R-052 | PASS |
| 5 | TAU-R-055 | 08fb446a | direct | False | None | None | TAU-R-053 | PASS |
| 5 | TAU-R-056 | abdf16f0 | precedent-assisted | False | 033f435f3aab | 308 | TAU-R-055 | PASS |
| 5 | TAU-R-057 | 76402691 | precedent-assisted | False | f18452329f5c | 166 | TAU-R-056 | PASS |
| 5 | TAU-R-058 | 0ed5415e | precedent-assisted | False | a77091a4c3ce | 47 | TAU-R-057 | PASS |
| 5 | TAU-R-059 | b4d05ccb | direct | False | None | None | TAU-R-058 | FAIL |
| 5 | TAU-R-060 | 52dd1f41 | precedent-assisted | False | 721224ebfcc1 | 139 | TAU-R-059 | PASS |
| 5 | TAU-R-061 | ce5de102 | direct | False | None | None | TAU-R-060 | PASS |
| 5 | TAU-R-062 | 55ef5e72 | precedent-assisted | False | 721224ebfcc1 | 110 | TAU-R-061 | FAIL |
| 5 | TAU-R-063 | 58e86658 | precedent-assisted | False | 9a9107c53f34 | 165 | TAU-R-062 | FAIL |
| 5 | TAU-R-064 | 00666098 | direct | False | None | None | TAU-R-063 | PASS |
| 5 | TAU-R-065 | 15a0df32 | direct | False | None | None | TAU-R-064 | PASS |
| 5 | TAU-R-067 | 6d9b4515 | direct | False | None | None | TAU-R-065 | PASS |
| 5 | TAU-R-068 | a2e9db9a | direct | False | None | None | TAU-R-067 | PASS |
| 5 | TAU-R-069 | 65515e99 | direct | False | None | None | TAU-R-068 | PASS |
| 5 | TAU-R-070 | 05ba7818 | precedent-assisted | True | 00c673ea4796 | 126 | TAU-R-069 | PASS |
| 5 | TAU-R-071 | 61d7afec | precedent-assisted | False | 1932cfe427b1 | 186 | TAU-R-070 | FAIL |
| 5 | TAU-R-072 | a67f1b04 | precedent-assisted | False | e2040fc7e9c2 | 260 | TAU-R-071 | PASS |
| 5 | TAU-R-073 | d62776b9 | direct | False | None | None | TAU-R-072 | PASS |
| 5 | TAU-R-074 | 0e4498a2 | precedent-assisted | False | 1932cfe427b1 | 109 | TAU-R-073 | PASS |
| 5 | TAU-R-075 | da7302eb | direct | False | None | None | TAU-R-074 | PASS |
| 5 | TAU-R-076 | 144a298b | precedent-assisted | False | 1932cfe427b1 | 123 | TAU-R-075 | FAIL |
| 5 | TAU-R-077 | 3365b04c | direct | False | None | None | TAU-R-076 | PASS |
| 5 | TAU-R-079 | d10c6d40 | direct | False | None | None | TAU-R-077 | FAIL |
| 5 | TAU-R-080 | a9a0e29b | direct | True | None | None | TAU-R-079 | PASS |
| 5 | TAU-R-081 | 36fd1456 | precedent-assisted | True | 1932cfe427b1 | 161 | TAU-R-080 | PASS |
| 5 | TAU-R-082 | a63aea83 | direct | False | None | None | TAU-R-081 | PASS |
| 5 | TAU-R-083 | 16cad518 | direct | False | None | None | TAU-R-082 | PASS |
| 5 | TAU-R-084 | b20e930d | direct | False | None | None | TAU-R-083 | PASS |
| 5 | TAU-R-087 | ce8a3052 | precedent-assisted | False | 1932cfe427b1 | 156 | TAU-R-084 | PASS |
| 5 | TAU-R-088 | 4596c9d0 | precedent-assisted | False | 77f18e2446b6 | 341 | TAU-R-087 | FAIL |
| 5 | TAU-R-091 | 6958a5a5 | precedent-assisted | False | 1932cfe427b1 | 122 | TAU-R-088 | FAIL |
| 5 | TAU-R-092 | 0c515afb | precedent-assisted | False | e2040fc7e9c2 | 202 | TAU-R-091 | PASS |
| 5 | TAU-R-093 | 1e3e26a8 | direct | False | None | None | TAU-R-092 | PASS |
| 5 | TAU-R-094 | afc977ee | direct | False | None | None | TAU-R-093 | PASS |
| 5 | TAU-R-096 | 590a6f0f | precedent-assisted | False | 1932cfe427b1 | 166 | TAU-R-094 | PASS |
| 5 | TAU-R-097 | 90f17a21 | direct | True | None | None | TAU-R-096 | PASS |
| 5 | TAU-R-098 | d6fe927b | precedent-assisted | False | e2040fc7e9c2 | 197 | TAU-R-097 | PASS |
| 5 | TAU-R-099 | ff297b0b | direct | False | None | None | TAU-R-098 | FAIL |
| 5 | TAU-R-100 | 7df7f08c | direct | False | None | None | TAU-R-099 | FAIL |
| 5 | TAU-R-101 | 811c37a1 | precedent-assisted | True | e2040fc7e9c2 | 268 | TAU-R-100 | FAIL |
| 5 | TAU-R-102 **←** | 2c80e024 | direct | False | None | None | TAU-R-101 | PASS |
| 5 | TAU-R-105 **←** | fa73670f | precedent-assisted | True | 3d05a416ea71 | 281 | TAU-R-102 | FAIL |
| 5 | TAU-R-106 | 2106318e | direct | False | None | None | TAU-R-105 | PASS |
| 5 | TAU-R-107 | e945141e | precedent-assisted | False | 1932cfe427b1 | 361 | TAU-R-106 | PASS |
| 5 | TAU-R-108 | 67f92a21 | precedent-assisted | False | 1932cfe427b1 | 182 | TAU-R-107 | FAIL |
| 5 | TAU-R-110 | 0edcb738 | direct | False | None | None | TAU-R-108 | PASS |
| 5 | TAU-R-111 | 3cb25dab | direct | False | None | None | TAU-R-110 | PASS |
| 5 | TAU-R-112 | 044d5853 | direct | False | None | None | TAU-R-111 | PASS |
| 5 | TAU-R-113 | 873b6577 | direct | False | None | None | TAU-R-112 | PASS |
| 5 | TAU-R-114 | 591ddad4 | precedent-assisted | False | 3d05a416ea71 | 299 | TAU-R-113 | PASS |

**计数**：e4 precedent 臂 70 条 / e5 66 条；两 epoch 全部 precedent 臂任务均注入『上一任务』计划（工单1/3 证明）。

**判据**：`neighbor` 列 = 同 epoch 内按 created_at 排序的紧邻上一任务；A-008/A-019/R-105 的注入已实证等于该列。
