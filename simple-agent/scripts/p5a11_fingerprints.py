#!/usr/bin/env python3
"""P5a.11 Part 1 — 四条机制指纹（零成本，对 epoch-3/4 现有 spans）。

只读 trace.db；不写 backend/ 代码，不烧 API。
"""
import json
import os
import sqlite3
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "backend", "logs", "trace.db")


def load_epoch(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return json.load(f)


def tids(rep):
    return [e["task_id"] for e in rep["entries"] if e.get("task_id")]


def qmarks(n):
    return ",".join("?" * n)


def spans(con, types, ids):
    rows = con.execute(
        f"SELECT trace_id, type, start_time, attributes FROM spans "
        f"WHERE type IN ({qmarks(len(types))}) AND trace_id IN ({qmarks(len(ids))}) "
        f"ORDER BY trace_id, start_time",
        list(types) + list(ids),
    ).fetchall()
    out = []
    for r in rows:
        try:
            attrs = json.loads(r[3]) if r[3] else {}
        except Exception:
            attrs = {}
        out.append({"trace": r[0], "type": r[1], "t": r[2], "a": attrs})
    return out


def pct(v, q):
    if not v:
        return 0
    v = sorted(v)
    return v[min(len(v) - 1, int(q * len(v)))]


def fp4(con, ids, label):
    vals = []
    for tid in ids:
        r = con.execute(
            "SELECT json_extract(attributes,'$.total_tokens') FROM spans "
            "WHERE type='tau_cost' AND trace_id=?", (tid,)).fetchone()
        if r and r[0]:
            vals.append(r[0])
    print(f"FP-4 {label}: n={len(vals)} p90={pct(vals,.9):,} p99={pct(vals,.99):,} "
          f"max={max(vals) if vals else 0:,} >150k={sum(1 for x in vals if x>150000)}")


def fp1(con, ids, label):
    sp = spans(con, ("dialogue_turn", "tool_call"), ids)
    by_trace = defaultdict(list)
    for s in sp:
        by_trace[s["trace"]].append(s)
    resp_total = conf_total = 0
    turns_total = 0
    for tid, ss in by_trace.items():
        first_tc = next((s["t"] for s in ss if s["type"] == "tool_call"), None)
        for s in ss:
            if s["type"] == "dialogue_turn":
                turns_total += 1
                if s["a"].get("role") == "assistant":
                    resp_total += 1
                    if first_tc is not None and s["t"] < first_tc:
                        conf_total += 1
    print(f"FP-1 {label}: assistant(RESPOND) turns={resp_total} "
          f"pre-first-toolcall(确认型)={conf_total} avg_turns/task={turns_total/len(ids):.1f}")


def fp5(con, ids, label):
    cb = con.execute(f"SELECT count(*) FROM spans WHERE type='circuit_break' "
                     f"AND trace_id IN ({qmarks(len(ids))})", ids).fetchone()[0]
    fi = con.execute(f"SELECT count(*) FROM spans WHERE type='feedback_injected' "
                     f"AND trace_id IN ({qmarks(len(ids))})", ids).fetchone()[0]
    fr = con.execute(f"SELECT count(*) FROM spans WHERE type='feedback_response' "
                     f"AND trace_id IN ({qmarks(len(ids))})", ids).fetchone()[0]
    # consecutive same-tool failure segments >=3
    sp = spans(con, ("tool_call",), ids)
    by_trace = defaultdict(list)
    for s in sp:
        by_trace[s["trace"]].append(s)
    seg3 = 0
    for tid, ss in by_trace.items():
        run = 0
        for s in ss:
            name = s["a"].get("tool")
            if s["a"].get("success") is False:
                run += 1
            else:
                if run >= 3:
                    seg3 += 1
                run = 0
        if run >= 3:
            seg3 += 1
    print(f"FP-5 {label}: circuit_break={cb} feedback_injected={fi} "
          f"feedback_response={fr} same-tool-fail-run>=3={seg3}")


def fp2(con, ids, label, sample=False):
    sp = spans(con, ("dialogue_turn", "tool_call"), ids)
    by_trace = defaultdict(list)
    for s in sp:
        by_trace[s["trace"]].append(s)
    total_calls = unfounded_calls = 0
    samples = []
    for tid, ss in by_trace.items():
        ctx = ""
        for s in ss:
            if s["type"] == "dialogue_turn":
                ctx += " " + str(s["a"].get("text", ""))
            else:
                total_calls += 1
                args = s["a"].get("args") or {}
                bad = []
                for k, v in args.items():
                    if isinstance(v, str) and len(v) >= 3 and any(c.isalpha() for c in v):
                        if v not in ctx:
                            bad.append(f"{k}={v!r}")
                if bad:
                    unfounded_calls += 1
                    if len(samples) < 3:
                        samples.append((tid[:8], s["a"].get("tool"), bad))
                ctx += " " + str(s["a"].get("output", ""))
    print(f"FP-2 {label}: tool_calls={total_calls} unfounded={unfounded_calls} "
          f"ratio={unfounded_calls/max(1,total_calls):.1%}")
    if sample:
        for tid, tool, bad in samples:
            print(f"   sample: trace={tid} tool={tool} unfounded_args={bad}")


def main():
    con = sqlite3.connect(DB)
    e3 = load_epoch(".agent/reports/tau-epoch-3.json")
    e4 = load_epoch(".agent/reports/tau-epoch-4.json")
    E3, E4 = tids(e3), tids(e4)
    print("=== Part 1 机制指纹（epoch-3 vs epoch-4）===")
    print(f"tasks: e3={len(E3)} e4={len(E4)}")
    for label, ids in (("e3", E3), ("e4", E4)):
        fp4(con, ids, label)
    for label, ids in (("e3", E3), ("e4", E4)):
        fp1(con, ids, label)
    for label, ids in (("e3", E3), ("e4", E4)):
        fp5(con, ids, label)
    for label, ids in (("e3", E3), ("e4", E4)):
        fp2(con, ids, label, sample=(label == "e4"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
