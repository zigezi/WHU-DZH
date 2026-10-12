# P5a.36 失败开采候选逐条裁决（含误伤分析）

**纪律**（P5a.46 §二 / P5a.48 §八）：谓词只许出生于尸体；逐条走完整路径（点火规则+干预语义+电池≥5含阴性对照+C-1）；**不许批量**。下表 = 25 条候选的三分类。

| 模式 | 次数/证据（run） | 点火规则（确定性） | 干预语义（Path B'） | **误伤分析**（正确拒绝／合理重试／只读） | 建议 |
|---|---|---|---|---|---|
| `LOCK_ORDER::modify_items_first` | 7（R-041/058/072/098/105…） | 首个 modify_items 前同 oid 未成功改地址 | 否决+提示先地址后物品 | 单步改 item、已改地址 → 不撞 | **已部署**（lock_order_v1），不重复 |
| `REPEAT::tau__get_order_details` | 39（R-002/005/006/020…） | 同 (tool,**同 args**) 失败≥2 | 否决+换方法 | **原候选"同工具≥3"过宽**：读多张不同订单=合法；收窄为 **identical-args** 后不撞 | **已收窄并部署**（repeat_failure_v1） |
| `REPEAT::get_reservation_details` | 16（A-002/003/005/015…） | 同上 | 同上 | 同上（不同 reservation_id=合法） | 已收窄部署 |
| `REPEAT::search_direct_flight` | 11（A-000/002/008…） | 同上 | 同上 | 换日/换航点=不同 args，不撞 | 已收窄部署 |
| `REPEAT::get_product_details` | 6 | 同上 | 同上 | 同上 | 已收窄部署 |
| `REPEAT::tau__calculate` | 5 | 同上 | 同上 | 数值运算合理重试多因输入不同，不撞 | 已收窄部署 |
| `REPEAT::search_onestop_flight` | 3 | 同上 | 同上 | 同上 | 已收窄部署 |
| `REPEAT::update_reservation_flights` | 3 | 同上 | 同上 | 改签参数不同=合法重试，不撞 | 已收窄部署 |
| `REPEAT::return_delivered_order_items` | 2 | 同上 | 同上 | 退不同订单=合法 | 已收窄部署 |
| `REPEAT::book_reservation` | 1 | 同上 | 同上 | 极少 | 已收窄部署 |
| `ERR::user not found` | 15（R-000/034/036/038…） | find_user_* 返回该串 | 无（**不应干预**） | **正确拒绝/正确报告"查无此人"=合法行为**，谓词会打正确行为 | **驳回**（归任务数据缺陷/GT 不一致，走 harness 筛查，非资产） |
| `ERR::not enough seats (HAT290/229/213)` | 8（A-015/003/000） | book/update 使用**先前 search 标不可用**的航班 | 否决+要求重搜可用航班 | 可用性可能变化；正确行为=先查可用。轻度误伤（合法改签） | **拆解重写**（需先导数带可用性字段） |
| `ERR::gift card balance is not enough` +`not enough balance in payment` | 5（A-003/023/033/022） | gift_card 余额 < 应付额（据 get_user_details） | 否决+换支付/降额 | **正确拒绝**（用户坚持礼品卡但余额不足）会被撞 | **拆解重写**（需余额上下文；先导确认） |
| `ERR::payment amount does not add up` | 4（A-009/000/008×2） | 支付的 payment 金额之和 ≠ total（工具返回可算） | 否决+要求 `tau__calculate` 复核 | 舍入/口径差异风险；正确加总不撞 | **建电池**（数值工具化 L1 的代码化） |
| `ERR::non-delivered order cannot be exchanged` | 2（R-019/074） | exchange_* on status≠delivered 的订单 | 否决+先查订单状态 | 正确行为=先查状态；低误伤 | **建电池** |
| `ERR::the number of items to be exchanged should match` | 1（R-076） | `len(item_ids)≠len(new_item_ids)` | 否决+要求等长 | 几乎无误伤（纯参数形状） | **建电池**（最易确定性） |
| `ERR::certificate cannot be used to update res` | 1（A-033） | update_reservation_* 用 `certificate_*` 支付 | 否决+换支付 | 正确拒绝（政策禁止）形状相同，需限定"update 场景" | **拆解重写** |
| `ERR::BookReservation.invoke() got an unexpected` | 1（A-008） | 工具签名异常 | 无 | **实现缺陷**（非 agent 死法） | **驳回**（归代码 bug） |

## 汇总
- **已部署/已收窄**：`LOCK_ORDER` + 全部 `REPEAT::*`（收窄为 identical-args）→ 资产 `lock_order_v1`、`repeat_failure_v1`。
- **建议建电池（可确定性、低误伤）**：`payment amount does not add up`、`non-delivered order cannot be exchanged`、`number of items to be exchanged should match`。
- **建议拆解重写（需先导数据/上下文确认）**：`not enough seats`（可用性字段）、`gift card balance`（余额+正确拒绝边界）、`certificate ... update`（限定场景）。
- **建议驳回（非 agent 死法）**：`user not found`（任务数据缺陷）、`BookReservation.invoke() unexpected`（实现 bug）。
- 无一条被"批量放行"；建电池者逐条走 **谓词+干预语义+电池(含阴性对照)+C-1**（如 a48 §八）。
