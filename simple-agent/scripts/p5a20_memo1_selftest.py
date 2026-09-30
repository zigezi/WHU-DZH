#!/usr/bin/env python3
"""P5a.20 便签1 自测：GT-vs-final 字段级 diff（纯函数，无需 tau venv）。

  /root/miniconda3/envs/mini-agent/bin/python scripts/p5a20_memo1_selftest.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend", "requirements", "adapters", "tau"))

import diff  # noqa: E402

A = {"name": "modify_pending_order_address",
     "kwargs": {"order_id": "#W4860251", "city": "Chicago"}}
I = {"name": "modify_pending_order_items",
     "kwargs": {"order_id": "#W4860251", "item_ids": ["5209958006"]}}
R = {"name": "respond", "kwargs": {"content": "done"}}


def t1_actions_missing():
    # agent did items-only (R-105 e4/e5 order); GT = address -> items
    d = diff.actions_diff([I, R], [A, I, R], terminate=("respond",))
    assert any(m["name"] == "modify_pending_order_address" for m in d["missing"]), d
    assert d["extra"] == [], d
    print("  t1 actions_missing OK ->", [m["name"] for m in d["missing"]])


def t2_actions_extra():
    d = diff.actions_diff([A, I, {"name": "return_delivered_order_items",
                                  "kwargs": {"order_id": "#W1"}}],
                          [A, I], terminate=("respond",))
    assert any(e["name"] == "return_delivered_order_items" for e in d["extra"]), d
    print("  t2 actions_extra OK ->", [e["name"] for e in d["extra"]])


def t3_data_diff():
    agent = {"orders": {"#W4860251": {"status": "pending (item modified)",
                                      "address": {"city": "Seattle"}}},
             "users": {}, "products": {}}
    gt = {"orders": {"#W4860251": {"status": "pending (item modified)",
                                   "address": {"city": "Chicago"}}},
          "users": {}, "products": {}}
    d = diff.data_diff(agent, gt)
    assert any(x.get("field") == "address" and x.get("id") == "#W4860251" for x in d), d
    print("  t3 data_diff OK ->", d)


def t4_bounded():
    agent = {"orders": {f"#W{i}": {"status": "x"} for i in range(100)},
             "users": {}, "products": {}}
    gt = {"orders": {f"#W{i}": {"status": "y"} for i in range(100)},
          "users": {}, "products": {}}
    d = diff.data_diff(agent, gt, limit=5)
    assert len(d) <= 6 and d[-1].get("truncated") is True, d
    print("  t4 bounded OK ->", len(d), "entries, truncated=", d[-1].get("truncated"))


if __name__ == "__main__":
    print("[memo1 selftest]")
    t1_actions_missing()
    t2_actions_extra()
    t3_data_diff()
    t4_bounded()
    print("ALL PASS")
