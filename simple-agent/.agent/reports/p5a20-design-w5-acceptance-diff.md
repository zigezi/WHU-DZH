# 设计便签 1（工单 5）— acceptance_check 携带 GT-vs-final 字段级 diff

**依据**：P5a.20 §三.1（批准便签，设计≠实施；交审后动手）
**目标**：FAIL 归因不再靠人工；V 层 span 自带"哪个字段/哪个动作不匹配"。

## 1. 现状缺口

- `backend/requirements/adapters/tau/scoring.py:12-21` `_assertions_from_info`：只从 `info` 读 `r_actions` / `r_outputs`（布尔）。
- sidecar `rpc_reward`（`sidecar.py:137-150`）返回 `info = res.info.model_dump()`：
  - 无 outputs 的任务 → `RewardActionInfo{r_actions, gt_data_hash}`；
  - 有 outputs 的任务 → **`info` 被替换为 `RewardOutputInfo{r_outputs, outputs}`，`r_actions` 丢失**。
- 结论：现有 span 无字段级信息；且 outputs 分支遮蔽了 db 检查。三案复查全靠人工推断。

## 2. 设计

### 2.1 sidecar 侧：计算 diff（不改评测语义，只增加信息）
`rpc_reward` 内，在调用 `env.calculate_reward()` **之前**先快照 agent 终态
（**关键顺序风险**：`base.py:133-137` 会 `self.data = data_load_func()` 覆盖为 GT 并 step，之后 env.data=GT 终态）：

```
agent_data    = copy.deepcopy(env.data)
agent_actions = list(env.actions)          # 含 RESPOND
res           = env.calculate_reward()      # 现有逻辑不动
gt_data       = env.data                     # calculate_reward 后即 GT 终态
info = {
  "r_actions": bool, "gt_data_hash": str, "agent_data_hash": str,
  "r_outputs": bool|None, "outputs": {str: bool},
  "data_diff": [...],            # 有界：仅变更实体，最多 N=30 条
  "actions_missing_gt": [...],   # GT 动作中 agent 未做的（按规范化签名比对）
  "actions_extra": [...],        # agent 做过、GT 未含的 DB 变更动作
}
```

- `data_diff` 粒度：`{entity: orders|users|products, id, field, gt, agent}`。
  比较用 `agent_data` vs `gt_data`，只输出**值不等**的字段。
- `actions_missing_gt` / `actions_extra`：按 `(name, canonical_kwargs)` 集合差；
  脱敏：只保留动作名 + 关键 id（order_id/reservation_id/user_id/item_ids），不落 instruction。
- 有界化：diff 超限截断并记 `truncated:true` + `total_changed`，防 span 膨胀。

### 2.2 scoring 侧：写进 span
`score_tau_episode` 把上述字段并入 `acceptance_check`（及 `verdict`）的 attributes：
`data_diff`、`actions_missing_gt`、`actions_extra`、`outputs`。**保留**现有 `name/passed/severity/source` 字段不变（向后兼容）。

### 2.3 兼容
- `_assertions_from_info`：优先用 `r_actions`（若存在），不再因 outputs 分支丢失 db 检查 → 同时输出 `db_final_state` 与 `actions_match` 两条 check。
- 旧 span 不受影响（新字段可选）。

## 3. 红线
- 新字段只含 **DB 层 GT（动作名/args/实体字段）**，不含 hidden instruction 明文 → 符合 P5a.20 §二 tracked 层。
- GT action args 可能含人名/订单号（DB 数据），非 instruction，允许入库。

## 4. 验证（实施时）
1. 单元：构造 R-105 items-first 轨迹，断言 `actions_missing_gt` 含 `modify_pending_order_address`，`data_diff` 含 `#W4860251.address`。
2. 单元：构造 A-008 1 乘客轨迹，断言 `data_diff` 含 `reservation.passengers` 差异 + `outputs` 缺项。
3. 回归：对 A-019（无 outputs）确认 `r_actions` 与 `r_outputs=null` 均落 span。

## 5. 工作量与风险
- 改动：`sidecar.py`（+~40 行）、`scoring.py`（+~15 行）、1 测试。中低风险；唯一硬点是 §2.1 的快照顺序。
