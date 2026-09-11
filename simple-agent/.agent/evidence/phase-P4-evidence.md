# Phase P4 证据 — 进化闭环 v1：半自动

- 生成时间：2026-09-11T11:46:27+08:00
- 分支：simple-agent @ 48ba9e2

## ⛔ MR-3 闸门复查（两条前置硬条件）

```
$ sqlite3 -readonly logs/trace.db "SELECT json_extract(attributes,\$.effect_diff) FROM spans WHERE layer=E ... LIMIT 3"
{"created":["smoke.txt"],"modified":[],"deleted":[]}
{"created":[],"modified":[],"deleted":[]}
{"created":["hello.txt"],"modified":[],"deleted":[]}
$ ls -la .agent/reports/decomposition-report.md
-rw-r--r-- 1 root root 655 Sep 11 11:45 .agent/reports/decomposition-report.md
```

## 6.1 epoch 评测器（--limit 1）

```
$ cd backend && python monitor/eval_loop.py --epoch 1 --limit 1
(真实 API 调用，产出如下)
$ cat .agent/reports/epoch-1.json
{
  "epoch": 1,
  "generated_at": "2026-09-11T11:45:19.902096",
  "base_url": "http://localhost:8000",
  "train_loss": 0.0037,
  "entries": [
    {
      "req_id": "REQ-001",
      "split": "train",
      "title": "创建文本文件并写入内容",
      "task": "在 workspace 中创建 hello.txt，并写入内容 hi",
      "status": "success",
      "task_id": "d6159896-77ee-4479-8d65-270518427fd7",
      "assertion_loss": 0,
      "loss": 0.0037,
      "tokens": 2246,
      "failed": []
    }
  ]
}```

## 6.2 影子实例 8002 启停（pidmap PID 必须与监听 PID 一致；8000 不受影响）

```
$ bash scripts/shadow.sh start shadow-test
[shadow] started pid=124079 port=8002 branch=shadow-test
$ cat .agent/pidmap.json
{"port":8002,"pid":124079,"branch":"shadow-test","dir":"/root/simple-agent/.agent/worktrees/shadow","started_at":"2026-09-11T11:46:33+08:00"}
$ ss -tlnp | grep :8002
LISTEN 0      2048         0.0.0.0:8002      0.0.0.0:*    users:(("python3",pid=124079,fd=9)) 
$ curl -s localhost:8002/
{"service":"mini-agent-v2","status":"running","endpoints":["/task/submit","/task/{id}","/tasks","/metrics"]}
$ bash scripts/shadow.sh stop
[shadow] stopped pid=124079 port=8002
$ ss -tlnp | grep :8002   # want empty
(empty)
$ ss -tlnp | grep :8000   # 8000 不受影响
LISTEN 0      2048         0.0.0.0:8000      0.0.0.0:*    users:(("python",pid=122685,fd=9))  
```

## 6.3 更新器（只生成提案，不动代码）

```
$ python backend/monitor/updater.py .agent/reports/epoch-1.json
[updater] 1 proposals -> /root/simple-agent/.agent/proposals/epoch-1-proposal.json
$ cat .agent/proposals/epoch-1-proposal.json
{
  "epoch": 1,
  "generated_at": "2026-09-11T11:46:35.317868",
  "note": "v1：仅生成提案，需人工审阅后手动应用并单独 commit",
  "source_report": "epoch-1.json",
  "proposals": [
    {
      "type": "prompt_hint",
      "target": "unknown",
      "evidence": [
        "d6159896-77ee-4479-8d65-270518427fd7"
      ],
      "suggested_value": null,
      "confidence": 0.0,
      "req_id": "REQ-001",
      "loss": 0.0037
    }
  ]
}```

## 6.4 双门 merge + 早停

```
$ python scripts/epoch_gate.py /tmp/prev.json /tmp/curr_merge.json   # 应 MERGE
{"decision": "MERGE", "improvement": 0.1, "train_ok": true, "dev_ok": true, "dev_regressions": [], "prev_train_loss": 10.0, "curr_train_loss": 9.0}
$ python scripts/epoch_gate.py /tmp/prev.json /tmp/curr_reject.json  # 应 REJECT
{"decision": "REJECT", "improvement": 0.1, "train_ok": true, "dev_ok": false, "dev_regressions": ["REQ-008"], "prev_train_loss": 10.0, "curr_train_loss": 9.0}
$ python scripts/epoch_gate.py --history /tmp/flat1.json /tmp/flat2.json /tmp/flat3.json  # 收敛
CONVERGED -> /root/simple-agent/.agent/reports/convergence.md
```
