"""P5a.54 C4-1：资产 gift_card_balance_v1 —— 用**已知余额不足**的礼品卡支付。

点火（确定性）：调用参数含 `payment_methods` 列表（如 `book_reservation`），其中某
`payment_id` 为 gift_card 且 `amount` **>** 该卡**本 run 观测余额**（来自 `get_user_details`）→ 否决。
- 余额未知 → 不拦；非礼品卡 → 不拦；无 `payment_methods` 金额 → 不拦。
- **覆盖边界（诚实）**：`update_reservation_*` 的应扣金额由工具内部计算、**不在 args**，
  本谓词**不可确定性地覆盖该类**（登记为覆盖外）。
- 误伤边界：正确拒绝（无支付提交调用）不触发。
"""
import json
from typing import Optional, Tuple


class GiftCardBalanceGuard:
    def __init__(self):
        self._bal = {}   # payment_id -> balance

    def observe(self, tool_name: str, args: dict, output: str):
        if tool_name not in ("get_user_details", "get_user_id_by_email", "find_user_id_by_email"):
            # 余额来自用户详情；其余工具结果忽略
            pass
        if tool_name != "get_user_details":
            return
        try:
            data = json.loads(output) if isinstance(output, str) else output
        except Exception:  # noqa: BLE001
            return
        pms = (data or {}).get("payment_methods")
        if isinstance(pms, dict):
            for pid, pm in pms.items():
                if isinstance(pm, dict) and pm.get("source") == "gift_card" and isinstance(pm.get("amount"), (int, float)):
                    self._bal[pid] = pm["amount"]

    def before(self, tool_name: str, args: dict) -> Tuple[bool, Optional[str]]:
        pms = (args or {}).get("payment_methods")
        if not isinstance(pms, list):
            return False, None
        for p in pms:
            if not isinstance(p, dict):
                continue
            pid, amt = p.get("payment_id"), p.get("amount")
            if isinstance(pid, str) and pid.startswith("gift_card_") and pid in self._bal \
                    and isinstance(amt, (int, float)) and amt > self._bal[pid] + 1e-9:
                return True, (f"GIFTCARD-BALANCE：{pid} 余额 {self._bal[pid]} < 支付额 {amt}。"
                              "请改用余额足够的卡或调整金额。")
        return False, None


guard = GiftCardBalanceGuard()


def reset():
    global guard
    guard = GiftCardBalanceGuard()
    return guard
