#!/usr/bin/env python3
"""P5a.48：non_delivered_exchange_v1 电池（≥5，含阴性对照）。"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from monitor.exchange_guard import ExchangeGuard  # noqa: E402

OUT_PENDING = '{"order_id": "#W1", "status": "pending", "items": []}'
OUT_DELIVERED = '{"order_id": "#W1", "status": "delivered", "items": []}'


def probes():
    g = ExchangeGuard(); g.observe("get_order_details", {"order_id": "#W1"}, OUT_PENDING)
    p1 = g.before("exchange_delivered_order_items", {"order_id": "#W1"})[0] is True

    g2 = ExchangeGuard(); g2.observe("get_order_details", {"order_id": "#W1"}, OUT_DELIVERED)
    n1 = g2.before("exchange_delivered_order_items", {"order_id": "#W1"})[0] is False

    n2 = ExchangeGuard().before("exchange_delivered_order_items", {"order_id": "#W1"})[0] is False  # 未知状态

    n3 = ExchangeGuard().before("get_order_details", {"order_id": "#W1"})[0] is False

    g4 = ExchangeGuard()
    g4.observe("get_order_details", {"order_id": "#W1"}, OUT_PENDING)
    g4.observe("get_order_details", {"order_id": "#W1"}, OUT_DELIVERED)   # 状态更新为 delivered
    n4 = g4.before("exchange_delivered_order_items", {"order_id": "#W1"})[0] is False

    g5 = ExchangeGuard(); g5.observe("get_order_details", {"order_id": "#W1"}, OUT_PENDING)
    p2 = "不是 delivered" in (g5.before("exchange_delivered_order_items", {"order_id": "#W1"})[1] or "")
    return [("P1_pending_blocks", p1), ("N1_delivered_passes", n1),
            ("N2_unknown_status_passes", n2), ("N3_non_target_passes", n3),
            ("N4_status_update_passes", n4), ("P2_text", p2)]


def main():
    res = [{"probe": n, "pass": bool(p)} for n, p in probes()]
    passed = sum(1 for r in res if r["pass"])
    out = {"note": "non_delivered_exchange_v1 电池", "n": len(res), "passed": passed,
           "all_pass": passed == len(res), "results": res}
    json.dump(out, open(os.path.join(ROOT, ".agent", "reports", "exchange-guard-battery.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
