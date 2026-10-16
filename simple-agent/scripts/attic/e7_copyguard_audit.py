#!/usr/bin/env python3
"""P5a.29 §四 / a31 §三：e7 72 条注入的 CopyGuard 全样本审计（零 token）。

  /root/miniconda3/envs/mini-agent/bin/python scripts/e7_copyguard_audit.py
"""
import hashlib
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)

from monitor.copyguard import entity_values, scan_trace  # noqa: E402

DB = os.path.join(BACKEND, "logs", "trace.db")
OUT = os.path.join(ROOT, ".agent", "reports", "e7-copyguard-audit.json")


def chash(plan):
    return hashlib.sha256(
        json.dumps(plan, ensure_ascii=False, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    # snapshot plans by (req_id, hash)
    snap = {}
    for r in con.execute("SELECT req_id,plan_json FROM precedent_snapshots WHERE epoch=7"):
        try:
            p = json.loads(r["plan_json"]) if r["plan_json"] else []
        except Exception:
            p = []
        snap[(r["req_id"], chash(p))] = p
    # verdicts
    W = "req_id LIKE 'TAU-%' AND created_at>='2026-09-29T14:30'"
    verd = {}
    for t in con.execute(f"SELECT task_id,req_id FROM tasks WHERE {W}"):
        for s in con.execute("SELECT attributes FROM spans WHERE trace_id=? AND type='verdict'", (t["task_id"],)):
            a = json.loads(s["attributes"]) if s["attributes"] else {}
            verd[t["req_id"]] = a.get("decision")

    rows = []
    for t in con.execute(f"SELECT task_id,req_id FROM tasks WHERE {W}"):
        for s in con.execute("SELECT attributes FROM spans WHERE trace_id=? AND type='precedent_injected'", (t["task_id"],)):
            a = json.loads(s["attributes"]) if s["attributes"] else {}
            prec, h = a.get("precedent_req"), a.get("content_sha256_16")
            plan = snap.get((prec, h), [])
            watch = entity_values(plan)
            hits = scan_trace(t["task_id"], watch)
            rows.append({"task": t["req_id"], "injectant": prec, "self": t["req_id"] == prec,
                         "verdict": verd.get(t["req_id"]),
                         "watch_values": len(watch), "hits": len(hits),
                         "hit_values": sorted({x["value"] for x in hits})[:8]})
    n = len(rows)
    n_hit = sum(1 for r in rows if r["hits"])
    print(f"e7 injections audited: {n}; with copy hits: {n_hit}")
    for r in rows:
        if r["hits"]:
            print(f"  {r['task']:11} <- {r['injectant']:11} self={str(r['self']):5} "
                  f"verdict={r['verdict']} hits={r['hits']} {r['hit_values'][:3]}")
    json.dump({"note": "e7 CopyGuard 全样本；命中=值在 args 且未经先前工具结果",
               "audited": n, "with_hits": n_hit, "rows": rows},
              open(OUT, "w"), ensure_ascii=False, indent=1)
    print("->", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
