#!/usr/bin/env python3
"""P5a.66 §一：回合末收割（主）——把本回合**真实**代码操作失败并入 code_corpses（零 token）。

用法：回合末把本回合真实失败写成 JSONL（默认 .agent/logs/turn-events.jsonl），
  /root/miniconda3/envs/mini-agent/bin/python scripts/code_harvest.py [--events <jsonl>]
去重键 = (ts, command, exit_code)；不伪造、不造任务（a65 §四）。
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from monitor import code_corpses as cc  # noqa: E402

DEFAULT = os.path.join(ROOT, ".agent", "logs", "turn-events.jsonl")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", default=DEFAULT)
    args = ap.parse_args()
    existing = {(c["ts"], c["command"], c["exit_code"]) for c in cc.list_all(limit=100000)}
    events = []
    if os.path.exists(args.events):
        with open(args.events, encoding="utf-8") as f:
            events = [json.loads(x) for x in f if x.strip()]
    added = 0
    for e in events:
        key = (e.get("ts"), e.get("command"), int(e.get("exit_code", 0)))
        if key in existing:
            continue
        if cc.add(e.get("ts"), e.get("op"), e.get("command"),
                  int(e.get("exit_code", 0)), e.get("error", "")):
            added += 1
            existing.add(key)
    all_c = cc.list_all(limit=100000)
    classes = sorted(set(c["death_class"] for c in all_c))
    out = {"note": "P5a.66 回合末收割（只捡真实失败）", "events_read": len(events),
           "added": added, "corpses_total": len(all_c), "death_classes": classes,
           "trigger_line": {"min_corpses": 30, "min_classes": 3},
           "trigger_reached": len(all_c) >= 30 and len(classes) >= 3}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
