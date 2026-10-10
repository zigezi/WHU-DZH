#!/usr/bin/env python3
"""P5a.42 §二 R3：提取保真 85 例专项核查（不挡门，e8 判读附件）。

按方向（plan>run 扩张 / plan<run 截断）、epoch 分布分类；判定计划性质。
  PYTHONPATH=.agent/vendor/tau-bench .agent/venv/tau/bin/python scripts/e8_extraction_audit.py --epoch 7
"""
import argparse
import hashlib
import json
import os
import sqlite3
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from e8_freeze import run_epoch_of  # noqa: E402

R = os.path.join(ROOT, ".agent", "reports")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epoch", type=int, default=7)
    args = ap.parse_args()
    con = sqlite3.connect(os.path.join(BACKEND, "logs", "trace.db"))
    con.row_factory = sqlite3.Row
    calls = {}
    for t in con.execute("SELECT task_id,req_id,created_at FROM tasks WHERE req_id LIKE 'TAU-%'"):
        e = run_epoch_of(t["created_at"])
        if e is None:
            continue
        calls[(t["req_id"], e)] = con.execute(
            "SELECT count(*) FROM spans WHERE trace_id=? AND type='tool_call'",
            (t["task_id"],)).fetchone()[0]

    direction = Counter()
    by_epoch = Counter()
    rows = []
    seen = set()
    for r in con.execute("SELECT req_id,plan_json,created_at FROM precedent_snapshots WHERE epoch=?",
                         (args.epoch,)):
        rid = r["req_id"] or ""
        if not rid.startswith("TAU-"):
            continue
        try:
            plan = json.loads(r["plan_json"]) if r["plan_json"] else []
        except Exception:
            plan = []
        if not all(str(s.get("tool", "")).startswith("tau__") for s in plan):
            continue
        e = run_epoch_of(r["created_at"])
        key = (rid, e, len(plan))
        if key in seen:
            continue
        seen.add(key)
        n = calls.get((rid, e))
        if n is None or n == len(plan):
            continue
        d = "plan>run(expansion)" if len(plan) > n else "plan<run(truncation)"
        direction[d] += 1
        by_epoch[e] += 1
        rows.append({"req_id": rid, "epoch": e, "plan_tools": len(plan), "run_tool_calls": n,
                     "direction": d})
    out = {
        "note": "P5a.42 R3 提取保真；机器只分类，性质判定待审。计划来源=run 事后抽取（_store_precedent 采 tool_call 步）",
        "defect_n": len(rows), "direction": dict(direction), "by_epoch": dict(by_epoch),
        "epoch_concentration": (max(by_epoch.values()) / len(rows) if rows else 0),
        "rows": rows[:200],
    }
    json.dump(out, open(os.path.join(R, "e8-extraction-audit.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
