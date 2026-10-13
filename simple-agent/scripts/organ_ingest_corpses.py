#!/usr/bin/env python3
"""P5a.61 §三：器官消化本批 FAIL 尸体（ring_mine → ring_triage 分诊处置单，零 token）。
  /root/miniconda3/envs/mini-agent/bin/python scripts/organ_ingest_corpses.py [--since 2026-10-13]
"""
import argparse
import json
import os
import sqlite3
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
from monitor.organ import Pipeline  # noqa: E402

DB = os.path.join(BACKEND, "logs", "trace.db")
R = os.path.join(ROOT, ".agent", "reports")
READ = ("get_", "search_", "list_", "find_", "calculate", "think")
LOCK_ERR = "non-pending order cannot be modified"


def run_pattern(con, tid, rid):
    verdict, errors, tools = None, [], []
    for s in con.execute("SELECT type,attributes FROM spans WHERE trace_id=? ORDER BY start_time", (tid,)):
        a = json.loads(s["attributes"]) if s["attributes"] else {}
        if s["type"] == "verdict":
            verdict = a.get("decision")
        elif s["type"] == "tool_call":
            tools.append((a.get("tool") or "").replace("tau__", ""))
        elif s["type"] == "sandbox_exec":
            o = str(a.get("output") or "")
            if "Error:" in o:
                errors.append(o[o.find("Error:"):][:60])
    if verdict != "FAIL":
        return None
    if any(LOCK_ERR in e for e in errors):
        return {"pattern_id": "LOCK_ORDER::modify_items_first", "kind": "order_lock", "examples": [rid]}
    if errors:
        return {"pattern_id": "ERR::" + errors[0][:40], "kind": "tool_error", "examples": [rid]}
    c = Counter(tools)
    if any(v >= 3 and not t.startswith(READ) for t, v in c.items()):
        return {"pattern_id": "REPEAT::" + max(c, key=c.get), "kind": "repeat_failure", "examples": [rid]}
    return {"pattern_id": "VERDICT_FAIL::" + rid, "kind": "verdict_fail", "examples": [rid]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-10-13")
    args = ap.parse_args()
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    pipe = Pipeline()
    rows = []
    for t in con.execute("SELECT task_id,req_id,created_at FROM tasks WHERE req_id LIKE 'TAU-%' AND created_at>=? ORDER BY created_at", (args.since,)):
        p = run_pattern(con, t["task_id"], t["req_id"])
        if not p:
            continue
        disp = pipe.classify_disposition(p)
        rows.append({"req_id": t["req_id"], "at": t["created_at"][11:19],
                     "death": p["pattern_id"], "kind": p["kind"], "disposition": disp})
    cnt = Counter(r["disposition"] for r in rows)
    out = {"note": "P5a.61 器官消化本批 FAIL 尸体（ring_mine→ring_triage）；处置=分诊单",
           "corpses": len(rows), "disposition_counts": dict(cnt),
           "candidates_new": sum(1 for r in rows if r["disposition"] == "deploy"),
           "rows": rows}
    json.dump(out, open(os.path.join(R, "organ-corpse-triage.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, ensure_ascii=False, indent=1))
    for r in rows:
        print(f"  {r['req_id']:11} {r['death'][:38]:38} {r['kind']:14} -> {r['disposition']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
