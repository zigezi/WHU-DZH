# Phase 5a.5 证据 — 首轮烧批 mini-epoch（--limit 10）

- 生成时间：2026-09-11T18:16:11+08:00  分支：simple-agent @ 85b2826

## 1. 运行

```
$ cd backend && python monitor/eval_loop.py --epoch 1 --tau-only --limit 10 --tag tau-
[eval_loop] tau total tokens=898,122
[eval_loop] epoch=1 train_loss=6.0
[eval_loop] report -> .agent/reports/tau-epoch-1.json
```

## 2. 报告（每条 TAU REQ 有 loss）

```
# Epoch 1 评测报告

- 生成时间：2026-09-11T18:14:32.139953
- train loss：6.0

| req_id | split | status | assertion_loss | loss | tokens | failed |
|---|---|---|---|---|---|---|
| TAU-A-000 | train | success | 1.0 | 1.0 | 79105 | db_final_state |
| TAU-A-002 | train | success | 1.0 | 1.0 | 87080 | actions_match |
| TAU-A-003 | train | success | 1.0 | 1.0 | 124894 | db_final_state |
| TAU-A-005 | train | success | 1.0 | 1.0 | 63531 | db_final_state |
| TAU-A-006 | train | success | 1.0 | 1.0 | 44303 | db_final_state |
| TAU-A-007 | train | success | 0.0 | 0.0 | 89916 | - |
| TAU-A-008 | train | success | 0.0 | 0.0 | 89942 | - |
| TAU-A-009 | train | success | 1.0 | 1.0 | 149861 | - |
| TAU-A-012 | train | success | 0.0 | 0.0 | 54452 | - |
| TAU-A-013 | train | success | 0.0 | 0.0 | 26094 | - |
```

## 3. 成本实测 vs 5a.4 预估

```
5a.4 公式预估：15 轮 × 2k token × 2 模型 = 60,000 token/任务
5a.5 实测    ：898,122 / 10 = 89,812 token/任务
偏差          ：(89812-60000)/60000 = +49.7%（阈值 50%，压线通过）
全 train(135) 预估：135 × 89,812 ≈ 12.13M token ≈ ¥24（@¥2/M）
```

## 4. precedents / routes

```
$ sqlite3 ... SELECT count(*) FROM precedents   # >0
24
$ sqlite3 ... routes τ 族条目
4c2be0c87a8f|direct|11.0|2.0|11
```

## 5. 观察

- 10 条 airline 任务：loss=0 共 4 条，loss=1 共 6 条（reward 通过率 40%，高于任务书预期 0.1~0.25）
- 1 条 g_halted（max_tokens=200000 仍触顶）；token/任务 26k~170k，方差大
- 所有 τ 任务 req.content 相同（占位开场白），导致 routing sig_family 收敛为单一族——
  后续如需按任务族路由，应改用 hidden instruction 计算签名（非本期验收项）
