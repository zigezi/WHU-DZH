# P5a.20 便签 3 实施证据 — 测量模式 precedent 选择器

**依据**：P5a.20 §三.1 批准的便签 3；修 P5a.19 工单 1/3 证据（恒取最新=上一任务）。

## 1. 交付

| 文件 | 变更 |
|---|---|
| `backend/monitor/precedent_select.py` | 新增：纯函数 `select`（同族+最早 id）/`content_hash`/`summary_of` |
| `backend/monitor/trace_store.py` | 新增 `precedent_snapshots` 表 + `freeze_precedent_snapshot` / `list_precedent_snapshot` |
| `backend/worker.py` | `_inject_precedent` 改用新选择器（同族/快照/最早 id/无则 `precedent_skip`）；臂选择支持 `ROUTER_MODE=measurement`；测量模式不更新 Thompson |
| `backend/monitor/routing.py` | 新增 `choose_measurement`（确定性 50/50） |
| `scripts/freeze_precedents.py` | epoch 开始冻结先例快照 |
| `scripts/p5a20_memo3_selftest.py` | 4 项自测 |

## 2. 行为

- **选择器**：`select(candidates, sig_family)` = 同族中 **id 最小**（最早沉积）；无同族 → `None` → 记 `precedent_skip` span（不注入无关内容）。
- **快照**：`SA_EPOCH=<N>` 时读 `precedent_snapshots[epoch=N]`（epoch 开始冻结，=先前 epoch 沉积）；无快照回退 `live`。
- **content_hash**：`precedent_injected` span 增 `content_sha256_16` / `content_chars` / `precedent_req` / `source`，供跨 epoch 字节相等断言。
- **臂分配**：`ROUTER_MODE=measurement` → `choose_measurement(task_id)` 确定性 50/50，且**不** `router.update`（测量与学习分离，治 F1 选择偏差）。

## 3. 验证

```
$ /root/miniconda3/envs/mini-agent/bin/python scripts/p5a20_memo3_selftest.py
  t1 same-family->oldest OK id= 10
  t2 no same-family -> None OK
  t3 content_hash OK 655305ce9cadaf19
  t4 measurement 50/50 OK: 107/200 precedent-assisted, deterministic
ALL PASS
$ py_compile worker/routing/trace_store/precedent_select/freeze_precedents  -> OK
```

## 4. 运行口径（重要）

| 运行 | 环境变量 | 是否注入 | 目的 |
|---|---|---|---|
| epoch-6（干净基线） | `ROUTER_MODE=measurement`，**direct-only**（不选 precedent 臂） | 否 | 摆脱坏臂污染，重测真实 direct 水位（P5a.20 §三.2） |
| epoch-7（命题一） | `ROUTER_MODE=measurement`，`SA_EPOCH=7`，先 `freeze_precedents --epoch 7` | 是（新选择器） | 固定 50/50 回答"沉积物是否有用" |

- 前置：**重启 sidecar**（便签1 已改 `rpc_reward`，当前进程为旧码）。
- epoch-6 不需 `SA_EPOCH`（不注入）；epoch-7 需先冻结快照。

## 5. 注意

- **行为变更**：未设 `SA_EPOCH` 时，生产路径的选择器也从"恒取最新"变为"同族最早"（修复，但属测量路径变更，已随本便签签字）。
- 若 epoch-7 前某族无**先前**沉积 → 该任务 `precedent_skip`（诚实记录为"无可注入"），而非注入无关内容。
