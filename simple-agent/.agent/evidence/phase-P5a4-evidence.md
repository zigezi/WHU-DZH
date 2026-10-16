# Phase 5a.4 证据 — 批量入库与分族

- 生成时间：2026-09-11T18:04:51+08:00  分支：simple-agent @ 2d988ea

## 1. ingest 运行

```
$ python scripts/tau_ingest.py
[tau_ingest] raw=165 dropped=6 written=159 (train=135, dev=24) est_tokens=9,540,000 est_cost=¥19.08
[tau_ingest] report -> /root/simple-agent/.agent/reports/tau-ingest.md
```

## 2. 报告数字 == 文件数

```
$ ls backend/requirements/tau/ | wc -l
159
$ (loader) tau req count / dev count
tau: 159 dev: 24
```

## 3. 抽 3 条 REQ（人工可读）

```
--- TAU-A-000 ---
{
  "req_id": "TAU-A-000",
  "split": "train",
  "title": "tau-bench airline task 0",
  "task": "你好，我需要帮助",
  "tau_env": "airline",
  "tau_task_id": 0,
  "tau_task_split": "test",
  "assertions": [
    {
      "name": "db_final_state",
      "severity": "blocker",
      "tau": true
    },
    {
      "name": "actions_match",
      "severity": "blocker",
      "tau": true
    }
  ],
  "budget": {
    "max_steps": 30,
    "max_tokens": 100000,
    "timeout_s": 900
  },
  "source": "tau-bench/airline",
  "sig": "12fd37c8c41a"
}--- TAU-R-090 ---
{
  "req_id": "TAU-R-090",
  "split": "dev",
  "title": "tau-bench retail task 90",
  "task": "你好，我需要帮助",
  "tau_env": "retail",
  "tau_task_id": 90,
  "tau_task_split": "test",
  "assertions": [
    {
      "name": "db_final_state",
      "severity": "blocker",
      "tau": true
    },
    {
      "name": "actions_match",
      "severity": "blocker",
      "tau": true
    }
  ],
  "budget": {
    "max_steps": 30,
    "max_tokens": 100000,
    "timeout_s": 900
  },
  "source": "tau-bench/retail",
  "sig": "004aa3724e69"
}--- TAU-R-063 ---
{
  "req_id": "TAU-R-063",
  "split": "train",
  "title": "tau-bench retail task 63",
  "task": "你好，我需要帮助",
  "tau_env": "retail",
  "tau_task_id": 63,
  "tau_task_split": "test",
  "assertions": [
    {
      "name": "db_final_state",
      "severity": "blocker",
      "tau": true
    },
    {
      "name": "actions_match",
      "severity": "blocker",
      "tau": true
    }
  ],
  "budget": {
    "max_steps": 30,
    "max_tokens": 100000,
    "timeout_s": 900
  },
  "source": "tau-bench/retail",
  "sig": "013533982f76"
}```

## 4. 成本预估（双模型口径）与实测校准点

- 公式口径：159 × 15 轮 × 2000 token × 2 ≈ 9.54M token ≈ ¥19.08
- **实测校准**：5a.1 单条 airline 任务 agent 侧 ~103k token / 21 轮（远超 2k/轮）。
  按 ~130k token/任务估，159 条 ≈ 20M+ token/epoch，成本显著高于公式口径，接近 ¥50/日上限。
- **闸门：需人工确认后才许进 5a.5。**
