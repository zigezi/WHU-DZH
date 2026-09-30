#!/usr/bin/env python3
"""P5a.20 便签3 自测：测量模式选择器（同族/最早/无同族跳过）+ 固定 50/50 分配。

  /root/miniconda3/envs/mini-agent/bin/python scripts/p5a20_memo3_selftest.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from monitor import precedent_select as ps  # noqa: E402
from monitor.routing import Router  # noqa: E402

CANDS = [
    {"id": 10, "sig": "AAA", "req_id": "t10", "plan": [{"tool": "x"}], "content": "c"},
    {"id": 30, "sig": "AAA", "req_id": "t30", "plan": [{"tool": "y"}], "content": "c"},
    {"id": 20, "sig": "BBB", "req_id": "t20", "plan": [{"tool": "z"}], "content": "c"},
]


def t1_same_family_oldest():
    b = ps.select(CANDS, "AAA")
    assert b is not None and b["id"] == 10, b  # 最早沉积，而非最大 id
    print("  t1 same-family->oldest OK id=", b["id"])


def t2_none():
    assert ps.select(CANDS, "CCC") is None
    print("  t2 no same-family -> None OK")


def t3_hash_deterministic():
    p = [{"tool": "a", "args": {"k": 1}}]
    assert ps.content_hash(p) == ps.content_hash(p)
    assert len(ps.content_hash(p)) == 16
    print("  t3 content_hash OK", ps.content_hash(p))


def t4_measurement_balanced():
    r = Router()
    arms = [r.choose_measurement(f"TAU-A-{i:03d}") for i in range(200)]
    n_pa = sum(1 for a in arms if a == "precedent-assisted")
    assert 60 <= n_pa <= 140, n_pa          # 近似 50/50
    assert arms == [r.choose_measurement(f"TAU-A-{i:03d}") for i in range(200)]  # 确定性
    print(f"  t4 measurement 50/50 OK: {n_pa}/200 precedent-assisted, deterministic")


if __name__ == "__main__":
    print("[memo3 selftest]")
    t1_same_family_oldest()
    t2_none()
    t3_hash_deterministic()
    t4_measurement_balanced()
    print("ALL PASS")
