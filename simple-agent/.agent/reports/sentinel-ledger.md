# τ 哨兵台账（自动生成；源 assets.json + firing-audit.json）

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
- 在役 7；field_validated 6；live_confirmed True: lock_order_v1, flight_availability_enforce_v1, gift_card_balance_enforce_v1
- superseded 3；revoked 1

---
## 常设规则（模板页脚，随生成保留）
- **哨兵静默可解性**：接线金丝雀电池全绿后，哨兵不点火的唯一解释是「该模式未发生」，不再是「可能没接线」。
- **50-run 检查点**：累计 50 个哨兵在岗 run 后盘点；届时仍 `live_confirmed=False` 者，二选一呈裁——靶向小批（≤0.3M tokens）或降级休眠（`dormant`：保留注册、退出在岗）。持续静默本身是信息，不许烂尾。
- **出生要件**：可观测性证明 + `naming_proof`（名称匹配守卫须经真实 `execute_tool`、生产命名点火证明）+ 金丝雀电池 + C-1 + 影子模式，一要件不免。
- **治理缺陷类记录**：生成器不得吞掉人工立法注记——立法文本进生成模板的常设页脚，不进数据行（P5a.67 立案）。
