#!/usr/bin/env python3
"""P5a.56 §三：payment_amount_sum_enforce_v1（前置强制型）电池（≥5，含阴性对照）。"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from monitor.payment_guard import PaymentSumGuard  # noqa: E402

TOT = '{"total": 100.00}'
BOOK = lambda amt: {"payment_methods": [{"amount": amt}]}


def probes():
    p1 = PaymentSumGuard(enforce=True).before("book_reservation", BOOK(100))[0] is True  # 无总额观测
    g = PaymentSumGuard(enforce=True); g.observe("get_order_details", {}, TOT)
    n1 = g.before("book_reservation", BOOK(100))[0] is False
    g2 = PaymentSumGuard(enforce=True)
    first = g2.before("book_reservation", BOOK(100))[0]
    second = g2.before("book_reservation", BOOK(100))[0]
    n2 = first is True and second is False
    g3 = PaymentSumGuard(enforce=True); g3.observe("get_order_details", {}, TOT)
    n3 = g3.before("book_reservation", BOOK(50))[0] is True      # 观测且不符 → 拦
    n4 = PaymentSumGuard(enforce=True).before("get_order_details", {})[0] is False
    p2 = "先核对总额" in (PaymentSumGuard(enforce=True).before("book_reservation", BOOK(1))[1] or "")
    return [("P1_no_total_blocks", p1), ("N1_observed_match_passes", n1),
            ("N2_reissue_passes", n2), ("N3_observed_mismatch_blocks", n3),
            ("N4_non_target_passes", n4), ("P2_text", p2)]


def main():
    res = [{"probe": n, "pass": bool(p)} for n, p in probes()]
    passed = sum(1 for r in res if r["pass"])
    out = {"note": "payment_amount_sum_enforce_v1 电池", "n": len(res), "passed": passed,
           "all_pass": passed == len(res), "results": res}
    json.dump(out, open(os.path.join(ROOT, ".agent", "reports", "payment-enforce-battery.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
