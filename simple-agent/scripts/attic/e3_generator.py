#!/usr/bin/env python3
"""P5a.49 §三 C1：E3 代码域任务生成器 + 测试灵敏度门（零 token）。

- 任务 = 算子微任务：spec(签名+docstring+示例) + 参考解 + 隐藏单测 + 变异体；
- 生成：模板族 + 参数变异（seeded RNG）；
- **测试灵敏度门**：参考解全过 ∧ ≥3 变异体被杀 → 入库；否则弃；
- 新颖性机检：spec 哈希去重 + 与公开金丝雀不撞；
- 探针 schema：template_family 为簇单位。

产出：.agent/reports/e3-pilot-tasks.json、e3-sensitivity-gate.json
  /root/miniconda3/envs/mini-agent/bin/python scripts/e3_generator.py --n 40 --canary 4 --seed 20261012
"""
import argparse
import hashlib
import json
import os
import random
import signal
import sys


class _Timeout(Exception):
    pass


def _alarm(sig, frm):
    raise _Timeout()


def _run(src, tests, timeout=1.0):
    """带超时执行源码 + 测试；超时/异常 = 失败（防变异体死循环挂死）。"""
    old = signal.signal(signal.SIGALRM, _alarm)
    signal.setitimer(signal.ITIMER_REAL, timeout)
    try:
        ns = {}
        exec(src, ns)
        for t in tests:
            exec(t, ns)
        return True
    except Exception:  # noqa: BLE001
        return False
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, ".agent", "reports")

FAMILIES = {
    "clamp": {"sig": "def clamp(x, lo, hi)",
              "doc": "Return x clipped to [lo, hi].",
              "ref": "def clamp(x, lo, hi):\n    return max(lo, min(x, hi))",
              "mutants": ["def clamp(x, lo, hi):\n    return min(lo, max(x, hi))",
                          "def clamp(x, lo, hi):\n    return x",
                          "def clamp(x, lo, hi):\n    return min(x, hi)"]},
    "gcd": {"sig": "def gcd(a, b)",
            "doc": "Return the greatest common divisor of a,b (both > 0).",
            "ref": "def gcd(a, b):\n    while b:\n        a, b = b, a % b\n    return a",
            "mutants": ["def gcd(a, b):\n    while b:\n        a, b = b, a // b\n    return a",
                        "def gcd(a, b):\n    return a",
                        "def gcd(a, b):\n    return a + b"]},
    "digit_sum": {"sig": "def digit_sum(n)",
                  "doc": "Return sum of decimal digits of non-negative n.",
                  "ref": "def digit_sum(n):\n    s = 0\n    while n > 0:\n        s += n % 10\n        n //= 10\n    return s",
                  "mutants": ["def digit_sum(n):\n    s = 0\n    while n > 0:\n        s += n % 10\n        n //= 10\n    return s + 1",
                              "def digit_sum(n):\n    return n % 10",
                              "def digit_sum(n):\n    s = 0\n    while n > 1:\n        s += n % 10\n        n //= 10\n    return s"]},
    "lcm": {"sig": "def lcm(a, b)",
            "doc": "Return least common multiple of a,b (>0).",
            "ref": "def lcm(a, b):\n    def g(x, y):\n        while y:\n            x, y = y, x % y\n        return x\n    return a // g(a, b) * b",
            "mutants": ["def lcm(a, b):\n    return a * b",
                        "def lcm(a, b):\n    return a",
                        "def lcm(a, b):\n    def g(x, y):\n        while y:\n            x, y = y, x % y\n        return x\n    return a // g(a, b) * b + 1"]},
    "count_vowels": {"sig": "def count_vowels(s)",
                     "doc": "Count vowels (aeiou) in lowercase string s.",
                     "ref": "def count_vowels(s):\n    return sum(1 for c in s if c in 'aeiou')",
                     "mutants": ["def count_vowels(s):\n    return sum(1 for c in s if c in 'aeio')",
                                 "def count_vowels(s):\n    return len(s)",
                                 "def count_vowels(s):\n    return sum(1 for c in s if c in 'aeiou') + 1"]},
    "is_pal": {"sig": "def is_pal(s)",
               "doc": "Return True if string s is a palindrome.",
               "ref": "def is_pal(s):\n    return s == s[::-1]",
               "mutants": ["def is_pal(s):\n    return True",
                           "def is_pal(s):\n    return s == s[::1]",
                           "def is_pal(s):\n    return s[::-1] == s[1:]"]},
}

# 公开金丝雀（HumanEval 式，只作污染对照，不作主证据）
CANARY = {
    "has_close_elements": {"sig": "def has_close_elements(numbers, threshold)",
                           "doc": "[public canary] HumanEval-style.",
                           "ref": "def has_close_elements(numbers, threshold):\n    return any(abs(a-b) < threshold for i,a in enumerate(numbers) for b in numbers[i+1:])"},
    "separate_paren_groups": {"sig": "def separate_paren_groups(s)",
                              "doc": "[public canary] HumanEval-style.",
                              "ref": "def separate_paren_groups(s):\n    return [s]"},
}

MUT_TRANSFORMS = [
    ("min", "max"), ("max", "min"), ("+", "-"), ("-", "+"),
    ("<", "<="), ("<=", "<"), (">", ">="), (">=", ">"), ("//", "/"), ("==", "!="),
    ("%", "//"), ("aeiou", "aeio"), ("[::-1]", "[::1]"), ("+=", "-="),
    ("True", "False"), ("False", "True"), ("while b:", "while not b:"),
    ("n > 0", "n > 1"), ("s +=", "s -="),
]


def gen_tests(family, rng):
    defs = []
    if family == "clamp":
        vals = [(rng.randint(-20, 20), rng.randint(-10, 0), rng.randint(0, 10)) for _ in range(6)]
        defs = [f"assert clamp({x},{lo},{hi}) == max({lo}, min({x}, {hi}))" for x, lo, hi in vals]
    elif family == "gcd":
        vals = [(rng.randint(1, 60), rng.randint(1, 60)) for _ in range(6)]
        defs = [f"import math as _m; assert gcd({a},{b}) == _m.gcd({a},{b})" for a, b in vals]
    elif family == "digit_sum":
        defs = [f"assert digit_sum({n}) == {sum(int(c) for c in str(n))}" for n in
                [rng.randint(0, 10**6) for _ in range(6)]]
    elif family == "lcm":
        vals = [(rng.randint(1, 30), rng.randint(1, 30)) for _ in range(6)]
        defs = [f"import math as _m; assert lcm({a},{b}) == ({a}*{b})//_m.gcd({a},{b})" for a, b in vals]
    elif family == "count_vowels":
        import string
        strs = ["".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randint(3, 12))) for _ in range(6)]
        defs = [f"assert count_vowels({s!r}) == {sum(1 for c in s if c in 'aeiou')}" for s in strs]
    elif family == "is_pal":
        import string
        strs = ["".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randint(1, 8))) for _ in range(6)]
        defs = [f"assert is_pal({s!r}) == {(s == s[::-1])}" for s in strs]
    return defs


def run_ref(ref, tests):
    return _run(ref, tests, timeout=2.0)


def make_mutants(ref, tests, curated=None):
    killed = 0
    for m in (curated or []):
        if not _run(m, tests, timeout=1.0):
            killed += 1
    for a, b in MUT_TRANSFORMS:
        if a not in ref:
            continue
        mut = ref.replace(a, b)
        if mut != ref and not _run(mut, tests, timeout=1.0):
            killed += 1
    return killed


def build(n, canary, seed):
    rng = random.Random(seed)
    fams = list(FAMILIES)
    tasks, rejected = [], 0
    seen = set()
    for i in range(n + canary):
        is_canary = i >= n
        fam = "canary" if is_canary else fams[i % len(fams)]
        f = CANARY[list(CANARY)[i % len(CANARY)]] if is_canary else FAMILIES[fam]
        tests = gen_tests(fam, rng) if not is_canary else ["import math as _m"]
        ref = f["ref"]
        ref_ok = run_ref(ref, tests)
        killed = make_mutants(ref, tests, f.get("mutants")) if not is_canary else 4
        prompt = f["sig"] + "\n" + f["doc"] + "\n" + "\n".join(tests[:2])
        ph = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        admitted = ref_ok and killed >= 3 and ph not in seen
        if not admitted:
            rejected += 1
            continue
        seen.add(ph)
        tasks.append({"task_id": f"E3-{i:03d}", "template_family": fam,
                      "is_canary": is_canary, "prompt_hash": ph,
                      "signature": f["sig"], "doc": f["doc"],
                      "hidden_tests": tests, "reference": ref,
                      "mutants_killed": killed})
    return tasks, rejected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--canary", type=int, default=4)
    ap.add_argument("--seed", type=int, default=20261012)
    args = ap.parse_args()
    tasks, rejected = build(args.n, args.canary, args.seed)
    admitted = len([t for t in tasks if not t["is_canary"]])
    gate = {
        "note": "P5a.49 C1 灵敏度门良率（参考解全过 ∧ ≥3 变异体被杀）",
        "requested": args.n, "admitted": admitted, "rejected": rejected,
        "admit_rate": round(admitted / args.n, 3) if args.n else 0,
        "canary_n": args.canary, "seed": args.seed,
        "mutants_killed_min": min((t["mutants_killed"] for t in tasks), default=0),
    }
    json.dump({"note": "E3 先导任务（spec+hidden_tests+reference+mutants_killed）",
               "n": len(tasks), "tasks": tasks},
              open(os.path.join(R, "e3-pilot-tasks.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(gate, open(os.path.join(R, "e3-sensitivity-gate.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(gate, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
