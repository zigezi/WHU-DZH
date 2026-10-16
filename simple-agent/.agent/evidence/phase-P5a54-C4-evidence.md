# P5a.54 C4 三规格落地证据（逐条完整路径）

| 资产 | 点火规则（确定性） | 干预（Path B'） | 电池 | C-1 | 部署域 |
|---|---|---|---|---|---|
| `certificate_update_v1` | `update_reservation_*` 且 `payment_id` 以 `certificate_` 开头 | 否决+改用信用卡/礼品卡 | 7/7 | PASS | τ |
| `flight_availability_v1` | book/update flights 中航班的本 run `available_seats[cabin]` < 乘客数 | 否决+改选有座航班 | 6/6 | PASS | τ |
| `gift_card_balance_v1` | `payment_methods` 中 gift_card 的 `amount` > 本 run 观测余额 | 否决+改用余额足够卡 | 6/6 | PASS | τ |

## 误伤边界（诚实登记）
- `certificate_update_v1`：**限 update 场景**（`update_reservation_*`）；book 用 certificate 合法 → 放行；纯回复（正确拒绝）无调用 → 不触发。
- `flight_availability_v1`：**只基于可用性字段 + 本 run 新鲜度**（guard 每任务 reset），不基于"先前搜过"；未观测/乘客数未知 → 不拦。
- `gift_card_balance_v1`：**覆盖外**——`update_reservation_*` 的应扣金额由工具内部计算、不在 args，确定性前置检查**不可覆盖**该类（A-003 即此类）→ 登记为覆盖外，仅覆盖带 `payment_methods` 金额的调用（book）。

## 接线
worker `execute_tool`：`SA_CERT_GUARD` / `SA_AVAIL_GUARD` / `SA_GIFTCARD_GUARD`；exchange/payment/availability/giftcard 经 `observe(output)` 读状态/座位/余额；每任务 reset；点火记 `interceptor_fire` span。

## 资产库
现役 **τ=8**：lock_order_v1 / repeat_failure_v1 / items_count_match_v1 / non_delivered_exchange_v1 / payment_amount_sum_v1 / certificate_update_v1 / flight_availability_v1 / gift_card_balance_v1。
全部过 金丝雀电池（含阴性对照）+ C-1；B-3 溯源层 b3-v1 记录齐全。
