#!/usr/bin/env python3
"""P5a.48 §八：repeat_failure_v1 金丝雀电池（≥5 探针，含阴性对照）。"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from monitor.repeat_guard import RepeatFailureGuard, SYNTHETIC  # noqa: E402

PROBES = []


def probe(name, fn):
    PROBES.append((name, fn))


def p_third_identical_blocks():
    G = RepeatFailureGuard()
    a = {"user_id": "u1"}
    G.after("tau__get_user_details", a, False)
    G.after("tau__get_user_details", a, False)
    v, _ = G.before("tau__get_user_details", a)
    return v is True
probe("P1_third_identical_fail_blocks", p_third_identical_blocks)


def p_two_attempts_allowed():
    G = RepeatFailureGuard()
    a = {"user_id": "u1"}
    G.after("t", a, False)
    v, _ = G.before("t", a)   # 本次将是第 2 次 → 放行
    return v is False
probe("P2_below_threshold_allowed", p_two_attempts_allowed)


def p_success_resets():   # 阴性对照：合法重演
    G = RepeatFailureGuard()
    a = {"x": 1}
    G.after("t", a, False); G.after("t", a, False)
    G.after("t", a, True)            # 成功 → 清零
    v, _ = G.before("t", a)
    return v is False
probe("N1_success_resets_no_block", p_success_resets)


def p_distinct_args():    # 阴性对照：不同参数
    G = RepeatFailureGuard()
    G.after("t", {"x": 1}, False); G.after("t", {"x": 1}, False)
    v, _ = G.before("t", {"x": 2})
    return v is False
probe("N2_distinct_args_no_block", p_distinct_args)


def p_distinct_tools():   # 阴性对照：不同工具
    G = RepeatFailureGuard()
    G.after("t1", {"x": 1}, False); G.after("t1", {"x": 1}, False)
    v, _ = G.before("t2", {"x": 1})
    return v is False
probe("N3_distinct_tools_no_block", p_distinct_tools)


def p_synthetic_text():
    G = RepeatFailureGuard()
    a = {"x": 1}
    G.after("t", a, False); G.after("t", a, False)
    v, s = G.before("t", a)
    return v and "请改变参数或方法" in s
probe("P3_synthetic_text_correct", p_synthetic_text)


def p_state_change_resets():   # N4（P5a.48 修正）：中间状态变更成功 → 同参放行
    G = RepeatFailureGuard()
    m = {"order_id": "#W1", "item_ids": ["a"], "new_item_ids": ["b"]}
    G.after("modify_pending_order_items", m, False)
    G.after("modify_pending_order_items", m, False)
    G.after("modify_pending_order_address", {"order_id": "#W1"}, True)   # 状态变更成功
    v, _ = G.before("modify_pending_order_items", m)
    return v is False
probe("N4_state_change_resets_no_block", p_state_change_resets)


def main():
    res = []
    for n, f in PROBES:
        try:
            res.append({"probe": n, "pass": bool(f())})
        except Exception as e:  # noqa: BLE001
            res.append({"probe": n, "pass": False, "err": repr(e)[:120]})
    n = len(res); passed = sum(1 for r in res if r["pass"])
    out = {"note": "repeat_failure_v1 电池（含 3 阴性对照）", "n": n, "passed": passed,
           "all_pass": passed == n, "results": res}
    path = os.path.join(ROOT, ".agent", "reports", "repeat-guard-battery.json")
    json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
