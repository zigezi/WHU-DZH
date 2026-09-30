#!/usr/bin/env python3
"""P5a.20 便签 3：epoch 先例快照冻结。

epoch **开始时**运行一次，把当前先例库冻结为本轮可见集合；
之后 worker 以 `SA_EPOCH=<N>` 运行，`_inject_precedent` 只读该快照（先前 epoch 沉积）。

  /root/miniconda3/envs/mini-agent/bin/python scripts/freeze_precedents.py --epoch 6
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)

from monitor.trace_store import trace_store  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epoch", type=int, required=True)
    args = ap.parse_args()
    n = trace_store.freeze_precedent_snapshot(args.epoch)
    print(f"[freeze] epoch {args.epoch}: {n} precedents snapshotted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
