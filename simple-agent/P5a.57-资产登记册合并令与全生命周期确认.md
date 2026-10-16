# P5a.57 — 资产登记册合并令与 τ 免疫系统全生命周期确认

> 触发：P5a.56b 执行完毕（在役 10、撤销 1；审计复跑 962 run，硬线违例 0，良性税负全登记）。裁决人核验 assets.json 原件后发现双重在岗问题。
> 裁决：**本批验收；登记册合并（3 件 supersede）+ 2 件升级 + 1 项 schema 卫生修正。τ 免疫系统全生命周期闭环确认。**

## 一、验收（复跑审计结论采纳）

- 硬线违例 = 0（all_hardline_zero）；总救场 8 维持；良性税负四笔全登记：lock_order 118（12.3%）、avail_enforce 46（4.8%）、payment_enforce 4、giftcard_enforce 2 ✓
- 前置强制型原型验证成立：**把"根本不查"的盲动型死亡纳入兜底**（观测缺失即否决+重发即通过），观测依赖型的天生盲区被补上了 ✓

## 二、登记册卫生：三处双重在岗（核验 assets.json 发现）

enforce 版的第二阶段（"观测且不符 → 拦"）在功能上**包含**观测依赖旧版的全部职责。同一死因两个资产在岗 = 同一次死亡事件可能双重点火、救场账目两本。合并令：

1. `flight_availability_v1` → status=**superseded**（由 flight_availability_enforce_v1 承接）；
2. `payment_amount_sum_v1` → superseded（由 payment_amount_sum_enforce_v1 承接）——**承接条件**：enforce 版第二阶段的判定必须完整携带旧版的舍入口径规格（整数分、ROUND_HALF_UP、容差 0.01），证据栏附一行等价性说明；
3. `gift_card_balance_v1` → superseded（由 gift_card_balance_enforce_v1 承接）——A-003 型覆盖缺口的已登记限制随承接转移，不得随旧版下线而消失。

B-3 schema 增补 status 值 `superseded`（含 superseded_by 字段）。合并后**在役 7 件**，每个死因单一守卫。

## 三、两件升级

payment_amount_sum_enforce_v1、gift_card_balance_enforce_v1：电池 6/6 + C-1 + 审计复跑 0 硬线（税 4 / 2 已登记）→ 升 **field_validated(static)**。至此 field_validated 共 5 件。

## 四、schema 卫生一项

两件 enforce 资产的 death_cause 填的是自己的 asset_id——死因字段应命名死亡（如 `payment_total_unchecked` / `giftcard_balance_unchecked`），修正。出生证字段不是装饰，是 B-3 的检索键。

## 五、全生命周期确认（里程碑登记）

至此 τ 免疫系统已完整执行过资产生命的**每一个动词**：开采 → 分诊 → 谓词 → 金丝雀 → C-1 冷启动 → 部署 → 追溯审计 → **撤销**（certificate）/ **升级**（field_validated）/ **合并**（superseded）。登记册干净态：在役 7（5 件 field_validated）、撤销 1、被取代 3、负先例 213 条、硬线违例 0。

τ 线进入稳态哨兵模式：不主动开挖，干预日志随未来运行自然累积。这正好对上撤退曲线——用户在本流程中的剩余职责仅剩：每周换 token、以及未来某次运行后扫一眼干预日志。

## 六、一句话

**免疫系统成熟的标志不是资产数量，是它学会了死亡之外的三种处置：升级、撤销、合并。登记册从"名录"变成了"家谱"——每个活资产有出生证，每个死资产有死亡证明，每个被取代者有继承记录。**
