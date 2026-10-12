#!/usr/bin/env python3
"""P5a.56 §三：gift_card_balance_enforce_v1（前置强制型）电池（≥5，含阴性对照）。"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from monitor.giftcard_guard import GiftCardBalanceGuard  # noqa: E402

UD = json.dumps({"payment_methods": {"gift_card_1": {"source": "gift_card", "amount": 50}}})
BOOK = lambda amt: {"payment_methods": [{"payment_id": "gift_card_1", "amount": amt}]}


def probes():
    p1 = GiftCardBalanceGuard(enforce=True).before("book_reservation", BOOK(10))[0] is True  # 无余额观测
    g = GiftCardBalanceGuard(enforce=True); g.observe("get_user_details", {}, UD)
    n1 = g.before("book_reservation", BOOK(40))[0] is False
    g2 = GiftCardBalanceGuard(enforce=True)
    first = g2.before("book_reservation", BOOK(10))[0]
    second = g2.before("book_reservation", BOOK(10))[0]
    n2 = first is True and second is False
    g3 = GiftCardBalanceGuard(enforce=True); g3.observe("get_user_details", {}, UD)
    n3 = g3.before("book_reservation", BOOK(80))[0] is True      # 观测且超额 → 拦
    n4 = GiftCardBalanceGuard(enforce=True).before("book_reservation",
                                                   {"payment_methods": [{"payment_id": "credit_card_1", "amount": 1}]})[0] is False
    p2 = "先核对余额" in (GiftCardBalanceGuard(enforce=True).before("book_reservation", BOOK(1))[1] or "")
    return [("P1_no_balance_blocks", p1), ("N1_observed_within_passes", n1),
            ("N2_reissue_passes", n2), ("N3_observed_over_blocks", n3),
            ("N4_credit_card_passes", n4), ("P2_text", p2)]


def main():
    res = [{"probe": n, "pass": bool(p)} for n, p in probes()]
    passed = sum(1 for r in res if r["pass"])
    out = {"note": "gift_card_balance_enforce_v1 电池", "n": len(res), "passed": passed,
           "all_pass": passed == len(res), "results": res}
    json.dump(out, open(os.path.join(ROOT, ".agent", "reports", "giftcard-enforce-battery.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
