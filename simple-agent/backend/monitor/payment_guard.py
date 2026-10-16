"""P5a.48：资产 payment_amount_sum_v1 —— 含**舍入口径规格**（整数分、容差 0.01）。

口径规格（先于实现立法）：
- 全部金额转**整数分**比较；四舍五入 ROUND_HALF_UP；
- 容差 = 0.01 元（1 分）；|sum(payment amounts) - total| > 1 分 → 否决。
点火：即将 book_reservation（带 payment_methods）且**已知 total** 而金额和不符 → 否决。
total 未知 → 不拦（避免误判）。total 由先前工具结果 observe（含 "total" 字段）。
"""
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Tuple

TARGET = "book_reservation"
SYNTHETIC = ("PAYMENT-SUM：支付金额之和与应付总额不符（按整数分、容差 1 分）。"
             "请用确定性工具核对金额后再提交。")
_TOTAL_RE = re.compile(r'"total"\s*:\s*"?([0-9]+(?:\.[0-9]+)?)"?')


def to_cents(x) -> int:
    return int((Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)) * 100)


class PaymentSumGuard:
    def __init__(self, tol_cents: int = 1, enforce: bool = False):
        self.tol = tol_cents
        self.enforce = enforce          # 前置强制型（P5a.56 §三）
        self._vetoed = set()
        self._total = {}    # order_scope -> total cents（用 user_id 或最近 total）

    def observe(self, tool_name: str, args: dict, output: str):
        s = str(output or "")
        m = _TOTAL_RE.search(s)
        if m:
            try:
                self._total["_last"] = to_cents(m.group(1))
            except Exception:  # noqa: BLE001
                pass

    def before(self, tool_name: str, args: dict) -> Tuple[bool, Optional[str]]:
        if tool_name != TARGET:
            return False, None
        total = self._total.get("_last")
        if self.enforce and total is None:      # 前置强制：无本 run 总额观测 → 否决（once）
            if "book" not in self._vetoed:
                self._vetoed.add("book")
                return True, ("NO-OBS：本 run 尚未确认应付总额。请先核对总额，"
                              "然后重新发起本调用即通过。")
            return False, None                  # 重发即通过（良性）
        if total is None:
            return False, None            # 未知 total → 不拦
        pms = (args or {}).get("payment_methods")
        if not isinstance(pms, list) or not pms:
            return False, None
        try:
            s = sum(to_cents(p.get("amount", 0)) for p in pms if isinstance(p, dict))
        except Exception:  # noqa: BLE001
            return False, None
        if abs(s - total) > self.tol:
            return True, SYNTHETIC
        return False, None


guard = PaymentSumGuard()
guard_enforce = PaymentSumGuard(enforce=True)


def reset():
    global guard, guard_enforce
    guard = PaymentSumGuard()
    guard_enforce = PaymentSumGuard(enforce=True)
    return guard
