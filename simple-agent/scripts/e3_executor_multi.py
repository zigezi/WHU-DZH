#!/usr/bin/env python3
"""P5a.53：多步执行器（agent 回路四工具）+ 过程型死亡检测（零 token 冒烟可验）。

工具：read_file / run_visible_tests / edit_file / submit（显式）。
隐藏测试在 submit 后由执行器**外部**判分；可见测试只读；步数上限 20；轨迹入 schema。
过程型死亡检测（确定性，看轨迹）：
  premature_done / test_loop / partial_fix_plateau / regression_break。
"""
import json
import os
import signal
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, ".agent", "reports")
MAX_STEPS = 20


class _T(Exception):
    pass


def _alarm(s, f):
    raise _T()


def run_tests(source, tests, timeout=2.0):
    """module source + tests 在子进程执行；返回 'PASS'/'FAIL'。"""
    prog = source + "\n\n" + "\n".join(tests) + "\nprint('__OK__')\n"
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(prog)
        path = f.name
    try:
        p = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=timeout)
        ok = p.returncode == 0 and "__OK__" in (p.stdout or "")
    except subprocess.TimeoutExpired:
        ok = False
    finally:
        os.unlink(path)
    return "PASS" if ok else "FAIL"


def detect_process_deaths(traj):
    """确定性过程型死亡检测（traj 元素：{tool, result?}）。"""
    deaths = []
    tools = [t["tool"] for t in traj]
    # premature_done：submit 前无成功 visible，或 submit 前最后一次 visible=FAIL，或提交前有未复跑的 edit
    if tools and tools[-1] == "submit":
        vis = [t for t in traj if t["tool"] == "run_visible_tests"]
        edits_since_vis = False
        seen_vis = False
        for t in traj[:-1]:
            if t["tool"] == "run_visible_tests":
                seen_vis = True
                edits_since_vis = False
            elif t["tool"] == "edit_file":
                edits_since_vis = True
        last_vis = vis[-1]["result"] if vis else None
        if not vis or last_vis == "FAIL" or edits_since_vis:
            deaths.append("premature_done")
    # test_loop：连续 ≥3 次 run_visible_tests 无 edit
    run = 0
    for t in traj:
        if t["tool"] == "run_visible_tests":
            run += 1
            if run >= 3:
                deaths.append("test_loop")
                break
        elif t["tool"] == "edit_file":
            run = 0
    # partial_fix_plateau：≥4 次 edit 且从未 visible PASS
    edits = sum(1 for t in traj if t["tool"] == "edit_file")
    any_pass = any(t.get("result") == "PASS" for t in traj if t["tool"] == "run_visible_tests")
    if edits >= 4 and not any_pass:
        deaths.append("partial_fix_plateau")
    # regression_break：曾 visible PASS，其后 edit 使可见失败并提交
    passed_once = False
    for i, t in enumerate(traj):
        if t["tool"] == "run_visible_tests" and t.get("result") == "PASS":
            passed_once = True
        if passed_once and t["tool"] == "run_visible_tests" and t.get("result") == "FAIL":
            deaths.append("regression_break")
            break
    return sorted(set(deaths))


def run_episode(task, step_fn, max_steps=MAX_STEPS):
    """step_fn(history, source, task) -> (tool, args)。返回 verdict/traj/process_deaths。"""
    source = task["buggy"]
    traj = []
    for _ in range(max_steps):
        tool, args = step_fn(traj, source, task)
        if tool == "submit":
            traj.append({"tool": "submit"})
            break
        if tool == "read_file":
            traj.append({"tool": "read_file", "result": "ok"})
        elif tool == "run_visible_tests":
            r = run_tests(source, task["visible"])
            traj.append({"tool": "run_visible_tests", "result": r})
        elif tool == "edit_file":
            source = args.get("source", source)
            traj.append({"tool": "edit_file", "result": "ok"})
        else:
            traj.append({"tool": "noop", "result": "ok"})
    else:
        traj.append({"tool": "max_steps"})
    hid = run_tests(source, task["hidden_tests"])
    verdict = 1 if hid == "PASS" else 0
    fc = "pass" if verdict else ("timeout_loop" if hid == "timeout" else "assert_fail")
    return {"verdict": verdict, "failure_class": fc, "trajectory": traj,
            "process_deaths": detect_process_deaths(traj), "final_source": source}


# ---- 桩 step_fn（零模型）----
def stub_good(traj, source, task):
    tools = [t["tool"] for t in traj]
    if "run_visible_tests" in tools:          # 改并复跑后提交
        return "submit", {}
    if "edit_file" in tools:
        return "run_visible_tests", {}
    return "edit_file", {"source": task["reference"]}


def stub_lazy(traj, source, task):
    return "submit", {}                      # 不读不跑不改 → premature_done


def stub_loop(traj, source, task):
    if sum(1 for t in traj if t["tool"] == "run_visible_tests") < 3:
        return "run_visible_tests", {}
    return "submit", {}


def smoke():
    tasks = json.load(open(os.path.join(R, "e3-pilot-tasks-v3.json")))["tasks"]
    t = tasks[0]
    good = run_episode(t, stub_good)
    lazy = run_episode(t, stub_lazy)
    loop = run_episode(t, stub_loop)
    checks = {
        "good_pass": good["verdict"] == 1 and not good["process_deaths"],
        "lazy_premature_done": "premature_done" in lazy["process_deaths"] and lazy["verdict"] == 0,
        "loop_detected": "test_loop" in loop["process_deaths"],
    }
    out = {"note": "多步执行器冒烟（桩，零 token）", "checks": checks,
           "good": {"v": good["verdict"], "pd": good["process_deaths"]},
           "lazy": {"v": lazy["verdict"], "pd": lazy["process_deaths"]},
           "loop": {"v": loop["verdict"], "pd": loop["process_deaths"]},
           "all_pass": all(checks.values())}
    json.dump(out, open(os.path.join(R, "e3-executor-multi-smoke.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(smoke())
