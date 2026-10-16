# Phase P5a.6 证据 — epoch-3 前置补丁 + 首次双门

- 生成时间：2026-09-14T17:31:45+08:00  分支：simple-agent @ 32004eb

## 补丁 1：τ 签名改用 hidden instruction（修单族塌缩）

```
# REQ 级（159 条，sig 来自 hidden instruction 的 md5，无明文）
families: 159 | max share: 0.6%
# epoch-3 arm_choice 的 sig_family 分布（实际路由口径）
families: 135 | samples: 137 | max share: 1.5%
# 验收：族数>=10 且最大族<40% -> PASS
```

## 补丁 2：启用 precedent-assisted 臂

```
# arm_choice 两臂样本
direct|68
precedent-assisted|69
# precedent_injected 的 tokens_injected 上限（验收 <=500）
69|500
# 老 REQ-001 回归：无 tau 专属 span，结构不变
arm_choice/dialogue_turn/tool_scope count = 0
0
```

## 补丁 3：epoch 报告分桶

```
# REQ 分桶分布
{'state-changing': 128, 'read-only': 31}
# epoch-3 分桶通过率
{'state-changing': {'n': 106, 'pass': 74, 'pass_rate': 0.6981, 'avg_tokens': 81761}, 'read-only': {'n': 29, 'pass': 25, 'pass_rate': 0.8621, 'avg_tokens': 58209}}
# 验收：read-only > state-changing -> PASS（86.2% > 69.8%）
```

## epoch-3 运行

```
$ cd backend && python monitor/eval_loop.py --epoch 3 --tau-only --split train --tag tau-
[eval_loop] tau total tokens=10,354,780
[eval_loop] epoch=3 train_loss=36.0
[eval_loop] report -> .agent/reports/tau-epoch-3.json
```

## 三读数（详见 .agent/reports/tau-epoch-3.md 附录）

- 同族 token Δ：epoch2 mean 72,398 → epoch3 76,702，**+4,304（+5.9%）未降反升**（precedent 注入 + 方差）
- arm_value_delta：direct 71.2% / 71,606 token vs precedent-assisted 75.4% / 81,576 token（+4.2pp 换 +9,970 token）
- 分桶通过率：state-changing 69.8%（真实水位）< read-only 86.2%

## 首次双门

```
$ python scripts/epoch_gate.py .agent/reports/tau-epoch-2.json .agent/reports/tau-epoch-3.json
{"decision": "REJECT", "improvement": -0.125, "train_ok": false, "dev_ok": true, "dev_regressions": [], "prev_train_loss": 32.0, "curr_train_loss": 36.0}
```

## 明确不做（本轮）

- 归因命中率（等 replay.py 金种子工厂，另立任务书）
- AUROC2（无 OOD 标签，维持未做）
- updater 提案（等 epoch-3 真实失败样本）
