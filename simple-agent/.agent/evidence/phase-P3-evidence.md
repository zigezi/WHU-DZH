# Phase P3 证据 — 记忆与路由 + B/C 段观测（backfill，真实重跑）

- 生成时间：2026-09-11T11:44:51+08:00
- 分支：simple-agent @ 71987cd

## 5.0.0 极简线性规划器（确定性，不调 LLM）

```
$ python3 -c "import planner; ..."
在 workspace 中创建 hello.txt，并写入内容 hi -> [('n0', '创建', [], ['hello.txt']), ('n1', '写入', ['n0'], [])] | step->node: ['n0', 'n1', 'n1', 'n1']
帮我处理一下那个文件 -> [('n0', '处理', [], [])] | step->node: ['n0', 'n0', 'n0', 'n0']
```

## 5.0.1 B 段：plan span 存在 + E 层 span 含 plan_node_id（REQ-001, trace=ef768e97-d17d-45cc-947c-19b1e3a0ed27）

```
$ sqlite3 -readonly logs/trace.db "SELECT layer,type,node_count,schema_valid,owns_disjoint,planner_model FROM spans WHERE trace_id='ef768e97-d17d-45cc-947c-19b1e3a0ed27' AND type='plan'"
L|plan|2|1|1|deterministic-linear-v1
$ sqlite3 ... E 层 plan_node_id
write_file|n0
read_file|n1
$ sqlite3 ... 该任务 E 层 span 均含 plan_node_id（缺失数=0）
0
```

## 5.0.2 C 段：decomposition-report.md 真实生成（含真实数值）

```
$ cat .agent/reports/decomposition-report.md
# 切分质量报告（decomposition-report）

- 生成时间：2026-09-11T11:44:34.499624
- 最近 trace：c2b903a0-5f0b-4bef-942e-8eea4605774b

## 最近一次切分

| metric | value |
|---|---|
| plan_id | 1b475242-2054-4643-bd6d-cce1ffc4bd9b |
| req_id | REQ-006 |
| node_success_rate | 1.0 |
| avg_retries | 7.0 |
| rework_edges | 0 |
| owns_conflicts | 0 |
| token_cv | 0.0 |
| critical_path | 1 |
| replan_count | 0 |

## planner 排行表

| planner_model | prompt_version | n | avg_node_success_rate | total_conflicts |
|---|---|---|---|---|
| deterministic-linear-v1 | n/a | 4 | 0.75 | 0 |

- owns_conflict_rate: 0.0
- rework_edge_rate: 0.25
```

### C 段对故意失败任务 REQ-004（trace=2a02e3f0-3ee2-41f8-985b-f1c9f49ead24）的指标：rework_edges>0、owns_conflicts=0

```
$ python3 -c "plan_observer.decomposition_report('2a02e3f0-3ee2-41f8-985b-f1c9f49ead24', write_span=False)"
{'trace_id': '2a02e3f0-3ee2-41f8-985b-f1c9f49ead24', 'plan_id': 'c7f025f6-6b7d-49eb-9e91-9589c29f213e', 'req_id': 'REQ-004', 'node_success_rate': 0.0, 'avg_retries': 2.0, 'rework_edges': 1, 'owns_conflicts': 0, 'token_cv': 0.0, 'critical_path': 3, 'replan_count': 0}
```

## 5.1 任务签名器（相似 >0.3，无关 <0.1）

```
similar  = 0.6 (want >0.3)
unrelated= 0.0 (want <0.1)
sign     = 22df338bc3fe
```

## 5.2 路由后验表（连续成功 5 次 → 后验偏移）

```
alpha,beta = (16.0, 1.0)
```

## 5.3 先例库（相似文本可召回）

```
$ curl -s "localhost:8000/precedents/similar?content=在workspace创建hello.txt写入hi&top=3"
hits= 3
  None sim= 1.0 | 在 workspace 创建 hello.txt 写入 hi
  None sim= 1.0 | 在 workspace 创建 hello.txt 写入 hi
  REQ-001 sim= 0.6364 | 在 workspace 中创建 hello.txt，并写入内容 hi
```

## 5.4 弃权机制（全新类型任务 → abstain_check{matched:false}，trace=c2b903a0-5f0b-4bef-942e-8eea4605774b）

```
$ sqlite3 -readonly logs/trace.db "SELECT layer,type,attributes FROM spans WHERE trace_id='c2b903a0-5f0b-4bef-942e-8eea4605774b' AND type='abstain_check'"
L|abstain_check|{"matched": false, "best_similarity": 0.0526}
```
