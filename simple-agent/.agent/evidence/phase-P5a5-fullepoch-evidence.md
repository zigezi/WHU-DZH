# Phase 5a.5 证据 — 首个完整 train epoch

- 生成时间：2026-09-14T10:34:33+08:00  分支：simple-agent @ 7ffcf66

## 1. 运行

```
$ cd backend && python monitor/eval_loop.py --epoch 2 --tau-only --split train --tag tau-
[eval_loop] tau total tokens=9,773,693
[eval_loop] epoch=2 train_loss=32.0
[eval_loop] report -> .agent/reports/tau-epoch-2.json
```

## 2. 结果

```
entries: 135 | train_loss: 32.0
status: {'success': 134, 'failed': 1}
pass rate: 103/135 = 76.3%
  env A: n=41 pass=31 (75.6%) avg_tokens=59161
  env R: n=94 pass=72 (76.6%) avg_tokens=78171
tokens: total=9,773,693 avg=72,397 min=22,880 max=179,995
cost @¥2/M ≈ ¥19.55
```

## 3. 成本实测 vs 预估

```
5a.4 公式预估：135 × 60,000 = 8,100,000 token ≈ ¥16.2
5a.5 实测    ：9,773,693 token（72,397/任务）≈ ¥19.55
偏差          ：+20.7%（在 50% 阈值内）
```

## 4. 唯一失败任务 TAU-A-009（失败原因 + 修复）

```
error: Unterminated string starting at: line 1 column 13 (char 12)
根因：LLM 偶发产出非法 JSON 工具参数，worker 的 json.loads 未捕获 → 整个任务 failed
修复：worker.py 捕获 JSONDecodeError，回灌 tool error 消息，不崩溃（本次 epoch 后补丁）
```

## 5. precedents / routes

```
precedents: 158
routes: 12
```

## 6. 观察

- DeepSeek-V4 通过率 76.3%，**远高于**任务书预期（0.1~0.25）与 mini-epoch（40%）；官方榜 gpt-4o airline 仅 0.42
- 部分任务 GT 不改变 db（纯查询类），agent 不改状态也可能 reward=1，会抬高通过率（τ-bench 固有性质）
- token 方差大（22k~180k）；τ 任务显著吃 token，批量预算需按实测而非公式
