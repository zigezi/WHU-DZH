#!/usr/bin/env python3
"""P5a.64 §三：代码操作日志常态化落盘 + 入 code_corpses（域转移采集，零 token）。

用法（opencode 每次代码操作后调用或包一层）：
  python scripts/code_op_log.py --op <op> --cmd "<命令/动作>" --exit <rc> [--error "<错误>"]
  或从 JSONL 批量：python scripts/code_op_log.py --ingest-file <jsonl>
落盘：.agent/logs/code-ops.jsonl（append）；同时死亡事件入 code_corpses 表。

禁令（攒批期）：禁谓词起草（ring_draft 关）、禁代码域资产出生、禁能力声明。只攒尸体。
触发线：code 尸体 ≥30 且 death_class ≥3 → 呈裁者做 Phase 1 再校准。
"""
import argparse
import json
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from monitor import code_corpses as cc  # noqa: E402

LOG = os.path.join(ROOT, ".agent", "logs", "code-ops.jsonl")


def _append(ev):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--op"); ap.add_argument("--cmd"); ap.add_argument("--exit", type=int, default=0)
    ap.add_argument("--error", default=""); ap.add_argument("--ingest-file")
    args = ap.parse_args()
    if args.ingest_file:
        with open(args.ingest_file, encoding="utf-8") as f:
            events = [json.loads(x) for x in f if x.strip()]
    else:
        events = [{"ts": datetime.now().isoformat(timespec="seconds"), "op": args.op,
                   "command": args.cmd, "exit_code": args.exit, "error": args.error}]
    added = 0
    for e in events:
        _append(e)
        if cc.add(e.get("ts"), e.get("op"), e.get("command"),
                  int(e.get("exit_code", 0)), e.get("error", "")):
            added += 1
    total = len(cc.list_all(limit=100000))
    classes = set(c["death_class"] for c in cc.list_all(limit=100000))
    out = {"note": "P5a.64 代码域尸体攒批（零 token；攒批期：只攒尸体不开药）",
           "this_added": added, "corpses_total": total, "death_classes": sorted(classes),
           "trigger_line": {"min_corpses": 30, "min_classes": 3},
           "trigger_reached": total >= 30 and len(classes) >= 3,
           "mine_input": cc.mine_input(), "log": LOG}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
