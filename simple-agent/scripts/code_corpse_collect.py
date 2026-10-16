#!/usr/bin/env python3
"""P5a.62 §四：代码操作日志 → 代码域尸体库（零 token）。
日志格式：JSONL，每行 {ts, op, command, exit_code, error}。
  /root/miniconda3/envs/mini-agent/bin/python scripts/code_corpse_collect.py --log <file.jsonl>
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from monitor import code_corpses as cc  # noqa: E402

R = os.path.join(ROOT, ".agent", "reports")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=None)
    ap.add_argument("--demo", action="store_true", help="用内置样例证明管线（零 token）")
    args = ap.parse_args()
    lines = []
    if args.demo:
        lines = [
            {"ts": "2026-10-13T16:00:00", "op": "run_tests", "command": "pytest -q", "exit_code": 1, "error": "AssertionError"},
            {"ts": "2026-10-13T16:01:00", "op": "build", "command": "python -c import x", "exit_code": 1, "error": "ModuleNotFoundError: x"},
            {"ts": "2026-10-13T16:02:00", "op": "edit", "command": "apply_patch", "exit_code": 0, "error": ""},
        ]
    elif args.log:
        with open(args.log, encoding="utf-8") as f:
            lines = [json.loads(x) for x in f if x.strip()]
    else:
        print("need --log or --demo"); return 2
    added = 0
    for e in lines:
        if cc.add(e.get("ts"), e.get("op"), e.get("command"), int(e.get("exit_code", 0)), e.get("error", "")):
            added += 1
    out = {"note": "P5a.62 代码域尸体采集（日志→死亡事件）", "lines": len(lines),
           "added_corpses": added, "mine_input": cc.mine_input()}
    json.dump(out, open(os.path.join(R, "code-corpse-collect.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
