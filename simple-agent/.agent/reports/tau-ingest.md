# τ-bench ingest 报告（5a.4 + P5a.9 签名归一化）

- 解析范围：test split only
- 原始任务数：airline=50 + retail=115 = 165
- 去重丢弃：6（阈值 similarity>0.85）
- 入库 REQ 数：159（train=135, dev=24）
- dev 占比：15.1%（要求 ≥15%）
- retail train（登记、本期不入库）：500
- 分桶：state-changing=128 / read-only=31

## 签名归一化（P5a.9 §三.1）

- 选型：GT 动作类型序列（read/write/compute/think/transfer 多重集）+ <3 小族确定性合并
- train 族数：**13**（要求 10~30）
- 最大族占比：**25.9%**（要求 <30%）
- 最小族规模：**3**（要求 ≥3）
- 族规模分布：[3, 3, 3, 4, 4, 4, 7, 9, 13, 13, 16, 21, 35]

## 成本预估（双模型口径）

- 单 epoch token 预估：9,540,000；成本 ≈ ¥19.08

## 入库清单（前 10 条示例）

| req_id | split | sig_family | tau_env | tau_task_id |
|---|---|---|---|---|
| TAU-R-090 | dev | 1932cfe427b1 | retail | 90 |
| TAU-R-063 | train | 721224ebfcc1 | retail | 63 |
| TAU-R-076 | train | e2040fc7e9c2 | retail | 76 |
| TAU-R-026 | train | 033f435f3aab | retail | 26 |
| TAU-A-035 | train | bb1218f84fd2 | airline | 35 |
| TAU-A-046 | train | 00c673ea4796 | airline | 46 |
| TAU-R-086 | dev | e2040fc7e9c2 | retail | 86 |
| TAU-R-101 | train | e2040fc7e9c2 | retail | 101 |
| TAU-A-000 | train | 1932cfe427b1 | airline | 0 |
| TAU-R-113 | train | 3d05a416ea71 | retail | 113 |

