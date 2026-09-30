# P5a.19 工单 2 — 零售锁序探针（离线，只读，确定性）

**结论**：锁序为真。`modify_pending_order_items` 会把订单状态改为 `pending (item modified)`，
此后 `modify_pending_order_address` 直接返回 `Error: non-pending order cannot be modified`。
因此**必须先改地址、后改 item**；反之第二动作必然失败，最终 DB 到不了 GT 状态。
R-105 两 epoch 都是 items-first，故两 epoch 均不可赢。**常量，非 e4→e5 变更点。**

## 1. 机制（代码）

- `modify_pending_order_items.invoke` 末行：`order["status"] = "pending (item modified)"`
  （`.agent/vendor/tau-bench/tau_bench/envs/retail/tools/modify_pending_order_items.py:84`）
- `modify_pending_order_address.invoke`：`if order["status"] != "pending": return "Error: non-pending order cannot be modified"`
  （同目录 `modify_pending_order_address.py:25-26`）

## 2. 实证（task 105 的 #W4860251，GT args）

在 retail 原始数据上按两种顺序调用（`load_data()` 深拷贝，互不污染）：

| 顺序 | 第 1 动作 | 第 2 动作 | 终态 |
|---|---|---|---|
| A: address → items（GT 顺序） | address **OK** | items **OK** | `pending (item modified)` |
| B: items → address（R-105 实际顺序） | items **OK** | address **Error: non-pending order cannot be modified** | `pending (item modified)`，地址未改 |

GT 动作顺序（τ-bench task 105）：`... modify_pending_order_address(#W4860251) → modify_pending_order_items(#W4860251)` = 顺序 A。

## 3. 与 R-105 GT 的关系

GT 终态 = 退 Bookshelf(#W8660475) + 退 Backpack(#W9218746) + **改地址** + **改 item**。
顺序 B 下地址改不动 → 终态缺"地址变更" → `data_hash != gt_data_hash` → reward=0。
两 epoch 的 verdict 均为 `FAIL / failed=actions_match`（见 trace.db），与此一致。

## 4. 复现

```bash
cd /root/simple-agent && PYTHONPATH=.agent/vendor/tau-bench .agent/venv/tau/bin/python - <<'PY'
import copy
from tau_bench.envs.retail.data import load_data
from tau_bench.envs.retail.tools.modify_pending_order_address import ModifyPendingOrderAddress as A
from tau_bench.envs.retail.tools.modify_pending_order_items import ModifyPendingOrderItems as I
base=load_data()
def addr(d): return A.invoke(d, order_id="#W4860251", address1="921 Park Avenue", address2="Suite 892",
                             city="Chicago", state="IL", country="USA", zip="60612")
def items(d): return I.invoke(d, order_id="#W4860251", item_ids=["5209958006"],
                              new_item_ids=["8964750292"], payment_method_id="credit_card_2112420")
d=copy.deepcopy(base); print("A addr:",addr(d)[:30]); print("A items:",items(d)[:30])
d=copy.deepcopy(base); print("B items:",items(d)[:30]); print("B addr:",addr(d)[:60])
PY
```
