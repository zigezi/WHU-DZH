# P5a.56b 落地证据：enforce 原型在役 + payment/giftcard 前置强制型改造

**裁定**：用户批准 enforce 原型进在役，并按原型审计结论将 `payment_sum`/`gift_card` 改造为前置强制型。

## 1. `flight_availability_enforce_v1` → 在役 + field_validated
- credit_level：T1_candidate → **field_validated**（原型审计良性：0 硬线，税 46；电池 6/6 + C-1）。

## 2. 两条前置强制型（新资产，全路径）
| 资产 | 点火（前置强制） | 观测后判定 | 电池 | C-1 |
|---|---|---|---|---|
| `payment_amount_sum_enforce_v1` | book 前无本 run 总额观测 → 否决"先核对总额，重发即通过"（once） | 观测且不符 → 拦 | 6/6 | PASS |
| `gift_card_balance_enforce_v1` | 支付前无本 run 该 gift_card 余额观测 → 否决"先核对余额，重发即通过"（once） | 观测且超额 → 拦 | 6/6 | PASS |

- 均含阴性对照（观测且相符→放行、重发→放行、非目标→放行）。
- worker：`SA_PAYMENT_ENFORCE_GUARD` / `SA_GIFTCARD_ENFORCE_GUARD` 接线（observe + reset）。

## 3. 审计复跑（962 run，干预语义分级）
```
总救场 = 8；硬线违例 = []（all_hardline_zero=True）
benign 税：lock_order 118（12.3%）；avail_enforce 46（4.8%）；payment_enforce 4；giftcard_enforce 2
certificate_update_v1 已撤销 → 移出在役审计
```
- 两型全部良性（0 硬线）；前置强制型把"根本不查"的盲动型死亡纳入兜底（以一步税换）。

## 4. 资产库
- 在役 **10**（+1 撤销，共登记 11）：5 field_validated（lock_order/items_count/non_delivered + avail_enforce）；其余 T1_candidate。
- τ 哨兵模式：日志自然累积；backlog 仪器（B-3/L1.5）在岗。
