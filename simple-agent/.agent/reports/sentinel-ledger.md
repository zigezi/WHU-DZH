# τ 哨兵台账 v2（登记册合并后）

> 源：`assets.json`（B-3 **b3-v3**）+ `firing-audit.json`（962 run）。status：active / superseded / revoked。

| 资产 | 状态 | 信用级别 | 死因 | 型 | 电池/C-1 | 救场 | 覆盖 | 税 | 备注 |
|---|---|---|---|---|---|---|---|---|---|
| `lock_order_v1` | active | field_validated | lock_order | benign | ✓ | 6 | 1.0 | 118 | 良性税 12.3% |
| `repeat_failure_v1` | active | T1_candidate | repeat_failure | benign | ✓ | 0 | 0.0 | 0 | 救场 0（依据=金丝雀） |
| `items_count_match_v1` | active | field_validated | syntactic_mismatch | hard | ✓ | 1 | 1.0 | 0 |  |
| `non_delivered_exchange_v1` | active | field_validated | precondition_unmet | hard | ✓ | 1 | 0.5 | 0 |  |
| `flight_availability_enforce_v1` | active | field_validated | flight_availability_unchecked | benign | ✓ | 0 | None | 46 | 前置强制型 |
| `payment_amount_sum_enforce_v1` | active | field_validated | payment_total_unchecked | benign | ✓ | 0 | None | 4 | 前置强制型 |
| `gift_card_balance_enforce_v1` | active | field_validated | giftcard_balance_unchecked | benign | ✓ | 0 | None | 2 | 前置强制型 |
| `flight_availability_v1` | superseded | T1_candidate | flight_availability | hard | ✓ | 0 | 0.0 | 0 | 被 `flight_availability_enforce_v1` 取代 |
| `payment_amount_sum_v1` | superseded | T1_candidate | numeric_sum | hard | ✓ | 0 | 0.0 | 0 | 被 `payment_amount_sum_enforce_v1` 取代 |
| `gift_card_balance_v1` | superseded | T1_candidate | gift_card_balance | hard | ✓ | 0 | 0.0 | 0 | 被 `gift_card_balance_enforce_v1` 取代 |
| `certificate_update_v1` | revoked | T1_candidate | certificate_update | - | ✓ | - | - | - | 已撤销（行为改道型；点火条件不可观测） |

## 汇总（P5a.57 合并后）
- **在役 7**；`field_validated` **6**：lock_order_v1, items_count_match_v1, non_delivered_exchange_v1, flight_availability_enforce_v1, payment_amount_sum_enforce_v1, gift_card_balance_enforce_v1
- 被取代 3 件；撤销 1 件；负先例 213 条
- 硬线违例 **0**；追溯总救场 **8**；良性税合计 170/962 ≈ 17.7%
- 每个死因**单一守卫**（合并消除双重在岗）