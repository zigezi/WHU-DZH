# τ 哨兵台账 v3（P5a.61；增 live_confirmed 列，与 assets.json 对齐）

| 资产 | 状态 | 信用 | live_confirmed | 死因 | 型 | 救场 | 覆盖 | 税 |
|---|---|---|---|---|---|---|---|---|
| `lock_order_v1` | active | field_validated | True | lock_order | benign | 6 | 1.0 | 118 |
| `repeat_failure_v1` | active | T1_candidate | — | repeat_failure | benign | 0 | 0.0 | 0 |
| `items_count_match_v1` | active | field_validated | False | syntactic_mismatch | hard | 1 | 1.0 | 0 |
| `non_delivered_exchange_v1` | active | field_validated | False | precondition_unmet | hard | 1 | 0.5 | 0 |
| `flight_availability_enforce_v1` | active | field_validated | True | flight_availability_unchecked | benign | 0 | None | 46 |
| `payment_amount_sum_enforce_v1` | active | field_validated | False | payment_total_unchecked | benign | 0 | None | 4 |
| `gift_card_balance_enforce_v1` | active | field_validated | True | giftcard_balance_unchecked | benign | 0 | None | 2 |
| `flight_availability_v1` | superseded | T1_candidate | — | flight_availability | hard | 0 | 0.0 | 0 |
| `payment_amount_sum_v1` | superseded | T1_candidate | — | numeric_sum | hard | 0 | 0.0 | 0 |
| `gift_card_balance_v1` | superseded | T1_candidate | — | gift_card_balance | hard | 0 | 0.0 | 0 |
| `certificate_update_v1` | revoked | T1_candidate | — | certificate_update | - | - | - | - |

## 汇总
- 在役 7；field_validated 6
- live_confirmed True：lock_order_v1 / flight_availability_enforce_v1 / gift_card_balance_enforce_v1
- live_confirmed False（本批未触发，非失能）：items_count_match_v1 / non_delivered_exchange_v1 / payment_amount_sum_enforce_v1
- 哨兵静默可解性立法：接线电池全绿后，静默=未发生，非失能；累计 50 哨兵 run 后盘点。