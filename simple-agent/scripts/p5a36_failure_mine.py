#!/usr/bin/env python3
"""P5a.36 / P5a.47 §三.1：失败开采管线首次实跑（零 token）。

从 e1–e8 的尸体库（FAIL 任务轨迹）挖掘 τ 死亡模式 → **谓词候选**（非资产）。
产出 .agent/reports/p5a36-death-patterns.json / .md。

纪律：谓词候选必须出生于尸体；每条须经金丝雀电池后才可登记资产（P5a.46 §二）。
  /root/miniconda3/envs/mini-agent/bin/python scripts/p5a36_failure_mine.py
"""
import json
import os
import re
import sqlite3
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "backend", "logs", "trace.db")
R = os.path.join(ROOT, ".agent", "reports")

LOCK_ERR = "non-pending order cannot be modified"
ERR_RE = re.compile(r"Error:\s*([^'\"\\\n]{0,80})")


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    fails = defaultdict(list)      # error-sig -> [req_id]
    lock_tasks = set()
    repeat_fail = defaultdict(set)
    n_fail = 0
    for t in con.execute("SELECT task_id,req_id,created_at FROM tasks WHERE req_id LIKE 'TAU-%'"):
        verdict = None
        tool_errors = []
        tool_calls = []
        for s in con.execute("SELECT type,attributes FROM spans WHERE trace_id=?", (t["task_id"],)):
            a = json.loads(s["attributes"]) if s["attributes"] else {}
            if s["type"] == "verdict":
                verdict = a.get("decision")
            elif s["type"] == "tool_call":
                tool_calls.append(a.get("tool"))
                out = str(a.get("output") or "")
                for m in ERR_RE.findall(out):
                    tool_errors.append(m.strip())
            elif s["type"] == "sandbox_exec":
                out = str(a.get("output") or "")
                if LOCK_ERR in out:
                    lock_tasks.add(t["req_id"])
        if verdict != "FAIL":
            continue
        n_fail += 1
        for e in tool_errors:
            fails[e].append(t["req_id"])
        # 重复失败（同工具多次）
        c = Counter(tool_calls)
        for tool, k in c.items():
            if k >= 3:
                repeat_fail[tool].add(t["req_id"])

    patterns = []
    for sig, reqs in sorted(fails.items(), key=lambda x: -len(x[1])):
        patterns.append({"pattern_id": f"ERR::{sig[:40]}", "kind": "tool_error",
                         "detector": f"tool result contains 'Error: {sig}'",
                         "occurrences": len(reqs), "examples": sorted(set(reqs))[:6]})
    for tool, reqs in sorted(repeat_fail.items(), key=lambda x: -len(x[1])):
        patterns.append({"pattern_id": f"REPEAT::{tool}", "kind": "repeat_failure",
                         "detector": f"same tool '{tool}' called >=3 times in a run",
                         "occurrences": len(reqs), "examples": sorted(reqs)[:6]})
    if lock_tasks:
        patterns.append({"pattern_id": "LOCK_ORDER::modify_items_first", "kind": "order_lock",
                         "detector": "modify_pending_order_items before modify_pending_order_address on same order",
                         "occurrences": len(lock_tasks), "examples": sorted(lock_tasks)[:6]})

    out = {"note": "P5a.36 失败开采首跑；全部为谓词**候选**，须过金丝雀电池方可登记资产",
           "fail_tasks": n_fail, "pattern_n": len(patterns), "patterns": patterns}
    json.dump(out, open(os.path.join(R, "p5a36-death-patterns.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps({"fail_tasks": n_fail, "pattern_n": len(patterns)}, ensure_ascii=False))
    for p in patterns[:12]:
        print(f"  [{p['kind']}] {p['pattern_id']} x{p['occurrences']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
