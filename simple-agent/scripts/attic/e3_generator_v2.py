#!/usr/bin/env python3
"""P5a.50 §三：基板变体 B（v2，修 bug 形态）任务装配（零 token）。

免费午餐：灵敏度门杀掉的**变异体**即"带标准答案的坏代码"——任务 = 坏模块(变异体) + 隐藏单测；
修复目标 = 参考解。
  /root/miniconda3/envs/mini-agent/bin/python scripts/e3_generator_v2.py
产出：.agent/reports/e3-pilot-tasks-v2.json、e3-v2-gate.json
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, ".agent", "reports")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from e3_generator import FAMILIES, CANARY, MUT_TRANSFORMS, run_ref  # noqa: E402


def inject_bugs(ref, n_bugs):
    """难度旋钮：对参考解依序施加 n_bugs 个不重叠变异算子 → 多 bug 坏模块。"""
    out, applied = ref, 0
    for a, b in MUT_TRANSFORMS:
        if applied >= n_bugs:
            break
        if a in out and a not in b:
            out2 = out.replace(a, b, 1)
            if out2 != out:
                out, applied = out2, applied + 1
    return out, applied

CANARY_V2 = [
    {"task_id": "E3-C01", "sig": "def has_close_elements(numbers, threshold)",
     "doc": "[public canary] Return True if any two numbers are within threshold.",
     "ref": "def has_close_elements(numbers, threshold):\n    return any(abs(a-b) < threshold for i,a in enumerate(numbers) for b in numbers[i+1:])",
     "buggy": "def has_close_elements(numbers, threshold):\n    return False",
     "tests": ["assert has_close_elements([1.0,2.0,3.0],0.5) == False",
               "assert has_close_elements([1.0,2.8,3.0],0.3) == True",
               "assert has_close_elements([1.0,2.0,3.0],1.5) == True"]},
    {"task_id": "E3-C02", "sig": "def separate_paren_groups(s)",
     "doc": "[public canary] Return list of balanced parenthesized groups.",
     "ref": "def separate_paren_groups(s):\n    out=[];depth=0;cur=''\n    for c in s:\n        cur+=c\n        if c=='(':depth+=1\n        elif c==')':depth-=1\n        if depth==0 and cur.strip():\n            out.append(cur.strip());cur=''\n    return out",
     "buggy": "def separate_paren_groups(s):\n    return [s]",
     "tests": ["assert separate_paren_groups('(()()) ((())) ()') == ['(()())','((()))','()']",
               "assert separate_paren_groups('()') == ['()']"]},
]


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--bugs", type=int, default=1)   # 难度旋钮：注入 bug 数
    ap.add_argument("--out", default="e3-pilot-tasks-v2.json")
    ap.add_argument("--gate", default="e3-v2-gate.json")
    args = ap.parse_args()
    import hashlib
    v1 = json.load(open(os.path.join(R, "e3-pilot-tasks.json")))["tasks"]
    tasks, rejected = [], 0
    for t in v1:
        if t["is_canary"]:
            continue  # 金丝雀用下方专用构造（v1 占位测试无断言）
        fam = t["template_family"]
        ms = FAMILIES[fam].get("mutants") or []
        if not ms:
            rejected += 1
            continue
        ref = t["reference"]
        if args.bugs <= 1:
            buggy = ms[0]                   # 起点：单 bug + 明显变异算子
            bug_kind = f"{fam}::mutant0"
        else:
            buggy, nb = inject_bugs(ref, args.bugs)
            bug_kind = f"{fam}::bugs{nb}"
        if run_ref(buggy, t["hidden_tests"]) or not run_ref(ref, t["hidden_tests"]):
            rejected += 1
            continue
        tasks.append({"task_id": t["task_id"], "template_family": fam,
                      "is_canary": False, "prompt_hash": t["prompt_hash"],
                      "signature": t["signature"], "doc": t["doc"],
                      "buggy": buggy, "hidden_tests": t["hidden_tests"],
                      "reference": ref, "bug_kind": bug_kind})
    for c in CANARY_V2:
        if run_ref(c["buggy"], c["tests"]) or not run_ref(c["ref"], c["tests"]):
            rejected += 1
            continue
        tasks.append({"task_id": c["task_id"], "template_family": "canary",
                      "is_canary": True,
                      "prompt_hash": hashlib.sha256(c["sig"].encode()).hexdigest()[:16],
                      "signature": c["sig"], "doc": c["doc"],
                      "buggy": c["buggy"], "hidden_tests": c["tests"],
                      "reference": c["ref"], "bug_kind": "canary::buggy"})
    gate = {"note": "P5a.50 v2 装配门（坏模块 FAIL ∧ 参考解 PASS）",
            "admitted": len(tasks), "rejected": rejected,
            "self": len([t for t in tasks if not t["is_canary"]]),
            "canary": len([t for t in tasks if t["is_canary"]])}
    json.dump({"note": "E3 v2 任务（坏模块+隐藏单测；修复目标=参考解）",
               "n": len(tasks), "tasks": tasks},
              open(os.path.join(R, "e3-pilot-tasks-v2.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(gate, open(os.path.join(R, "e3-v2-gate.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(gate, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
