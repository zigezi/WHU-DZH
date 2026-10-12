# P5a.57 落地证据：登记册合并 + 升级 + schema 卫生 + 全生命周期闭环

## §二 登记册合并（3 件 supersede，B-3 → b3-v3）
| 旧资产 | status | superseded_by | 承接条件 |
|---|---|---|---|
| `flight_availability_v1` | **superseded** | flight_availability_enforce_v1 | enforce 版第二段含旧版职责 |
| `payment_amount_sum_v1` | **superseded** | payment_amount_sum_enforce_v1 | **舍入口径等价**：整数分、ROUND_HALF_UP、容差 0.01（证据栏已附等价说明） |
| `gift_card_balance_v1` | **superseded** | gift_card_balance_enforce_v1 | **A-003 覆盖缺口限制随承接转移**（update_* 金额不在 args） |
- B-3 增 `superseded` status + `superseded_by` + `superseded_at`/`reason`；`supersede()`/`patch_asset()` 实现。
- 合并后**每个死因单一守卫**，消除同死因双重点火/双账本。

## §三 两件升级
- `payment_amount_sum_enforce_v1`、`gift_card_balance_enforce_v1` → **field_validated(static)**（电池 6/6 + C-1 + 审计 0 硬线）。

## §四 schema 卫生
- death_cause 由误填的 asset_id 修正为**命名死亡**：`payment_total_unchecked`、`giftcard_balance_unchecked`。

## §五 全生命周期闭环（里程碑）
已执行资产生命每一动词：**开采 → 分诊 → 谓词 → 金丝雀 → C-1 → 部署 → 追溯审计 → 撤销 / 升级 / 合并**。
登记册干净态：**在役 7 / 被取代 3 / 撤销 1 / 负先例 213 / 硬线违例 0**。

## 需知悉（一处数字差异，请仲裁核）
- a57 §三/§五 写"field_validated 共 **5** 件、在役 7（5 件 field_validated）"。
- 实际为 **6 件**：`lock_order_v1`、`items_count_match_v1`、`non_delivered_exchange_v1`、**`flight_availability_enforce_v1`**、`payment_amount_sum_enforce_v1`、`gift_card_balance_enforce_v1`。
- 差异来源：`flight_availability_enforce_v1` 在 **P5a.56b**（你批准"就这么干"）已升 field_validated；a57 的 5 件计法疑未计入它。
- 请指示：**维持 6 件**（承认 56b 的升级），或将 `flight_availability_enforce_v1` 降回 T1_candidate 以对齐 a57 的 5 件。

## 台账
`sentinel-ledger.md` 已更新为合并后状态（在役 7 / 6 field_validated / 3 superseded / 1 revoked）。
