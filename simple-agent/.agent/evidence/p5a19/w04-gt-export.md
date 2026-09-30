# P5a.19 工单 4 — 三案 GT 原文导出与判定（离线，只读）

> **红线处理**：P5a.6/P5a.9 规定 hidden instruction 明文禁入 evidence 文件。
> 本文件只收录 **GT actions / outputs / 评测语义**（DB 层 ground truth）与**派生结论**；
> instruction 明文另存**未跟踪**文件 `.agent/local/p5a19-gt-instructions.md`（`.gitignore` 命中 `.agent/*`），供仲裁者查阅。
> 该文件**不得提交**。若需将 instruction 明文写入仓库证据，请仲裁者显式覆盖红线。

## 0. 评测语义（`tau_bench/envs/base.py:124-164`）

```
data_hash = hash(agent 最终 data)
重置 data → 逐步执行 GT actions → gt_data_hash = hash(GT 最终 data)
r_actions = (data_hash == gt_data_hash)      # 不是动作序列匹配，是【最终 DB 状态哈希】相等
if 有 outputs: 要求 agent 的 RESPOND 文本包含每个 output 子串（小写、去逗号后子串匹配）
reward = 1.0 仅当 r_actions 且 outputs 全中
```

**推论**：改序、多余动作、缺失动作**都通过最终 DB 状态**体现；"actions_match" 与 "db_final_state" 在 tau 奖励层同源。
一个**多余但会改 DB** 的动作（如多退一件）同样致 FAIL。

## 1. TAU-A-008（airline test #8）

GT actions（2）：
```
cancel_reservation   {reservation_id: K1NW8N}
book_reservation     {user_id: mohamed_silva_9265, origin: JFK, destination: SFO,
                      flight_type: round_trip, cabin: business,
                      flights: [HAT023 2024-05-26, HAT204 2024-05-28, HAT100 2024-05-28],
                      passengers: [Mohamed Silva, Raj Sanchez, Liam Wilson],   # ← 3 人
                      payment_methods: [certificate_3765853:500, gift_card_8020792:198,
                                        gift_card_6136092:129, credit_card_2198526:1786],
                      total_baggages:0, nonfree_baggages:0, insurance:no}
```
outputs：`['327','1000','1786']`（最终回复须含这三个数）

| epoch | trace | verdict | 说明 |
|---|---|---|---|
| 4 | 2b4917e1… | **PASS** reward=1 | 订 3 人，DB 与 outputs 均中 |
| 5 | f854dfb5… | FAIL reward=0 `failed=actions_match` | 只订 1 人 → DB 状态 ≠ GT |

**派生判定**：GT 明确要求 **3 名乘客**；e5 模拟器答"just Mohamed"，与 GT 矛盾 → e5 此后不可赢。
P5a.16 §2.1 断点 2（模拟器违背 GT）**证实**。

## 2. TAU-A-019（airline test #19）

GT actions（3）：
```
get_reservation_details  {VA5SGQ}
update_reservation_flights {VA5SGQ, cabin: economy,
                            flights: [HAT169 2024-05-17, HAT033 2024-05-19],  # ← 返程 05-19
                            payment_id: credit_card_8003957}
update_reservation_baggages {VA5SGQ, total_baggages:1, nonfree_baggages:1, payment_id: credit_card_8003957}
```
outputs：`[]`（无输出子串要求）

| epoch | trace | verdict |
|---|---|---|
| 4 | f80ea911… | FAIL `failed=db_final_state` |
| 5 | 594bcfc2… | FAIL `failed=db_final_state` |

**派生判定**：GT 返程为 **HAT033 / 2024-05-19**，航点 **DTW→JFK**。
- e4 模拟器改口返程日期（与 GT/DB 的 5/19 不一致）；
- e5 模拟器要求 **DTW–LGA** 直飞（GT 是 JFK），且库中不存在该直飞 → 模拟器随后放弃任务。
两 epoch 模拟器发言均与 GT 不一致 → 任务结构上不可赢。P5a.16 §2.2 **证实**。

## 3. TAU-R-105（retail test #105）

GT actions（4）：
```
return_delivered_order_items {#W8660475, item_ids:[8479046075], payment_method_id: credit_card_2112420}   # Bookshelf
return_delivered_order_items {#W9218746, item_ids:[7824298782], payment_method_id: credit_card_2112420}   # Backpack
modify_pending_order_address {#W4860251, 921 Park Avenue/Suite 892, Chicago, IL, 60612}
modify_pending_order_items   {#W4860251, item_ids:[5209958006] → [8964750292], payment_method_id: credit_card_2112420}
```
outputs：`['286422338955']`（"cancelled order 的 tracking number"，回复须含该串）

| epoch | trace | verdict |
|---|---|---|
| 4 | ca1ff8d1… | FAIL `failed=actions_match` |
| 5 | fa73670f… | FAIL `failed=actions_match` |

**派生判定（修正 P5a.16 §2.3）**：
- GT **含** Backpack 退货（#W9218746 / 7824298782）→ P5a.16"GT 动作列表无 backpack"**证伪**。
- 真正的缺口在另一处：instruction 还要求退一件 **Jigsaw Puzzle**（该商品确在 Lucas 的 delivered 订单里），
  但 **GT actions 未包含**该退货 → **instruction ⊋ GT actions**。因评测是最终 DB 状态相等，
  跟随 instruction 去退 jigsaw 会**多改 DB → FAIL**。属**任务定义级缺陷**（tau-bench GT/instruction 不一致）。
- 另有锁序常量（见 w02）：items-first → 地址改不动 → FAIL。
- outputs 要求 tracking 串 `286422338955`，是第三重硬约束。

## 4. 复现

```bash
cd /root/simple-agent && PYTHONPATH=.agent/vendor/tau-bench .agent/venv/tau/bin/python - <<'PY'
import dataclasses
from tau_bench.envs.airline.tasks_test import TASKS as AT
from tau_bench.envs.retail.tasks_test import TASKS_TEST as RT
for label,T,i in [("A-008",AT,8),("A-019",AT,19),("R-105",RT,105)]:
    d=dataclasses.asdict(T[i])
    print(label,"outputs",d['outputs']); [print("  ",a.name,a.kwargs) for a in d['actions']]
PY
# instruction 明文：见未跟踪文件 .agent/local/p5a19-gt-instructions.md
```
