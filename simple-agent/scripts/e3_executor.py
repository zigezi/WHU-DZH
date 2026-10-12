#!/usr/bin/env python3
"""P5a.49 §三.C2：E3 执行器（算子微任务）：spec → 解 → 隐藏单测判分 → 结构化失败类别。

失败类别：syntax_death / timeout_loop / assert_fail / runtime_exception / pass。
执行隔离：解 + 隐藏单测在**子进程**里跑（真超时，可杀死循环）。

冒烟（零模型 token）：桩 agent 喂参考解→PASS；喂变异体→FAIL（类别正确）；语法错→syntax_death；死循环→timeout_loop。
  /root/miniconda3/envs/mini-agent/bin/python scripts/e3_executor.py --smoke
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, ".agent", "reports")
sys.path.insert(0, os.path.join(ROOT, "scripts"))


def build_prompt(task, examples=None):
    """难度参数（P5a.49 C2）：examples=False 时不给示例（更难）。默认读 env E3_EXAMPLES。"""
    if examples is None:
        examples = os.environ.get("E3_EXAMPLES", "1") == "1"
    base = (f"# Task {task['task_id']} ({task['template_family']})\n"
            f"{task['signature']}\n# {task['doc']}\n")
    if examples:
        base += "# examples:\n" + "\n".join(task["hidden_tests"][:2]) + "\n"
    return base + "# Write ONLY the function definition."


def build_prompt_v2(task):
    """P5a.50/51 变体 B：给坏模块 + 可见测试（v2.1= 仅 happy-path），要求输出修好的函数。"""
    vis = "\n".join(task.get("visible") or task["hidden_tests"][:3])
    return ("# 下面这个 Python 模块可能有 bug。请审查并修复它，使其满足全部测试。\n"
            "# 现可运行的测试（当前已通过）：\n" + vis + "\n# 坏模块：\n" + task["buggy"] + "\n"
            "# 只输出修正后的函数定义（完整函数），不要解释、不要 markdown 围栏。")


def run_task(task, solution_code, timeout=3.0):
    """返回 {verdict, failure_class, stderr_tail}。verdict=1 PASS / 0 FAIL。"""
    prog = solution_code + "\n\n" + "\n".join(task["hidden_tests"]) + "\nprint('__OK__')\n"
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(prog)
        path = f.name
    try:
        p = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        os.unlink(path)
        return {"verdict": 0, "failure_class": "timeout_loop", "stderr_tail": ""}
    os.unlink(path)
    err = p.stderr or ""
    if p.returncode == 0 and "__OK__" in (p.stdout or ""):
        return {"verdict": 1, "failure_class": "pass", "stderr_tail": ""}
    if "SyntaxError" in err or "IndentationError" in err:
        cls = "syntax_death"
    elif "AssertionError" in err:
        cls = "assert_fail"
    else:
        cls = "runtime_exception"
    return {"verdict": 0, "failure_class": cls, "stderr_tail": err.strip().splitlines()[-1] if err.strip() else ""}


# ---- 桩 agent（零模型）----
def stub_reference(prompt, task):
    return task["reference"]


def make_stub_mutant():
    from e3_generator import FAMILIES

    def stub(prompt, task):
        fam = task.get("template_family")
        ms = FAMILIES.get(fam, {}).get("mutants") or []
        return ms[0] if ms else task["reference"] + "\n"
    return stub


def stub_syntax_error(prompt, task):
    return "def broken(:\n    pass"


def stub_infinite_loop(prompt, task):
    name = task["signature"].split("(")[0].replace("def ", "").strip()
    return f"{task['signature']}:\n    while True:\n        pass"


def smoke():
    tasks = json.load(open(os.path.join(R, "e3-pilot-tasks.json")))["tasks"]
    tasks = [t for t in tasks if not t["is_canary"]]
    fams = {}
    for t in tasks:
        fams.setdefault(t["template_family"], t)
    sample = list(fams.values())   # 每族一题
    results = []
    for t in sample:
        ref = run_task(t, stub_reference("", t))
        mut = run_task(t, make_stub_mutant()("", t))
        results.append({"task": t["task_id"], "family": t["template_family"],
                        "ref": ref, "mut": mut,
                        "ok": ref["verdict"] == 1 and mut["verdict"] == 0})
    syn = run_task(sample[0], stub_syntax_error("", sample[0]))
    loop = run_task(sample[0], stub_infinite_loop("", sample[0]), timeout=1.5)
    results.append({"task": "syntax_probe", "family": "-", "ref": {}, "mut": syn,
                    "ok": syn["failure_class"] == "syntax_death"})
    results.append({"task": "loop_probe", "family": "-", "ref": {}, "mut": loop,
                    "ok": loop["failure_class"] == "timeout_loop"})
    all_ok = all(r["ok"] for r in results)
    out = {"note": "E3 执行器冒烟（桩 agent，零模型 token）", "n": len(results),
           "all_pass": all_ok, "results": results}
    json.dump(out, open(os.path.join(R, "e3-executor-smoke.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if all_ok else 1


def smoke_v2():
    tasks = json.load(open(os.path.join(R, "e3-pilot-tasks-v2.json")))["tasks"]
    fams = {}
    for t in tasks:
        fams.setdefault(t["template_family"], t)
    sample = list(fams.values())
    results = []
    for t in sample:
        ref = run_task(t, t["reference"])     # 参考解 → PASS
        bug = run_task(t, t["buggy"])         # 坏模块原样 → FAIL
        results.append({"task": t["task_id"], "family": t["template_family"],
                        "ref": ref["failure_class"], "bug": bug["failure_class"],
                        "ok": ref["verdict"] == 1 and bug["verdict"] == 0})
    all_ok = all(r["ok"] for r in results)
    out = {"note": "E3 v2 执行器冒烟（坏模块原样→FAIL；参考解→PASS；零模型 token）",
           "n": len(results), "all_pass": all_ok, "results": results}
    json.dump(out, open(os.path.join(R, "e3-executor-smoke-v2.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if all_ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--smoke-v2", action="store_true")
    args = ap.parse_args()
    if args.smoke:
        return smoke()
    if args.smoke_v2:
        return smoke_v2()
    print("usage: --smoke | --smoke-v2")
    return 2


if __name__ == "__main__":
    sys.exit(main())
