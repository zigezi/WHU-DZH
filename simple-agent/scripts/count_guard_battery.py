#!/usr/bin/env python3
"""P5a.48：items_count_match_v1 电池（≥5，含阴性对照）。"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from monitor.count_guard import CountMatchGuard  # noqa: E402


def probes():
    G = CountMatchGuard()
    return [
        ("P1_len_mismatch_blocks", G.before("exchange_delivered_order_items",
                                            {"item_ids": ["a", "b"], "new_item_ids": ["c"]})[0] is True),
        ("N1_equal_passes", CountMatchGuard().before("exchange_delivered_order_items",
                                                     {"item_ids": ["a"], "new_item_ids": ["b"]})[0] is False),
        ("N2_non_target_tool_passes", CountMatchGuard().before("get_order_details", {"order_id": "#W1"})[0] is False),
        ("N3_missing_keys_passes", CountMatchGuard().before("modify_pending_order_items", {"order_id": "#W1"})[0] is False),
        ("N4_both_empty_equal_passes", CountMatchGuard().before("exchange_delivered_order_items",
                                                                {"item_ids": [], "new_item_ids": []})[0] is False),
        ("P2_text", "长度必须相等" in (CountMatchGuard().before(
            "exchange_delivered_order_items", {"item_ids": ["a"], "new_item_ids": []})[1] or "")),
    ]


def main():
    res = [{"probe": n, "pass": bool(p)} for n, p in probes()]
    passed = sum(1 for r in res if r["pass"])
    out = {"note": "items_count_match_v1 电池", "n": len(res), "passed": passed,
           "all_pass": passed == len(res), "results": res}
    json.dump(out, open(os.path.join(ROOT, ".agent", "reports", "count-guard-battery.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
