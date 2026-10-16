# P5a.48 资产批次证据：REPEAT 回归修正 + 三条新资产（顺序立法）

## 1. REPEAT 回归修正（部署后电池修订，零 token）
- 用户指出的漏格：**两次同参失败之间若发生状态变更成功**（modify 失败×2 → 改地址成功 → 同参 modify 本会成功），谓词不该拦。
- 修法：`repeat_guard.after` 在**任意状态变更成功后清零全部计数**（只读成功仅清本键）。
- 新增阴性对照 **N4_state_change_resets_no_block**；电池 **7/7**；**C-1 复跑 PASS**（回归电池）。

## 2. 三条新资产（按用户顺序：items_count_match → non_delivered_exchange → payment_amount_sum）
| 资产 | 点火规则 | 干预（Path B'） | 电池 | C-1 |
|---|---|---|---|---|
| `items_count_match_v1` | `len(item_ids)≠len(new_item_ids)`（纯句法） | 否决+要求等长 | 6/6（含 N1等长/N2非目标/N3缺键/N4空等长） | PASS |
| `non_delivered_exchange_v1` | exchange_* 且**已知**订单 status≠delivered | 否决+先确认状态 | 6/6（含 N1 delivered/N2未知状态/N3非目标/N4状态更新后放行） | PASS |
| `payment_amount_sum_v1` | 已知 total 且 `sum(支付额)≠total`（**整数分**、容差 **1 分**） | 否决+要求确定性工具复核 | 6/6（含 N1相符/N2未知total/N3舍入恰好/N4非目标） | PASS |

- **payment 舍入口径规格**（先于实现）：全部转整数分、ROUND_HALF_UP、容差 0.01 元。
- worker 接线：`SA_COUNT_GUARD` / `SA_EXCHANGE_GUARD` / `SA_PAYMENT_GUARD`；exchange/payment 通过 `observe(output)` 读状态/总额；每任务 reset。

## 3. gift_card_balance 包含关系（用户指定核查）
- 实测 5 次 `gift card balance is not enough` 所在调用**无同参重复**（`repeated_payment_identical=0`）→ **不被 REPEAT 覆盖** → 维持"**拆解重写**"队列（挂起，待首轮电池全过后再审）。

## 4. 资产库状态
- 部署资产 **τ=5**：`lock_order_v1`、`repeat_failure_v1`、`items_count_match_v1`、`non_delivered_exchange_v1`、`payment_amount_sum_v1`（各过电池 + C-1）。
- 发热比 ~30:5。拆解重写组（gift_card_balance / not_enough_seats / certificate_update）**挂起**。
