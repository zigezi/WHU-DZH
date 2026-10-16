# Phase P5a.11 Part 2 证据 — epoch-5 复制实验

- 生成时间：2026-09-16T14:33:58+08:00  分支：simple-agent @ 489fa15

## 冻结复核（开跑前）

```
$ git diff --stat 482b629..HEAD -- backend/   # 期望空
(空 = 冻结成立)
$ policy_id
174e4c5dfd45
```

## epoch-5 运行

```
$ python monitor/eval_loop.py --epoch 5 --tau-only --split train --tag tau-
[eval_loop] tau total tokens=9,986,663
[eval_loop] epoch=5 train_loss=33.0
```

## 双门

```
$ epoch_gate tau-epoch-4.json tau-epoch-5.json  -> {"decision": "REJECT", "improvement": 0.0, "train_ok": false, "dev_ok": true, "dev_regressions": [], "prev_train_loss": 33.0, "curr_train_loss": 33.0}
$ epoch_gate tau-epoch-3.json tau-epoch-5.json  -> {"decision": "MERGE", "improvement": 0.0833, "train_ok": true, "dev_ok": true, "dev_regressions": [], "prev_train_loss": 36.0, "curr_train_loss": 33.0}
```

## 六项读数

- state-changing：e3 69.8% / e4 75.5% / e5 **71.7%**（均在 [70,80]）
- read-only：e3 86.2% / e4 75.9% / e5 89.7%
- arm_value_delta：direct 76.8%/75,320 vs precedent-assisted 74.2%/72,569（三样本 direct 赢 2 次，臂差噪声）
- cache hit_ratio：e4 **93.9%** / e5 **93.9%**（持平）
- 同族 token Δ（e5-e4）：mean **-2,089** / median -197
- FP-4 复跑：e4 p99=174,967/>150k=5 → e5 p99=168,574/>150k=4（尾部继续收窄）
- 成本：e5 9,986,663 token

## 预注册判读

- epoch-5 state-changing = 71.7% ∈ [70%,80%] → **效应复制成功，POLICY v1 坐实为确认资产**（解锁第 2 代资产生命周期）。
- 张力记录：Part 1 指纹 FP-1/FP-2/FP-5 弱或数据不足 → 效应**可复制**成立，但**归因到具体规则**开放（预注册不做消融）。

## 明确不做（维持）

不做消融；不换模型；不动 guard 阈值与 reward 权重；不应用新提案；threshold_patch 冻结。
