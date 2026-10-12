#!/usr/bin/env python3
"""P5a.56 §三：flight_availability_enforce_v1（前置强制型试产原型）电池（≥5，含阴性对照）。"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from monitor.availability_guard import FlightAvailabilityGuard  # noqa: E402

FEW = json.dumps([{"flight_number": "HAT1", "available_seats": {"economy": 1}}])
MANY = json.dumps([{"flight_number": "HAT1", "available_seats": {"economy": 10}}])
BOOK = {"cabin": "economy", "passengers": [{"n": 1}, {"n": 2}, {"n": 3}],
        "flights": [{"flight_number": "HAT1"}]}


def probes():
    # P1：无本 run 观测 → 否决（前置强制）
    p1 = FlightAvailabilityGuard(enforce=True).before("book_reservation", BOOK)[0] is True
    # N1：已观测且座位充足 → 放行
    g = FlightAvailabilityGuard(enforce=True); g.observe("search_direct_flight", {}, MANY)
    n1 = g.before("book_reservation", BOOK)[0] is False
    # N2：无观测被否决一次后，重发即通过（once-per-key 良性再发）
    g2 = FlightAvailabilityGuard(enforce=True)
    first = g2.before("book_reservation", BOOK)[0]
    second = g2.before("book_reservation", BOOK)[0]
    n2 = first is True and second is False
    # N3：观测到座位不足（n>seats）→ 否决（原规则）
    g3 = FlightAvailabilityGuard(enforce=True); g3.observe("search_direct_flight", {}, FEW)
    n3 = g3.before("book_reservation", BOOK)[0] is True
    # N4：非目标工具 → 放行
    n4 = FlightAvailabilityGuard(enforce=True).before("get_flight_status", {})[0] is False
    p2 = "先 search 确认有座" in (FlightAvailabilityGuard(enforce=True).before("book_reservation", BOOK)[1] or "")
    return [("P1_no_obs_blocks", p1), ("N1_observed_enough_passes", n1),
            ("N2_reissue_passes", n2), ("N3_observed_few_blocks", n3),
            ("N4_non_target_passes", n4), ("P2_text", p2)]


def main():
    res = [{"probe": n, "pass": bool(p)} for n, p in probes()]
    passed = sum(1 for r in res if r["pass"])
    out = {"note": "flight_availability_enforce_v1 电池（前置强制型原型）", "n": len(res),
           "passed": passed, "all_pass": passed == len(res), "results": res}
    json.dump(out, open(os.path.join(ROOT, ".agent", "reports", "availability-enforce-battery.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
