# Phase 5a.3 证据 — 评判翻译：evaluator → V 层

- 生成时间：2026-09-11T18:03:14+08:00  分支：simple-agent @ 78ff6c8

## 1. 失败 episode：loss>0 且 db_final_state{passed:false}（trace=985905c8-6e64-4b9d-b50e-7169923cc045）

```
$ sqlite3 ... layer='V' WHERE trace_id='985905c8-6e64-4b9d-b50e-7169923cc045'
progress||0|
progress||0|
progress||0|
progress||0|
acceptance_check|db_final_state|0|
verdict|||1.0
```

## 2. GT actions replay 驱动的完美 episode → loss=0（trace=）

```
$ python3 (GT replay probe):
  GT actions: [book_reservation]
  step book_reservation -> done=False obs={"reservation_id": "HATHAT", ...}
  GT replay reward: 1.0 | info: {r_actions: 1.0, gt_data_hash: a825bc53...}
  scoring result: {loss: 0.0, decision: PASS, reward: 1.0, failed: []}
$ sqlite3 ... layer='V' WHERE trace_id=''
```

## 3. replay 零 LLM 成本（StubUser）

- 见 P5a0 evidence §4：calculate_reward 经 StubUser 注桩后 LLM 调用次数 = 0

## 4. REQ JSON 口径

```
{
  "req_id": "TAU-A-000",
  "split": "train",
  "title": "tau-bench airline task 0",
  "task": "你好，我需要帮助",
  "tau_env": "airline",
  "tau_task_id": 0,
  "tau_task_split": "test",
  "assertions": [
    {"name": "db_final_state", "severity": "blocker", "tau": true},
    {"name": "actions_match", "severity": "blocker", "tau": true}
  ],
  "budget": {"max_steps": 30, "max_tokens": 100000, "timeout_s": 900},
  "source": "tau-bench/airline"
}
```
