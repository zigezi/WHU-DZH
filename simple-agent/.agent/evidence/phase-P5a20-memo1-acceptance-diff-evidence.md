# P5a.20 便签 1 实施证据 — acceptance_check 携带 GT-vs-final 字段级 diff

**依据**：P5a.20 §三.1 批准的便签 1。

## 1. 交付

| 文件 | 变更 |
|---|---|
| `backend/requirements/adapters/tau/diff.py` | 新增：纯函数 `data_diff` / `actions_diff`（有界、可测） |
| `backend/requirements/adapters/tau/sidecar.py` | `rpc_reward` 增快照 + diff |
| `backend/requirements/adapters/tau/scoring.py` | diff 字段写入 `acceptance_check` + `verdict`；修 outputs 分支遮蔽 `r_actions` |
| `scripts/p5a20_memo1_selftest.py` | 4 项纯函数自测 |

## 2. 行为

`rpc_reward` 现在返回：
```
info = {
  "r_actions": bool, "gt_data_hash": str, "agent_data_hash": str,
  "data_diff": [{entity,id,field,gt,agent}...] (≤30, 可 truncated),
  "actions_diff": {"missing":[...], "extra":[...]} (≤20),
  ...res.info 原字段（r_outputs / outputs）
}
```
- **顺序风险已处理**：`calculate_reward()` 会把 `env.data` 覆盖为 GT 终态；现在在其**之前** `copy.deepcopy(env.data)` + 记录 `agent_hash`。
- **修既有缺陷**：原 `_assertions_from_info` 在带 outputs 的任务上会丢失 `r_actions`（info 被 `RewardOutputInfo` 替换）；现两字段独立判断，`db_final_state` 与 `actions_match` 均落 span。

`scoring.score_tau_episode` 把 `gt_data_hash/agent_data_hash/data_diff/actions_diff/outputs` 并入每条 `acceptance_check` 与 `verdict` span（有界）。

## 3. 验证

```
$ /root/miniconda3/envs/mini-agent/bin/python scripts/p5a20_memo1_selftest.py
  t1 actions_missing OK -> ['modify_pending_order_address']   # R-105 items-first 场景
  t2 actions_extra   OK -> ['return_delivered_order_items']
  t3 data_diff       OK -> orders #W4860251.address gt=Chicago agent=Seattle
  t4 bounded         OK -> 6 entries, truncated=True
ALL PASS
$ PYTHONPATH=.agent/vendor/tau-bench .agent/venv/tau/bin/python -c "import sidecar, diff"
sidecar+diff import OK in tau venv
```

## 4. 生效条件 / 注意

- **需重启 sidecar**（当前 pid 1371676 为旧代码）；按测量路径管制，**在 epoch-6 启动时重启**，不提前动运行中的仪器。
- `actions_diff` 用 `(name, canonical_kwargs)` 精确匹配，偶发参数字段差异会记为 missing/extra（供人工判读，非判决）。
- 红线：diff 只含 DB 层 GT（动作/字段/hash），不含 hidden instruction。

## 5. 与既有裁决的关系

- 直接落地 P5a.16 §五.5「acceptance_check 必须携带 GT-vs-final diff」。
- 为隔离集工具与后续 FAIL 归因自动化提供字段；不再需要人工逐条推断"为什么 FAIL"。
