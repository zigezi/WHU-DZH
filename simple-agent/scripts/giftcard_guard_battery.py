#!/usr/bin/env python3
"""P5a.54 C4-1：gift_card_balance_v1 电池（≥5，含阴性对照）。"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from monitor.giftcard_guard import GiftCardBalanceGuard  # noqa: E402

UD = json.dumps({"payment_methods": {"gift_card_1": {"source": "gift_card", "amount": 50},
                                     "credit_card_1": {"source": "credit_card", "id": "credit_card_1"}}})
BOOK = lambda amt: {"payment_methods": [{"payment_id": "gift_card_1", "amount": amt}]}


def probes():
    g = GiftCardBalanceGuard(); g.observe("get_user_details", {}, UD)
    p1 = g.before("book_reservation", BOOK(80))[0] is True
    n1 = g.before("book_reservation", BOOK(40))[0] is False
    n2 = GiftCardBalanceGuard().before("book_reservation", BOOK(80))[0] is False   # 未观测余额
    n3 = g.before("book_reservation", {"payment_methods": [{"payment_id": "credit_card_1", "amount": 999}]})[0] is False
    g4 = GiftCardBalanceGuard(); g4.observe("get_user_details", {}, UD)
    n4 = g4.before("update_reservation_flights", {"reservation_id": "X", "payment_id": "gift_card_1"})[0] is False  # 覆盖外
    p2 = "余额" in (g.before("book_reservation", BOOK(80))[1] or "")
    return [("P1_over_balance_blocks", p1), ("N1_within_balance_passes", n1),
            ("N2_unobserved_passes", n2), ("N3_credit_card_passes", n3),
            ("N4_update_out_of_scope_passes", n4), ("P2_text", p2)]


def main():
    res = [{"probe": n, "pass": bool(p)} for n, p in probes()]
    passed = sum(1 for r in res if r["pass"])
    out = {"note": "gift_card_balance_v1 电池", "n": len(res), "passed": passed,
           "all_pass": passed == len(res), "results": res}
    json.dump(out, open(os.path.join(ROOT, ".agent", "reports", "giftcard-guard-battery.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
