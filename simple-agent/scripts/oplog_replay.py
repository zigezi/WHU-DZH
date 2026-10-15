#!/usr/bin/env python3
"""P5a.82 §三.8：code-ops.jsonl 离线重放（filter_oplog_v1 口径；零 token）。

- 逐行判级：collect（signal/timeout/build/gray）/ drop；
- collect 者按规则入库（去重：已存在 (ts,command,exit_code) 跳过）；gray 不计触发线；
- 4 条历史种子若已在库 → 去重跳过（维持隔离）。

  /root/miniconda3/envs/mini-agent/bin/python scripts/oplog_replay.py
"""
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from monitor import code_corpses as cc  # noqa: E402
from monitor.oplog_filter import filter_event  # noqa: E402

R = os.path.join(ROOT, ".agent", "reports")
LOG = os.path.join(ROOT, ".agent", "logs", "code-ops.jsonl")


def main():
    events = []
    if os.path.exists(LOG):
        with open(LOG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except Exception:  # noqa: BLE001
                    events.append({"_unparsable": line[:80]})
    existing = {(c["ts"], c["command"], c["exit_code"]) for c in cc.list_all(limit=100000)}

    tally = Counter()
    added = Counter()
    rows = []
    for e in events:
        if "_unparsable" in e:
            tally["unparsable"] += 1
            rows.append({"verdict": {"action": "unparsable"}, "line": e["_unparsable"]})
            continue
        v = filter_event(e)
        tally[v["action"]] += 1
        if v["action"] == "collect":
            tally["tier:" + v.get("tier", "?")] += 1
            key = (e.get("ts"), e.get("command"), int(e.get("exit_code", 0)))
            if key in existing:
                tally["dupe_skipped"] += 1
            else:
                cc.ingest_event(e, source="real", capture="replay_v1")
                existing.add(key)
                added[v.get("tier", "?")] += 1
        rows.append({"verdict": v, "command": (e.get("command") or "")[:80],
                     "exit_code": e.get("exit_code")})

    out = {"note": "P5a.82 §三.8 offline replay（filter_oplog_v1）",
           "lines": len(events), "tally": dict(tally), "added_by_tier": dict(added),
           "farm_real_countable": cc.real_count(), "farm_real_classes": cc.real_classes(),
           "rows": rows}
    json.dump(out, open(os.path.join(R, "oplog-replay.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("note", "lines", "tally", "added_by_tier",
                                          "farm_real_countable", "farm_real_classes")},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
