# Phase P2 证据 — G 层：刹车 + A 段观测（backfill，真实重跑）

- 生成时间：2026-09-11T11:36:53+08:00
- 分支：simple-agent @ 88d3f4e

## 4.2 熔断状态机：死循环任务第 3 次重复 → g_halted，token < 40% 预算

```
$ POST /task/submit {req_id: REQ-004}  -> task_id=ce32101f-b9a9-4bc7-9a8e-0d11ed3260a7
$ curl -s localhost:8000/task/ce32101f-b9a9-4bc7-9a8e-0d11ed3260a7
status= g_halted | llm_tokens= 2445 | tool_calls= 3 | 40%_budget= 12000.0
$ steps (3 次相同 read_file 调用)
  1 read_file {"path": "no_such_file_12345.txt"} success= False
  2 read_file {"path": "no_such_file_12345.txt"} success= False
  3 read_file {"path": "no_such_file_12345.txt"} success= False
$ sqlite3 -readonly logs/trace.db "SELECT type, json_extract(attributes,'$.reason') FROM spans WHERE trace_id='ce32101f-b9a9-4bc7-9a8e-0d11ed3260a7' AND layer='G' ORDER BY start_time"
feedback_injected|
feedback_response|
circuit_break|repeat
feedback_injected|
```

## 4.3 shell 白名单：5 条注入测试（G 层 permission_check span 齐全）

```
$ python3 - "6eeeb6f9-0c4d-42c6-9136-05af035e00e1"  # 直接调用真实 guard（trace_id=6eeeb6f9-0c4d-42c6-9136-05af035e00e1，真实 trace）
BLOCKED | 'rm -rf /' -> Command blocked by guard: 写命令路径越出 workspace: '/'
BLOCKED | 'rm ../backend/main.py' -> Command blocked by guard: 写命令路径越出 workspace: '../backend/main.py'
BLOCKED | 'sqlite3 logs/trace.db "DELETE FROM traces"' -> Command blocked by guard: sqlite3 必须带 -readonly（防止篡改 trace.db）
BLOCKED | 'cat $(pwd)/x' -> Command blocked by guard: 命令替换 $()/反引号一律拒绝
ALLOWED | 'echo hi > a.txt'
$ sqlite3 ... permission_check spans
rm -rf /|deny|写命令路径越出 workspace: '/'
rm ../backend/main.py|deny|写命令路径越出 workspace: '../backend/main.py'
sqlite3 logs/trace.db "DELETE FROM traces"|deny|sqlite3 必须带 -readonly（防止篡改 trace.db）
cat $(pwd)/x|deny|命令替换 $()/反引号一律拒绝
rm -rf /|deny|写命令路径越出 workspace: '/'
rm ../backend/main.py|deny|写命令路径越出 workspace: '../backend/main.py'
sqlite3 logs/trace.db "DELETE FROM traces"|deny|sqlite3 必须带 -readonly（防止篡改 trace.db）
cat $(pwd)/x|deny|命令替换 $()/反引号一律拒绝
```

## 4.0 A 段观测 1：effect_diff 非空且三键齐全

```
$ sqlite3 -readonly logs/trace.db "SELECT json_extract(attributes,'$.effect_diff') FROM spans WHERE layer='E' AND json_extract(attributes,'$.effect_diff') IS NOT NULL LIMIT 3"
{"created":["smoke.txt"],"modified":[],"deleted":[]}
{"created":[],"modified":[],"deleted":[]}
{"created":["hello.txt"],"modified":[],"deleted":[]}
$ 三键齐全计数（has_created|has_modified|has_deleted|count）
1|1|1|26
```

## 4.0 A 段观测 2：feedback_injected / feedback_response 存在（见 4.2 的 G span）

## 4.0 A 段观测 3：shell span 含非空 exit_code

```
$ sqlite3 -readonly logs/trace.db "SELECT name, exit_code, stdout_tail ..."
run_command|0|total 24
drwxr-xr-x 3 root root 4096 Sep
```

## 4.2 预算一致性代码修正（worker.py 循环上界）

```
$ grep -n "step_ceiling" backend/worker.py
219:        step_ceiling = min(budget["max_steps"], MAX_STEPS)
225:                            "applied": step_ceiling},
227:        for step in range(step_ceiling):
```
