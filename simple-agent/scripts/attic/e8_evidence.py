#!/usr/bin/env python3
"""P5a.43 证据包：运行表 + CopyGuard 审计 + 新旧分母对照。"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
R = os.path.join(ROOT, ".agent", "reports")
import sqlite3  # noqa: E402
from monitor.copyguard import entity_values, scan_trace  # noqa: E402


def chash(p):
    return hashlib.sha256(json.dumps(p, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()[:16]


def main():
    con = sqlite3.connect(os.path.join(BACKEND, "logs", "trace.db"))
    con.row_factory = sqlite3.Row
    matrix = {r["req_id"]: r for r in json.load(open(os.path.join(R, "e8-matrix-freeze.json")))["matrix"]}
    raw = json.load(open(os.path.join(R, "e8-deid-snapshot.json")))
    inv = {v["deid_hash"]: k for k, v in raw.items()}          # deid_hash -> orig_hash
    orig = {}
    for r in con.execute("SELECT plan_json FROM precedent_snapshots WHERE epoch=7"):
        p = json.loads(r["plan_json"] or "[]")
        orig.setdefault(chash(p), p)

    W = "req_id LIKE 'TAU-%' AND created_at>='2026-10-10'"
    table, cg_rows = [], []
    for t in con.execute(f"SELECT task_id,req_id,llm_tokens FROM tasks WHERE {W}"):
        arm = deid_hash = verdict = None
        for s in con.execute("SELECT type,attributes FROM spans WHERE trace_id=?", (t["task_id"],)):
            a = json.loads(s["attributes"]) if s["attributes"] else {}
            if s["type"] == "arm_choice":
                arm = a.get("arm")
            elif s["type"] == "precedent_injected":
                deid_hash = a.get("content_sha256_16")
            elif s["type"] == "verdict":
                verdict = a.get("decision")
        row = matrix.get(t["req_id"], {})
        table.append({"task_id": t["task_id"], "req_id": t["req_id"], "arm": arm,
                      "injectant": row.get("injectant"), "deid_hash": deid_hash,
                      "verdict": verdict, "tokens": t["llm_tokens"]})
        # CopyGuard：watch = 注入物原始（脱敏前）实体值
        watch = set()
        if deid_hash and deid_hash in inv:
            watch = entity_values(orig.get(inv[deid_hash], []))
        hits = scan_trace(t["task_id"], watch) if watch else []
        if hits:
            cg_rows.append({"req_id": t["req_id"], "arm": arm, "hits": len(hits),
                            "values": sorted({h["value"] for h in hits})[:5]})

    table.sort(key=lambda r: r["req_id"])
    json.dump({"note": "P5a.43 运行表", "n": len(table), "rows": table},
              open(os.path.join(R, "e8-run-table.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"note": "CopyGuard e8 审计（watch=原始注入值；脱敏后预期 0）",
               "with_hits": len(cg_rows), "rows": cg_rows},
              open(os.path.join(R, "e8-copyguard-audit.json"), "w"), ensure_ascii=False, indent=1)
    print(f"run table {len(table)} rows; CopyGuard hits {len(cg_rows)}")
    for c in cg_rows[:10]:
        print("  ", c)
    return 0


if __name__ == "__main__":
    sys.exit(main())
