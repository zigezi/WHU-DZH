#!/usr/bin/env python3
"""P5a.48：payment_amount_sum_v1 电池（≥5，含阴性对照；整数分/容差 1 分）。"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from monitor.payment_guard import PaymentSumGuard  # noqa: E402

TOT = '{"total": 100.00, "order_id": "#W1"}'


def probes():
    g = PaymentSumGuard(); g.observe("get_order_details", {}, TOT)
    p1 = g.before("book_reservation", {"payment_methods": [{"amount": 60}, {"amount": 30}]})[0] is True

    g2 = PaymentSumGuard(); g2.observe("get_order_details", {}, TOT)
    n1 = g2.before("book_reservation", {"payment_methods": [{"amount": 60}, {"amount": 40}]})[0] is False

    n2 = PaymentSumGuard().before("book_reservation", {"payment_methods": [{"amount": 1}]})[0] is False  # total 未知

    g3 = PaymentSumGuard(); g3.observe("get_order_details", {}, TOT)
    n3 = g3.before("book_reservation", {"payment_methods": [
        {"amount": 33.33}, {"amount": 33.33}, {"amount": 33.34}]})[0] is False   # 整数分恰好 100.00

    n4 = PaymentSumGuard().before("get_user_details", {"payment_methods": [{"amount": 1}]})[0] is False

    g5 = PaymentSumGuard(); g5.observe("get_order_details", {}, TOT)
    p2 = "整数分" in (g5.before("book_reservation", {"payment_methods": [{"amount": 50}]})[1] or "")
    return [("P1_sum_mismatch_blocks", p1), ("N1_sum_match_passes", n1),
            ("N2_unknown_total_passes", n2), ("N3_rounding_exact_passes", n3),
            ("N4_non_target_passes", n4), ("P2_text", p2)]


def main():
    res = [{"probe": n, "pass": bool(p)} for n, p in probes()]
    passed = sum(1 for r in res if r["pass"])
    out = {"note": "payment_amount_sum_v1 电池", "n": len(res), "passed": passed,
           "all_pass": passed == len(res), "results": res}
    json.dump(out, open(os.path.join(ROOT, ".agent", "reports", "payment-guard-battery.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
