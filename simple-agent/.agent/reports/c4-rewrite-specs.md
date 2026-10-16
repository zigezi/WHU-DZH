# C4 拆解重写组 — 案头再审规格（P5a.54 §四.1）

> 状态：**案头规格，未部署**。任一重写须走完整资产路径（规格 → 桌面审查 → 金丝雀≥5含阴性对照 → C-1）方可登记。
> 归属 monitor；Path B' 否决式；干预不改结局（τ reward 不动）。

## C4-1 `gift_card_balance_v1`
- **死因**：用**余额不足**的礼品卡支付（τ 报 "gift card balance is not enough"）。
- **点火规则**：`book_reservation`/`*_payment` 且 `payment_methods` 含 gift_card，其 `amount` **>** 该卡**已知余额**（余额来自先前 `get_user_details` observe）→ 否决。余额未知 → 不拦。
- **干预语义**：否决 + "该礼品卡余额 X < 应付 Y；请改用余额足够的卡或调整金额"。
- **误伤分析（关键）**：**正确拒绝**（用户坚持用不足卡，agent 据实告知"余额不足"）→ 形状相似，**必须靠"agent 正在提交超额支付"与"agent 正在报告不足"区分** → 点火只发生在**支付提交**调用上，不在普通回复上/查询上。
- **阴性对照**：余额充足→放行；未知余额→放行；非支付工具→放行；正确拒绝（无支付调用）→不触发。
- **状态**：待桌面审查（阈值/余额来源口径）。

## C4-2 `flight_availability_v1`
- **死因**：订/改使用**无座**航班（"not enough seats on flight HAT###"）。
- **点火规则**：`book/update_reservation_flights` 使用某 `flight_number`，而**近期**（新鲜度窗口内）该航班的 search 结果标记**不可用/无座** → 否决。**不基于"先前搜过"**（a48 用户裁定），只基于**可用性字段 + 时间戳新鲜度**。
- **干预语义**：否决 + "该航班在最近一次查询中不可用，请重搜可用航班"。
- **误伤分析**：可用性会随时间变；须**新鲜度窗口**（如最近一次 search ≤ 本 run 内 N 步）；窗口外无信号 → 不拦。
- **阴性对照**：可用航班→放行；无新鲜可用性信号→放行；非改签工具→放行。
- **状态**：待桌面审查（需 search 结果含可用性字段；先导数据确认字段名）。

## C4-3 `certificate_update_v1`
- **死因**：用 `certificate_*` 支付**改签**（政策禁止；"certificate cannot be used to update res"）。
- **点火规则**：`update_reservation_*`（**限 update 场景**）且 `payment_id` 以 `certificate_` 开头 → 否决。
- **干预语义**：否决 + "改签不可用 certificate 支付，请用信用卡/礼品卡"。
- **误伤分析**：**正确拒绝**（agent 告知用户"不可用 certificate 改签"）形状相同 → **限定"正在提交 update 且用 certificate 支付"**，排除纯回复。
- **阴性对照**：非 update 工具→放行；信用卡/礼品卡→放行；正确拒绝（无调用）→不触发。
- **状态**：待桌面审查（"update 场景"工具集合界定）。

## 状态（P5a.54 已执行）
- C4-1/2/3 均已电池+C-1+登记（τ=6/7/8）；c4 落地证据见 .agent/evidence/phase-P5a54-C4-evidence.md。

## 流程（逐条）
规格（本文件）→ 桌面审查通过 → 建电池(≥5 含阴性) → C-1 → 登记 `validated_domain=τ`（资产 τ=6,7,8）。
