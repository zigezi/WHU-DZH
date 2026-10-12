# P5a.54 backlog 仪器落地证据（B-3 溯源层 + L1.5 负先例）

## B-3 溯源层 schema
- `backend/monitor/provenance.py`：`SCHEMA_VERSION=b3-v1`、`REQUIRED_FIELDS`、`ASSET_TYPES`、`validate_asset()`；`register_asset` 强制校验（非法即拒）。
- 文档：`.agent/reports/b3-provenance-schema.md`。
- 现役资产 5 条（均含 validated_domain/credit_level/status/evidence/revalidation_log）：
  `lock_order_v1 / repeat_failure_v1 / items_count_match_v1 / non_delivered_exchange_v1 / payment_amount_sum_v1`（皆 τ，T1_candidate，C-1 PASS）。

## L1.5 负先例仪器（独立警告通道，不注入）
- 表 `negative_precedents`（加入 `trace_store` schema）：{req_id, death_cause, verdict, epoch, plan_json, tokens, created_at}。
- 模块 `backend/monitor/negative_precedent.py`：`add / list_all / count_by_cause`。
- 构建 `scripts/l15_build_negative_precedents.py`（e1–e8 失败轨迹，零 token）：
  **213 条**；by_cause：lock_order 6 / repeat_mutating 8 / tool_error:user not found 13 / not enough seats 5 / 其它 / verdict_fail 173。
- 定位：**与注入层隔离**——负先例不注入运行，仅作"规避已知死法"教具 + 谓词素材（P5a.47）。

## 关系
- 三册分立：**资产（溯源层 assets.json）**、**负结果（negative-results.md）**、**负先例（negative_precedents 表）**。
