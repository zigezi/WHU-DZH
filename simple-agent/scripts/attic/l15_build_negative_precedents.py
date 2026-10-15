#!/usr/bin/env python3
"""L1.5 负先例库构建（P5a.47 §三.4 / P5a.54）：e1–e8 失败轨迹 → negative_precedents 表（零 token）。
  /root/miniconda3/envs/mini-agent/bin/python scripts/l15_build_negative_precedents.py
"""
import json
import os
import sqlite3
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from monitor.trace_store import trace_store  # noqa: E402
from monitor import negative_precedent as np  # noqa: E402
from e8_freeze import run_epoch_of  # noqa: E402

LOCK_ERR = "non-pending order cannot be modified"
READ = ("get_", "search_", "list_", "find_", "calculate", "think")


def classify(errs, tools):
    if any(LOCK_ERR in e for e in errs):
        return "lock_order"
    if errs:
        return "tool_error:" + errs[0][:30]
    c = Counter(tools)
    if any(v >= 3 and not t.startswith(READ) for t, v in c.items()):
        return "repeat_mutating"
    return "verdict_fail"


def main():
    con = trace_store.conn
    con.row_factory = sqlite3.Row
    con.execute("DELETE FROM negative_precedents")
    con.commit()
    seen_map = {}
    n = 0
    for t in con.execute("SELECT task_id,req_id,created_at FROM tasks WHERE req_id LIKE 'TAU-%'"):
        verdict = None
        errors, tools = [], []
        for s in con.execute("SELECT type,attributes FROM spans WHERE trace_id=?", (t["task_id"],)):
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
            continue
        plan = [{"tool": tl} for tl in tools]
        cause = classify(errors, tools)
        epoch = run_epoch_of(t["created_at"])
        # 每 (req, epoch) 一条，避免重复
        key = (t["req_id"], epoch)
        if key in seen_map:
            continue
        seen_map[key] = True
        np.add(t["req_id"], cause, "FAIL", epoch, plan,
               tokens=0, created_at=t["created_at"])
        n += 1
    out = {"note": "L1.5 负先例库（不注入；警告通道）", "n": n,
           "by_cause": np.count_by_cause()}
    json.dump(out, open(os.path.join(ROOT, ".agent", "reports", "l15-negative-precedents.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
