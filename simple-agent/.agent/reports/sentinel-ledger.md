# τ 哨兵台账（在役资产 + 信用级别 + 覆盖/税负）

> 数据源：`assets.json`（B-3 溯源层）+ `firing-audit.json`（962 run 追溯审计）。
> mode：**benign**=否决后重发即通过（点火 PASS 记税）；**hard**=行为改道型（点火 PASS=硬线）。

| 资产 | 状态 | 信用级别 | 域 | 死因 | 型 | 电池/C-1 | 历史救场 | 覆盖率 | 税(点火PASS) | 备注 |
|---|---|---|---|---|---|---|---|---|---|---|
| `lock_order_v1` | active | field_validated | tau | lock_order | benign | ✓ | 6 | 1.0 | 118 | 良性税 12.3% |
| `repeat_failure_v1` | active | T1_candidate | tau | repeat_failure | benign | ✓ | 0 | 0.0 | 0 | 救场 0（部署依据=金丝雀，非历史匹配） |
| `items_count_match_v1` | active | field_validated | tau | syntactic_mismatch | hard | ✓ | 1 | 1.0 | 0 |  |
| `non_delivered_exchange_v1` | active | field_validated | tau | precondition_unmet | hard | ✓ | 1 | 0.5 | 0 | 覆盖 0.50 |
| `payment_amount_sum_v1` | active | T1_candidate | tau | numeric_sum | hard | ✓ | 0 | 0.0 | 0 | 观测依赖盲区（死因 run 无所需观测） |
| `flight_availability_v1` | active | T1_candidate | tau | flight_availability | hard | ✓ | 0 | 0.0 | 0 | 观测依赖盲区（死因 run 无所需观测） |
| `gift_card_balance_v1` | active | T1_candidate | tau | gift_card_balance | hard | ✓ | 0 | 0.0 | 0 | 观测依赖盲区（死因 run 无所需观测） |
| `flight_availability_enforce_v1` | active | field_validated | tau | flight_availability_unchecked | benign | ✓ | 0 | None | 46 | 前置强制型原型 |
| `payment_amount_sum_enforce_v1` | active | T1_candidate | tau | payment_amount_sum_enforce_v1 | benign | ✓ | 0 | None | 4 | 前置强制型原型 |
| `gift_card_balance_enforce_v1` | active | T1_candidate | tau | gift_card_balance_enforce_v1 | benign | ✓ | 0 | None | 2 | 前置强制型原型 |
| `certificate_update_v1` | revoked | T1_candidate | tau | certificate_update | - | ✓ | - | - | - | **已撤销**（行为改道型误伤；点火条件不可观测） |

## 汇总
- **在役 10（+1 撤销，共登记 11）**；其中 `field_validated` **4** 个：lock_order_v1, items_count_match_v1, non_delivered_exchange_v1, flight_availability_enforce_v1。
- 硬线违例：**0**（仅已撤销的 certificate 曾有 1）；追溯总救场：**8**（lock_order 6 / items_count 1 / non_delivered 1）。
- 税负合计（benign）：lock_order 118 + avail_enforce 46 + payment_enforce 4 + giftcard_enforce 2 = 170/962 ≈ 17.7%（含重复）。
- 模式：τ **哨兵模式**——日志自然累积，不再主动开挖；backlog 仪器（B-3 溯源层 / L1.5 负先例 213 条）在岗。