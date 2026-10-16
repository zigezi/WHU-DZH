#!/usr/bin/env python3
"""P5a.54 C4-2：flight_availability_v1 电池（≥5，含阴性对照）。"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from monitor.availability_guard import FlightAvailabilityGuard  # noqa: E402

SEARCH_FEW = json.dumps([{"flight_number": "HAT1", "available_seats": {"economy": 1, "business": 0}}])
SEARCH_MANY = json.dumps([{"flight_number": "HAT1", "available_seats": {"economy": 10, "business": 5}}])
BOOK = {"cabin": "economy", "passengers": [{"first_name": "A"}, {"first_name": "B"}, {"first_name": "C"}],
        "flights": [{"flight_number": "HAT1"}]}


def probes():
    g = FlightAvailabilityGuard(); g.observe("search_direct_flight", {}, SEARCH_FEW)
    p1 = g.before("book_reservation", BOOK)[0] is True

    g2 = FlightAvailabilityGuard(); g2.observe("search_direct_flight", {}, SEARCH_MANY)
    n1 = g2.before("book_reservation", BOOK)[0] is False

    n2 = FlightAvailabilityGuard().before("book_reservation", BOOK)[0] is False   # 未观测

    n3 = FlightAvailabilityGuard().before("get_flight_status", {})[0] is False
    g4 = FlightAvailabilityGuard(); g4.observe("search_direct_flight", {}, SEARCH_FEW)
    n4 = g4.before("update_reservation_flights", {"cabin": "economy", "flights": [{"flight_number": "HAT1"}]})[0] is False  # 乘客数未知
    p2 = "请改选有座航班" in (g.before("book_reservation", BOOK)[1] or "")
    return [("P1_few_seats_blocks", p1), ("N1_enough_passes", n1), ("N2_unobserved_passes", n2),
            ("N3_non_target_passes", n3), ("N4_unknown_pax_passes", n4), ("P2_text", p2)]


def main():
    res = [{"probe": n, "pass": bool(p)} for n, p in probes()]
    passed = sum(1 for r in res if r["pass"])
    out = {"note": "flight_availability_v1 电池", "n": len(res), "passed": passed,
           "all_pass": passed == len(res), "results": res}
    json.dump(out, open(os.path.join(ROOT, ".agent", "reports", "availability-guard-battery.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
