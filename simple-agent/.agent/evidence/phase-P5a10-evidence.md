# Phase P5a.10 证据 — POLICY v1 落地 + epoch-4 + 双门

- 生成时间：2026-09-15T17:01:10+08:00  分支：simple-agent @ 1b6e13b

## POLICY v1 应用（人工，单独 commit 1b6e13b）

```
policy_id=174e4c5dfd45 policy_version=worker-policy-v1 chars=706
# 生效子集：P1(修正) / P2 / P4 / P5；P3 作废
# policy_inject span（wiki sha256 证明不触碰）
174e4c5dfd45|worker-policy-v1|d539fd2a46a8b8dd
# wiki 基线：airline=56c335801c16e26b... retail=d539fd2a46a8b8dd...
```

## epoch-4 运行

```
$ python monitor/eval_loop.py --epoch 4 --tau-only --split train --tag tau-
[eval_loop] tau total tokens=10,268,621
[eval_loop] epoch=4 train_loss=33.0
```

## 双门

```
$ python scripts/epoch_gate.py .agent/reports/tau-epoch-3.json .agent/reports/tau-epoch-4.json
{"decision": "MERGE", "improvement": 0.0833, "train_ok": true, "dev_ok": true, "dev_regressions": [], "prev_train_loss": 36.0, "curr_train_loss": 33.0}
```

## 四读数

- 同族 token Δ：mean −638 / median +690（未稳定下降，族间 +17k~−17k）
- arm_value_delta：direct 81.5%/70,557 vs precedent-assisted 70.0%/81,177（direct 反超，臂差属噪声）
- 分桶：state-changing 69.8%→**75.5%**（+5.7pp）；read-only 86.2%→75.9%（n=29 噪声）
- policy cache：epoch-4 hit_ratio **93.9%**；epoch-3 不可比（埋点后置）

## 结论

- POLICY v1 使 train loss 36→33、state-changing 真实水位 +5.7pp，双门 MERGE。
- token 与臂信号未观察到稳定改善（噪声主导），符合 P5a.10 第五节'不预烧逐条臂'的预期。
