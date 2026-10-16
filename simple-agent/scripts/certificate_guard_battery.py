#!/usr/bin/env python3
"""P5a.54 C4-3：certificate_update_v1 电池（≥5，含阴性对照）。"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from monitor.certificate_guard import CertificateUpdateGuard  # noqa: E402


def probes():
    G = CertificateUpdateGuard
    return [
        ("P1_update_certificate_blocks",
         G().before("update_reservation_flights",
                    {"reservation_id": "X", "payment_id": "certificate_123"})[0] is True),
        ("N1_update_credit_card_passes",
         G().before("update_reservation_flights",
                    {"reservation_id": "X", "payment_id": "credit_card_1"})[0] is False),
        ("N2_update_gift_card_passes",
         G().before("update_reservation_baggages",
                    {"reservation_id": "X", "payment_id": "gift_card_1"})[0] is False),
        ("N3_book_certificate_passes",   # 非 update 场景
         G().before("book_reservation",
                    {"payment_methods": [{"payment_id": "certificate_1", "amount": 10}]})[0] is False),
        ("N4_non_target_passes",
         G().before("get_reservation_details", {"reservation_id": "X"})[0] is False),
        ("N5_update_no_payment_passes",
         G().before("update_reservation_flights", {"reservation_id": "X", "cabin": "economy"})[0] is False),
        ("P2_text", "不允许用 certificate" in (G().before(
            "update_reservation_flights", {"payment_id": "certificate_9"})[1] or "")),
    ]


def main():
    res = [{"probe": n, "pass": bool(p)} for n, p in probes()]
    passed = sum(1 for r in res if r["pass"])
    out = {"note": "certificate_update_v1 电池", "n": len(res), "passed": passed,
           "all_pass": passed == len(res), "results": res}
    json.dump(out, open(os.path.join(ROOT, ".agent", "reports", "certificate-guard-battery.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
