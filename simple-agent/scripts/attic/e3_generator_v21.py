#!/usr/bin/env python3
"""P5a.51：基板 v2.1（静默 bug）任务装配（零 token）。

配置：可见测试=仅 happy-path；隐藏测试=happy+boundary；坏模块=**边界/微妙类**静默 bug
（通过 happy、仅边界失败）。
  /root/miniconda3/envs/mini-agent/bin/python scripts/e3_generator_v21.py
产出：.agent/reports/e3-pilot-tasks-v2.json（供 e3_pilot --v2 复用）、e3-v21-gate.json
"""
import hashlib
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, ".agent", "reports")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from e3_generator import run_ref  # noqa: E402


def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a


REF = {
    "clamp": "def clamp(x, lo, hi):\n    return max(lo, min(x, hi))",
    "gcd": "def gcd(a, b):\n    while b:\n        a, b = b, a % b\n    return a",
    "count_vowels": "def count_vowels(s):\n    return sum(1 for c in s if c in 'aeiou')",
}
# 静默 bug：通过 happy、仅边界失败
BUGGY = {
    "clamp": "def clamp(x, lo, hi):\n    return min(x, hi)",          # 丢下界
    "gcd": "def gcd(a, b):\n    while b > 1:\n        a, b = b, a % b\n    return a",  # b==1 边界
    "count_vowels": "def count_vowels(s):\n    return sum(1 for c in s if c in 'aeio')",  # 漏 u
}
# 第 2 个静默 bug（a51 预注册调整路径）：同族再注入一个边界 bug
BUGGY2 = {
    "clamp": "def clamp(x, lo, hi):\n    return min(x, hi) if x > lo else lo - 1",  # 丢下界 + 下界 off-by-one
    "gcd": "def gcd(a, b):\n    if a == b:\n        return 0\n    while b > 1:\n        a, b = b, a % b\n    return a",  # b==1 + a==b
    "count_vowels": "def count_vowels(s):\n    return sum(1 for c in s if c in 'eio')",  # 漏 a 与 u
}


def gen_cases(fam, rng):
    if fam == "clamp":
        lo, hi = rng.randint(-10, -1), rng.randint(1, 10)
        x = rng.randint(lo, hi)
        happy = [f"assert clamp({x},{lo},{hi}) == {x}",
                 f"assert clamp({hi},{lo},{hi}) == {hi}"]
        boundary = [f"assert clamp({lo-5},{lo},{hi}) == {lo}"]
        sig, doc = "def clamp(x, lo, hi)", "Return x clipped to [lo, hi]."
    elif fam == "gcd":
        b = rng.randint(2, 9)
        a = b * rng.randint(2, 6)
        happy = [f"assert gcd({a},{b}) == {_gcd(a,b)}",
                 f"assert gcd({a},{b+1}) == {_gcd(a,b+1)}"]   # a≠b，避开 a==b 边界
        boundary = [f"assert gcd({a},1) == 1"]
        sig, doc = "def gcd(a, b)", "Return the greatest common divisor of a,b (>0)."
    else:  # count_vowels
        s = "".join(rng.choice("aeioabc") for _ in range(rng.randint(4, 10)))  # 无 u
        happy = [f"assert count_vowels({s!r}) == {sum(1 for c in s if c in 'aeiou')}"]
        boundary = [f"assert count_vowels('u') == 1", f"assert count_vowels('queue') == 4"]
        sig, doc = "def count_vowels(s)", "Count vowels (aeiou) in lowercase string s."
    return sig, doc, happy, boundary


CANARY = [
    {"task_id": "E3-C01", "fam": "canary",
     "sig": "def has_close_elements(numbers, threshold)",
     "doc": "[public canary] Return True if any two numbers are within threshold.",
     "ref": "def has_close_elements(numbers, threshold):\n    return any(abs(a-b) < threshold for i,a in enumerate(numbers) for b in numbers[i+1:])",
     "buggy": "def has_close_elements(numbers, threshold):\n    return any(abs(a-b) <= threshold for i,a in enumerate(numbers) for b in numbers[i+1:])",
     "happy": ["assert has_close_elements([1.0,2.0,3.0],0.5) == False"],
     "boundary": ["assert has_close_elements([1.0,2.0,3.0],1.0) == False"]},   # <= 边界
]


def main():
    rng = random.Random(20261012)
    fams = list(REF)
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--twobug", action="store_true"); _a = ap.parse_args()
    tasks, rejected = [], 0
    for i in range(8):
        fam = fams[i % len(fams)]
        sig, doc, happy, boundary = gen_cases(fam, rng)
        hidden = happy + boundary
        buggy, ref = (BUGGY2 if _a.twobug else BUGGY)[fam], REF[fam]
        if run_ref(buggy, happy) is False or run_ref(buggy, hidden) or not run_ref(ref, hidden):
            rejected += 1
            continue
        tasks.append({"task_id": f"E3V21-{i:02d}", "template_family": fam,
                      "is_canary": False,
                      "prompt_hash": hashlib.sha256((sig + str(happy)).encode()).hexdigest()[:16],
                      "signature": sig, "doc": doc, "buggy": buggy,
                      "visible": happy, "hidden_tests": hidden, "reference": ref,
                      "bug_kind": f"{fam}::silent_boundary"})
    for c in CANARY:
        hidden = c["happy"] + c["boundary"]
        if run_ref(c["buggy"], c["happy"]) is False or run_ref(c["buggy"], hidden) or not run_ref(c["ref"], hidden):
            rejected += 1
            continue
        tasks.append({"task_id": c["task_id"], "template_family": "canary", "is_canary": True,
                      "prompt_hash": hashlib.sha256(c["sig"].encode()).hexdigest()[:16],
                      "signature": c["sig"], "doc": c["doc"], "buggy": c["buggy"],
                      "visible": c["happy"], "hidden_tests": hidden, "reference": c["ref"],
                      "bug_kind": "canary::silent"})
    gate = {"note": "P5a.51 v2.1 装配门（坏模块过 happy ∧ 过不了 hidden ∧ 参考解过 hidden；静默边界 bug）",
            "admitted": len(tasks), "rejected": rejected,
            "self": len([t for t in tasks if not t["is_canary"]]),
            "canary": len([t for t in tasks if t["is_canary"]])}
    json.dump({"note": "E3 v2.1 静默 bug 任务（visible=happy；hidden=happy+boundary）",
               "n": len(tasks), "tasks": tasks},
              open(os.path.join(R, "e3-pilot-tasks-v2.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(gate, open(os.path.join(R, "e3-v21-gate.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(gate, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
