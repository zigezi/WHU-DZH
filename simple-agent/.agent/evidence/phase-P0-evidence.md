# Phase P0 证据 — 测量地基（backfill，真实重跑）

- 生成时间：2026-09-11T11:29:11+08:00
- 分支：simple-agent @ 1886aed

## 0.1 code_version 埋点

```
$ sqlite3 -readonly logs/trace.db "SELECT code_version FROM traces ORDER BY start_time DESC LIMIT 1"
1886aed
```

## 0.3 提交接口改 POST（先做，产生一条跨重启的任务）

```
$ curl -s -X POST localhost:8000/task/submit -H "Content-Type: application/json" -d "{\"content\":\"在 workspace 创建 hello.txt 写入 hi\"}"
task_id=ea2e7612-a83c-4b87-94b9-ab599880b9c7
$ curl -s localhost:8000/task/ea2e7612-a83c-4b87-94b9-ab599880b9c7
status= success | tool_calls= 2
$ cat workspace/hello.txt
hi
P0_TASK=ea2e7612-a83c-4b87-94b9-ab599880b9c7
```

## 0.2 任务状态统一入库（kill 重启后 /tasks 仍在）

```
$ curl -s "localhost:8000/tasks?limit=5"   # BEFORE
count= 3
  ea2e7612-a83c-4b87-94b9-ab599880b9c7 success
  f3d24bc2-b173-4c5a-aa7f-5a0e7cfda626 success
  0286a6cd-16a4-4a33-a286-b8a6bfa60e8b success
# kill backend pid=117363
$ curl -s "localhost:8000/tasks?limit=5"   # AFTER restart
count= 3
  ea2e7612-a83c-4b87-94b9-ab599880b9c7 success
  f3d24bc2-b173-4c5a-aa7f-5a0e7cfda626 success
  0286a6cd-16a4-4a33-a286-b8a6bfa60e8b success
$ curl -s localhost:8000/task/ea2e7612-a83c-4b87-94b9-ab599880b9c7  # 重启前的任务仍可查
task_id= ea2e7612-a83c-4b87-94b9-ab599880b9c7 | status= success
```

## 0.4 janitor 保险丝（默认 dry-run）

```
$ python scripts/janitor.py
[janitor] mode=DRY-RUN
[janitor] exited>1h containers: 1
  - 8048ba480e9d backend-api (Exited (0) 2 days ago)
[janitor] workspace files >7d: 0
[janitor] traces >30d: 0
[janitor] done
exit=0
```

## 0.5 任务族复发率统计（决策点）

```
$ python scripts/family_stats.py
[family_stats] total=6 families=5 top_ratio=33.3%
[family_stats] report -> /root/simple-agent/.agent/reports/family-stats.md
Top 族占比 33.3% ≤ 50% → **P3 只做路由表，编译留桩**。
exit=0
```

```
$ cat .agent/reports/family-stats.md
# 任务族复发率统计

- 总任务数：6
- 任务族数：5

| 排名 | 签名 | 数量 | 占比 | 代表任务 |
|---|---|---|---|---|
| 1 | fcfe8120cda2 | 2 | 33.3% | 在 workspace 创建 hello.txt 写入 hi |
| 2 | aaca89deafa6 | 1 | 16.7% | 读取 frontend/index.html 的内容 |
| 3 | dc1d8cd853bb | 1 | 16.7% | 读取 test.txt 文件内容并告诉我 |
| 4 | c7ef7b7f9ba9 | 1 | 16.7% | 读取 workspace 里的 test.txt 文件并告诉我内容 |
| 5 | 97f51999228e | 1 | 16.7% | 在 workspace 创建 smoke.txt 写入 ok |

## 决策结论

Top 族占比 33.3% ≤ 50% → **P3 只做路由表，编译留桩**。
```
