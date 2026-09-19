# Phase P5a.7 证据 — updater 消费 epoch-3 失败样本（v1：仅提案，人工审）

- 生成时间：2026-09-15T13:42:50+08:00  分支：simple-agent @ 88000fc

## 运行

```
$ cd backend && python monitor/updater.py ../.agent/reports/tau-epoch-3.json
[updater] 36 proposals -> /root/simple-agent/.agent/proposals/epoch-3-proposal.json
```

## 提案分布（epoch-3 的 36 条 loss>0 样本）

```
epoch: 3 | proposals: 36
by type  : {'threshold_patch': 9, 'prompt_hint': 27}
by target: {'monitor/elayer': 9, 'monitor/llayer': 2, 'SYSTEM_PROMPT': 25}
confidence range: 0.3333 ~ 1.0
```

## 样例（前 5 条）

```
{"type": "threshold_patch", "target": "monitor/elayer", "evidence": ["e48a27b1-7d75-48ea-a920-1fa41b198201", "L002", "C002", "E002"], "suggested_value": null, "confidence": 0.3333, "req_id": "TAU-A-000", "loss": 1.0}
{"type": "prompt_hint", "target": "monitor/llayer", "evidence": ["61a243dc-8740-4e05-9c1f-0162bbcef63a", "L001", "L002", "C002", "E002"], "suggested_value": null, "confidence": 0.6, "req_id": "TAU-A-002", "loss": 1.0}
{"type": "prompt_hint", "target": "SYSTEM_PROMPT", "evidence": ["fc041a8e-e438-4fe3-bc33-36f858d8e2c3", "C002"], "suggested_value": null, "confidence": 1.0, "req_id": "TAU-A-007", "loss": 1.0}
{"type": "threshold_patch", "target": "monitor/elayer", "evidence": ["2f045a6f-14ad-438c-b642-e5b2cce57eae", "C002", "E002"], "suggested_value": null, "confidence": 0.5, "req_id": "TAU-A-008", "loss": 1.0}
{"type": "threshold_patch", "target": "monitor/elayer", "evidence": ["087094f4-a1df-4dbe-be7e-eb971271ac24", "L002", "C002", "E002"], "suggested_value": null, "confidence": 0.3333, "req_id": "TAU-A-009", "loss": 1.0}
```

## v1 铁律

- 本文件只生成提案；代码修改一律人工审阅后手动应用并单独 commit（不自动改代码）
- suggested_value 均为 null：诊断只给方向（目标层/规则），具体取值待人工
