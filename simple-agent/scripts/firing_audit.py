#!/usr/bin/env python3
"""P5a.55 §二：追溯点火审计（零 token）——静态回放 e1–e8 轨迹，出每资产混淆矩阵。
  /root/miniconda3/envs/mini-agent/bin/python scripts/firing_audit.py
"""
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
from monitor import (interceptor, repeat_guard, count_guard, exchange_guard,  # noqa: E402
                     payment_guard, certificate_guard, availability_guard, giftcard_guard)

DB = os.path.join(BACKEND, "logs", "trace.db")
OUT = os.path.join(ROOT, ".agent", "reports", "firing-audit.json")

READ = ("get_", "search_", "list_", "find_", "calculate", "think")
LOCK_ERR = "non-pending order cannot be modified"


def classify_run(errors, tools):
    if any(LOCK_ERR in e for e in errors):
        return "lock_order"
    if errors:
        return "err:" + errors[0]
    from collections import Counter
    c = Counter(tools)
    if any(v >= 3 and not t.startswith(READ) for t, v in c.items()):
        return "repeat_mutating"
    return "verdict_fail"


# asset -> (guard factory, 死因匹配子串, 干预语义型)
#  benign = veto-then-reissue（点火 PASS 记税，不记硬线违例）
#  hard   = 行为改道型（点火 PASS = 硬线违例）
ASSETS = {
    "lock_order_v1": (lambda: interceptor.OrderLockInterceptor(), ["lock_order"], "benign"),
    "repeat_failure_v1": (lambda: repeat_guard.RepeatFailureGuard(), ["repeat_mutating"], "benign"),
    "items_count_match_v1": (lambda: count_guard.CountMatchGuard(), ["number of items"], "hard"),
    "non_delivered_exchange_v1": (lambda: exchange_guard.ExchangeGuard(), ["non-delivered"], "hard"),
    "payment_amount_sum_v1": (lambda: payment_guard.PaymentSumGuard(),
                              ["payment amount does not add up"], "hard"),
    "certificate_update_v1": (lambda: certificate_guard.CertificateUpdateGuard(),
                              ["certificate cannot be used"], "hard"),
    "flight_availability_v1": (lambda: availability_guard.FlightAvailabilityGuard(),
                               ["not enough seats"], "hard"),
    "flight_availability_enforce_v1": (lambda: availability_guard.FlightAvailabilityGuard(enforce=True),
                                       [], "benign"),
    "gift_card_balance_v1": (lambda: giftcard_guard.GiftCardBalanceGuard(),
                             ["gift card balance is not enough", "not enough balance in payment"], "hard"),
}


def load_runs(con):
    runs = []
    for t in con.execute("SELECT task_id,req_id FROM tasks WHERE req_id LIKE 'TAU-%'"):
        verdict, errors, calls = None, [], []
        for s in con.execute("SELECT type,attributes FROM spans WHERE trace_id=? ORDER BY start_time", (t["task_id"],)):
            a = json.loads(s["attributes"]) if s["attributes"] else {}
            if s["type"] == "verdict":
                verdict = a.get("decision")
            elif s["type"] == "tool_call":
                calls.append({"tool": (a.get("tool") or "").replace("tau__", ""),
                              "args": a.get("args") or {}, "success": a.get("success", True),
                              "output": str(a.get("output") or "")})
            elif s["type"] == "sandbox_exec":
                o = str(a.get("output") or "")
                if "Error:" in o:
                    errors.append(o[o.find("Error:"):][:80])
        if verdict is None:
            continue
        runs.append({"task_id": t["task_id"], "verdict": verdict, "errors": errors, "calls": calls})
    return runs


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    runs = load_runs(con)
    results = {}
    for asset, (factory, causes, mode) in ASSETS.items():
        fired_fail = fired_pass = rescue = miss = 0
        for r in runs:
            g = factory()
            fired = False
            for c in r["calls"]:
                if hasattr(g, "observe"):
                    try:
                        g.observe(c["tool"], c["args"], c["output"])
                    except Exception:  # noqa: BLE001
                        pass
                v, _ = g.before(c["tool"], c["args"])
                if v:
                    fired = True
                if hasattr(g, "after"):
                    try:
                        g.after(c["tool"], c["args"], c["success"])
                    except Exception:  # noqa: BLE001
                        pass
            is_fail = r["verdict"] == "FAIL"
            cause = classify_run(r["errors"], [c["tool"] for c in r["calls"]])
            match = any(sub in cause for sub in causes)
            if fired and not is_fail:
                fired_pass += 1                       # 真实误伤（硬线）
            if fired and is_fail:
                fired_fail += 1
                if match:
                    rescue += 1
            if (not fired) and is_fail and match:
                miss += 1
        coverage = round(rescue / (rescue + miss), 3) if (rescue + miss) else None
        viol = (mode == "hard") and fired_pass > 0        # 行为改道型才记硬线
        results[asset] = {"mode": mode, "fired_on_fail": fired_fail,
                          "fires_on_pass": fired_pass, "tax": fired_pass if mode == "benign" else 0,
                          "rescue": rescue, "miss": miss, "coverage": coverage,
                          "hardline_violation": viol}
    total_rescue = sum(v["rescue"] for v in results.values())
    out = {"note": "P5a.55/56 追溯点火审计（干预语义分级）", "runs": len(runs),
           "assets": results, "total_rescue": total_rescue,
           "hardline_violations": [a for a, v in results.items() if v["hardline_violation"]],
           "all_hardline_zero": not any(v["hardline_violation"] for v in results.values())}
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
