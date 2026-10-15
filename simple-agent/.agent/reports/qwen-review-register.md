# Qwen3.8-Max 二审档案（P5a.82 §七.3）

> 二审（reviewer 试用期）finding 登记：**产出永远是假设**，执行方验证回执后方可立法（LR-5）。

## 正面积分（finding 被采纳/确认）
- **finding 1（DC-9 层级绕过）** → 验证令 §四 → **确认成立**（QB-2 真）：`_guard_production` 原名仅在 `register_asset()`；`set_credit/shadow_event/patch_asset/supersede/revoke/revalidate` 全走无守卫 `_save()`。修法：守卫**下沉 I/O 层** `_save(d, allow_production)`，一切写路径必经之；`scripts/provenance_guard_battery.py` 17/17（沙盒可写 / 生产缺省拒 / 显式授权允许）。
- **finding 3（采集误判洪水 + 过滤方案骨架）** → 与 opencode 自抓缺陷收敛 → **立法采纳**为 `filter_oplog_v1`（a82 §三）。

## 负面积分（假阳性 / 误读）
- **QB-1（语言语义假阳性）**：主张 `r[9] or "unknown"` 对空串返回 `""`。**事实**：`"" or "unknown"` → `"unknown"`（空串 falsy）。其"修复"`r[9] if r[9] else "unknown"` 与原式**语义等价**。→ 不改代码；登记为首条二审校准数据。
- **finding 5（状态误读）**：称"本次提交涉及显式授权例外推送"。**事实**：该轮本地未推送（RL-3 默认）。警戒方向已由用户直裁关闭（§六）。低危，登记。

## 校准结论
- 信噪：1 项新高危确认 + 1 项立法采纳（正） vs 1 假阳性 + 1 状态误读（负）。
- 评委会判定：**有价值，二审试用期上岗**（a82 §一）。
- 用途校准点：语言语义类主张先零 token 证伪（LR-5）；架构类主张走验证令流程。
