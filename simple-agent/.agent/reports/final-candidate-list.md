# τ 采收季 · 最后一批待建清单（P5a.55 §三.1）

**结论：无新增可建候选。** 25 条失败开采模式（P5a.36 triage）已全部处置：
- 已部署/收窄：`LOCK_ORDER`（lock_order_v1）、`REPEAT::*`（repeat_failure_v1）；
- 已建电池：items_count_match_v1、non_delivered_exchange_v1、payment_amount_sum_v1；
- 拆解重写已落地：certificate_update_v1、flight_availability_v1、gift_card_balance_v1；
- 驳回：`user_not_found`（任务数据/能力，归负先例册）、`BookReservation.invoke`（实现 bug）。

**不做谓词开采**（a55 §三.2）：`verdict_fail` 173 条 = 能力/歧义型失败大头 → 归负先例语料，非谓词矿。

**采收季收官**：候选耗尽，转入"哨兵模式"（8 资产在岗、日志自然累积、不再主动开挖）。唯一挂起项：`certificate_update_v1` 回炉（firing-audit 真缺陷）+ 审计判据细化（veto-then-reissue）。
