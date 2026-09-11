# Phase P-1 证据 — 环境前置（开工闸门）

- 生成时间：2026-09-11T11:27:28+08:00
- 分支：simple-agent @ c6bcdd4

## 1. MR-6：删除无源 convergence.md

```
$ ls -la .agent/reports/
total 12
drwxr-xr-x 2 root root 4096 Sep 11 11:24 .
drwxr-xr-x 7 root root 4096 Sep 11 11:24 ..
-rw-r--r-- 1 root root  474 Sep 11 09:38 family-stats.md
```

## 2. .gitignore 例外自证（git check-ignore）

```
$ git check-ignore -v .agent/evidence/phase-P-1-evidence.md .agent/reports/decomposition-report.md .agent/proposals/epoch-1-proposal.json
# (无输出 = 未被忽略，例外生效)
$ git check-ignore -v .agent/worktrees/x .agent/logs/x.log
.gitignore:16:.agent/*	.agent/worktrees/x
.gitignore:16:.agent/*	.agent/logs/x.log
```

## 3. 进程/端口清理

```
$ ss -tlnp | grep -E ":8000|:8001|:8002"
LISTEN 0      2048         0.0.0.0:8000      0.0.0.0:*    users:(("python",pid=116766,fd=9))  
```

## 4. .env 加载链 + worker 缺 key 大声退出（key 已脱敏，仅显示长度）

```
$ python -c "import worker; print(\"worker import OK; key_len =\", len(worker.DEEPSEEK_API_KEY))"
worker import OK; key_len = 35
```

## 5. 后端健康

```
$ curl -s localhost:8000/
{"service":"mini-agent-v2","status":"running","endpoints":["/task/submit","/task/{id}","/tasks","/metrics"]}
```

## 6. 冒烟任务：真实 LLM + 工具调用

```
$ curl -s -X POST localhost:8000/task/submit -H "Content-Type: application/json" -d "{\"content\":\"在 workspace 创建 smoke.txt 写入 ok\"}"
task_id=0286a6cd-16a4-4a33-a286-b8a6bfa60e8b (见下方任务详情)
$ curl -s localhost:8000/task/0286a6cd-16a4-4a33-a286-b8a6bfa60e8b
{
    "task_id": "0286a6cd-16a4-4a33-a286-b8a6bfa60e8b",
    "status": "success",
    "created_at": "2026-09-11T11:27:07.586397",
    "created_at_ts": 1789097227.586397,
    "finished_at": "2026-09-11T11:27:11.682115",
    "result": "\u5df2\u521b\u5efa `smoke.txt`\uff0c\u5185\u5bb9\u4e3a `ok`\uff082 \u5b57\u7b26\uff09\uff0c\u5e76\u5df2\u8bfb\u53d6\u9a8c\u8bc1\u3002",
    "error": null,
    "duration_ms": 4114.0336990356445,
    "llm_tokens": 2163,
    "content": "\u5728 workspace \u521b\u5efa smoke.txt \u5199\u5165 ok",
    "steps": [
        {
            "type": "tool_call",
            "tool_name": "write_file",
            "args": {
                "path": "smoke.txt",
                "content": "ok"
            },
            "success": true,
            "output": "Successfully wrote 2 chars to smoke.txt",
            "error": "",
            "duration_ms": 4.2552947998046875
        },
        {
            "type": "tool_call",
            "tool_name": "read_file",
            "args": {
                "path": "smoke.txt"
            },
            "success": true,
            "output": "File: smoke.txt\nSize: 2 chars\n---\nok",
            "error": "",
            "duration_ms": 3.2351016998291016
        }
    ],
    "tool_calls_count": 2,
    "req_id": null
}
$ cat workspace/smoke.txt
ok
```

## 7. trace 含真实 tool_call / E 层 span

```
$ sqlite3 -readonly backend/logs/trace.db "SELECT layer,type,name,status FROM spans WHERE trace_id='0286a6cd-16a4-4a33-a286-b8a6bfa60e8b' ORDER BY start_time"
L|task|任务编排|success
L|step|步骤1|success
C|llm_call|LLM推理|success
T|tool_call|write_file|success
E|sandbox_exec|write_file|success
L|step|步骤2|success
C|llm_call|LLM推理|success
T|tool_call|read_file|success
E|sandbox_exec|read_file|success
L|step|步骤3|success
C|llm_call|LLM推理|success
O|observability|埋点自检|success
```

## 8. effect_diff / code_version

```
$ sqlite3 -readonly backend/logs/trace.db "SELECT count(*) FROM spans WHERE trace_id='0286a6cd-16a4-4a33-a286-b8a6bfa60e8b' AND layer='E' AND json_extract(attributes,'$.effect_diff') IS NOT NULL"
2
$ sqlite3 -readonly backend/logs/trace.db "SELECT code_version FROM traces ORDER BY start_time DESC LIMIT 1"
c6bcdd4
```
