# Phase P1 证据 — V 层：尺子（backfill，真实重跑）

- 生成时间：2026-09-11T11:33:18+08:00
- 分支：simple-agent @ 2c133b2

## 1.1 需求集入库门禁（无 assertions / 无 task / 非法 split 均拒绝）

```
$ python3 - <<PY ... loader.load_requirement tests ...
[ok] ACCEPTED
[no_assertions] REJECTED: TMP: 无 assertions，拒绝入库（绑定率门禁）
[no_task] REJECTED: TMP: 缺少 task 字段，拒绝入库（eval_loop 只允许用 task 喂模型）
[empty_task] REJECTED: TMP: 缺少 task 字段，拒绝入库（eval_loop 只允许用 task 喂模型）
[bad_split] REJECTED: TMP: split 必须属于 ['dev', 'train']
--- all 8 real requirements ---
 loaded REQ-001 train
 loaded REQ-002 train
 loaded REQ-003 train
 loaded REQ-004 train
 loaded REQ-005 train
 loaded REQ-006 train
 loaded REQ-007 dev
 loaded REQ-008 dev
```

## 1.2 V 层执行器：故意失败需求 → V 层 span + loss>0（REQ-006 歧义需求）

```
$ curl -X POST /task/submit {"content":"帮我处理一下那个文件","req_id":"REQ-006"}  -> task_id=887fba7d-ba0d-44de-b2e0-f5dc19f2e06f
$ curl -s localhost:8000/task/887fba7d-ba0d-44de-b2e0-f5dc19f2e06f | status
success
$ python3 -c "from monitor import vlayer; r=vlayer.evaluate('REQ-006', trace_id='887fba7d-ba0d-44de-b2e0-f5dc19f2e06f'); ..."
loss = 3
decision = FAIL
  not_lying_success passed= False severity= blocker
$ sqlite3 -readonly logs/trace.db "SELECT type, json_extract(attributes,'$.name'), json_extract(attributes,'$.passed') FROM spans WHERE trace_id='887fba7d-ba0d-44de-b2e0-f5dc19f2e06f' AND layer='V'"
progress||0
progress||0
acceptance_check|not_lying_success|0
verdict||
acceptance_check|not_lying_success|0
verdict||
```

## 1.3 每步进度曲线（REQ-001 带 cheap 断言）

```
$ curl -X POST /task/submit {"content":"在 workspace 中创建 hello.txt，并写入内容 hi","req_id":"REQ-001"}  -> task_id=adef40d1-4e4a-41c4-ab85-01bd4059fe71
$ sqlite3 -readonly logs/trace.db "SELECT step,passed,total,tokens_so_far FROM spans WHERE trace_id='adef40d1-4e4a-41c4-ab85-01bd4059fe71' AND type='progress' ORDER BY step"
1|2|2|676
2|2|2|1411
```
