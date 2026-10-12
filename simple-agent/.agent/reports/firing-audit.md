# 追溯点火审计报告（P5a.55 §二，零 token，静态回放 e1–e8）

**方法**：回放 962 个 τ run 的工具流（不跑模型），逐资产算混淆矩阵。硬线：**对任何 PASS run 点火 = 设计缺陷**。

## 混淆矩阵（每资产）
| 资产 | 该点火(命中死因 FAIL)=救场 | 真实误伤(命中 PASS) | 漏报(死因 FAIL 未点) | 覆盖率 | 硬线(误伤=0) |
|---|---|---|---|---|---|
| `lock_order_v1` | 6 | **118** | 0 | 1.00 | ❌ |
| `repeat_failure_v1` | 0 | 0 | 10 | 0.00 | ✓ |
| `items_count_match_v1` | 1 | 0 | 0 | 1.00 | ✓ |
| `non_delivered_exchange_v1` | 1 | 0 | 1 | 0.50 | ✓ |
| `payment_amount_sum_v1` | 0 | 0 | 4 | 0.00 | ✓ |
| `certificate_update_v1` | 0 | **1** | 0 | — | ❌ |
| `flight_availability_v1` | 0 | 0 | 8 | 0.00 | ✓ |
| `gift_card_balance_v1` | 0 | 0 | 3 | 0.00 | ✓ |

- 总救场（历史 ROI 下界）：**8**。
- 硬线违例：`lock_order_v1`（118）、`certificate_update_v1`（1）。

## 两类误伤（性质不同，必须分开）
1. **certificate_update_v1 — 真缺陷**：误伤 run（PASS）用 `certificate_*` 支付 `update_reservation_flights` 却合法（该类场景允许 certificate，如退款/无费用改签）。→ 谓词**过宽**：须限定为"需**费用**的改签"（amount>0），但 update 的 amount 不在 args（已知覆盖缺口）→ **须回炉重设计**。
2. **lock_order_v1 — 语义歧义（需判据细化）**：118 次"命中 PASS"实为 **否决后重发即通过**（Path B' 的 once-per-order 设计）——每次命中都允许重发。对"合法 items-first（本任务无需改地址）"的点火是**良性再发**，非真误伤。**硬线文字（"对任何 PASS run 点火=缺陷"）对 veto-then-reissue 型守卫过严**；须把判据细化为"**是否会把 PASS 结局改成 FAIL**"（硬阻断）vs"良性再发"。

## 结论（诚实）
- **审计抓到 1 个真缺陷（certificate）+ 1 条判据语义问题（veto-then-reissue）**——这正是"金丝雀证明笼子里对、追溯审计证明历史里对"的价值。
- 覆盖率为 0 的资产（payment/availability/giftcard/repeat）：其死因 FAIL run 里**未出现所需观测信号**（如未先查座位/余额/total），谓词因此不点火——`miss` 是保守行为（不误伤优先），但**历史救场为 0**。
- **暂不批量升级 `field_validated`**：硬线未全清且判据待细化，升级须在（a）certificate 回炉、（b）判据细化（硬阻断 vs 良性再发）之后。

## 待裁 / 下一步
1. **certificate_update_v1 回炉**：窄化为"需费用的改签"，或降级为覆盖外（与 gift_card 同）；
2. **审计判据细化**：对 veto-then-reissue 型守卫，改测"是否改变 PASS 结局"；
3. 细化后重跑审计 → 决定 `field_validated` 升级名单；
4. `verdict_fail` 173 条**不做谓词开采**（能力/歧义型，拦截器拦不出能力）；剩余候选清单见 `final-candidate-list.md`。
