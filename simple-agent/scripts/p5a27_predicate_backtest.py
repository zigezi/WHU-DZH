#!/usr/bin/env python3
"""P5a.27 §六.1 工单：结构谓词漏检率/误报率回测（零 token）。

谓词（a27 §四.2 版）：在"首个 modify_*/exchange_* 调用被解析时点火"，
用于注入锁序规则（同一实体多步修改先地址后物品）。

在 e4-e6 零售轨迹上量化：
  - 目标人群：同订单上 >=2 个 modify 类调用；
  - 漏检（rescue）：锁序报错是否发生在"首个 modify"之后可被阻止的位置；
  - 误报：谓词点火但无 modify 报错。

  /root/miniconda3/envs/mini-agent/bin/python scripts/p5a27_predicate_backtest.py
"""
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "backend", "logs", "trace.db")
OUT = os.path.join(ROOT, ".agent", "reports", "p5a27-predicate-backtest.json")

KEYS = ("modify_pending_order", "exchange_delivered_order", "return_delivered_order")
ITEMISH = ("modify_pending_order_items", "exchange_delivered_order_items")


def ep(ts):
    for p, v in (("2026-09-15", 4), ("2026-09-16", 5), ("2026-09-29", 6)):
        if ts and ts.startswith(p):
            return v
    return None


def short(t):
    return t.replace("tau__", "")


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    runs = []
    for t in con.execute("SELECT task_id,req_id,created_at FROM tasks WHERE req_id LIKE 'TAU-R-%'"):
        e = ep(t["created_at"])
        if e not in (4, 5, 6):
            continue
        seq = []
        for s in con.execute(
            "SELECT attributes FROM spans WHERE trace_id=? AND type='tool_call' ORDER BY start_time",
            (t["task_id"],),
        ):
            a = json.loads(s["attributes"]) if s["attributes"] else {}
            tool = a.get("tool") or ""
            if any(k in tool for k in KEYS):
                out = str(a.get("output") or "")
                seq.append((short(tool), (a.get("args") or {}).get("order_id"),
                            "non-pending order cannot be modified" in out, "Error:" in out))
        if seq:
            runs.append({"epoch": e, "req_id": t["req_id"], "seq": seq})

    lock = [r for r in runs if any(x[3] for x in r["seq"])]
    multi = [r for r in runs if any(
        sum(1 for x in r["seq"] if x[1] == o) >= 2 for o in {x[1] for x in r["seq"]})]
    noerr = [r for r in runs if not any(x[3] for x in r["seq"])]
    single = [r for r in noerr if not any(
        sum(1 for x in r["seq"] if x[1] == o) >= 2 for o in {x[1] for x in r["seq"]})]

    timing = []
    coincide = before = 0
    for r in lock:
        for o in {x[1] for x in r["seq"]}:
            calls = [(i, x) for i, x in enumerate(r["seq"]) if x[1] == o]
            errs = [(i, x) for i, x in calls if x[2]]
            if not errs:
                continue
            first = calls[0][0]
            dmg = next((i for i, x in calls if x[0] in ITEMISH), None)
            tag = "too_late" if (dmg is not None and first >= dmg) else "before"
            coincide += tag == "too_late"
            before += tag == "before"
            timing.append({"epoch": r["epoch"], "req_id": r["req_id"], "order": o,
                           "calls": [x[0] for _, x in calls], "err_idx": errs[0][0],
                           "first_modify_idx": first, "items_idx": dmg, "verdict": tag})

    result = {
        "note": "P5a.27 §六.1 谓词回测；机器输出，不作结论",
        "runs_with_modify": len(runs),
        "multi_modify_target": len(multi),
        "modify_error_runs": len(lock),
        "fire_too_late": coincide,
        "fire_before": before,
        "rescue_rate": f"{before}/{coincide + before}",
        "harmless_fires": len(noerr),
        "pure_false_alarm_single_modify": len(single),
        "timing": timing,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(result, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in result.items() if k != "timing"}, ensure_ascii=False, indent=1))
    print(f"-> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
