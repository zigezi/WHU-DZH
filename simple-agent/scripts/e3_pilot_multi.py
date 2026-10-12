#!/usr/bin/env python3
"""P5a.53：多步 agent 先导（10 探针）+ 双轴判据（难度轴 fail_rate∈[20,70] ∧ 过程轴 process_deaths>0）。
  /root/miniconda3/envs/mini-agent/bin/python scripts/e3_pilot_multi.py --stage 1
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
R = os.path.join(ROOT, ".agent", "reports")
sys.path.insert(0, BACKEND)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from e3_executor_multi import detect_process_deaths, run_tests  # noqa: E402

_env = {}
with open(os.path.join(BACKEND, ".env"), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            _env[k.strip()] = v.strip()
from openai import OpenAI  # noqa: E402

MODEL = os.getenv("MODEL_NAME", "deepseek-chat")
client = OpenAI(api_key=_env["DEEPSEEK_API_KEY"],
                base_url=_env.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"))

TOOLS = [
    {"type": "function", "function": {"name": "read_file", "description": "Read current module source.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "run_visible_tests", "description": "Run the visible tests; returns PASS/FAIL.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "edit_file", "description": "Replace the module source with fixed code.", "parameters": {"type": "object", "properties": {"source": {"type": "string"}}, "required": ["source"]}}},
    {"type": "function", "function": {"name": "submit", "description": "Declare the fix complete.", "parameters": {"type": "object", "properties": {}}}},
]


def run_episode(task, max_steps=20):
    source = task["buggy"]
    traj, tokens = [], 0
    messages = [
        {"role": "system", "content": "You fix bugs in Python modules using the provided tools. "
         "Read the module, run the visible tests, edit to fix, rerun, then submit."},
        {"role": "user", "content": "模块源码：\n" + source + "\n可见测试：\n" +
         "\n".join(task["visible"]) + "\n请修复并用工具完成。"},
    ]
    for _ in range(max_steps):
        r = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS, temperature=0)
        tokens += getattr(getattr(r, "usage", None), "total_tokens", 0) or 0
        msg = r.choices[0].message
        tcs = msg.tool_calls or []
        if not tcs:
            messages.append({"role": "assistant", "content": msg.content or ""})
            messages.append({"role": "user", "content": "请使用工具（read_file/run_visible_tests/edit_file/submit）。"})
            continue
        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": tcs})
        submitted = False
        for tc in tcs:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except Exception:  # noqa: BLE001
                args = {}
            if name == "submit":
                traj.append({"tool": "submit"}); messages.append({"role": "tool", "tool_call_id": tc.id, "content": "submitted"}); submitted = True
            elif name == "read_file":
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": source}); traj.append({"tool": "read_file", "result": "ok"})
            elif name == "run_visible_tests":
                r = run_tests(source, task["visible"]); messages.append({"role": "tool", "tool_call_id": tc.id, "content": r}); traj.append({"tool": "run_visible_tests", "result": r})
            elif name == "edit_file":
                source = args.get("source") or source; messages.append({"role": "tool", "tool_call_id": tc.id, "content": "edited"}); traj.append({"tool": "edit_file", "result": "ok"})
            else:
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": "unknown"}); traj.append({"tool": name, "result": "ok"})
        if submitted:
            break
    else:
        traj.append({"tool": "max_steps"})
    hid = run_tests(source, task["hidden_tests"])
    verdict = 1 if hid == "PASS" else 0
    return {"verdict": verdict, "failure_class": "pass" if verdict else "assert_fail",
            "trajectory": traj, "process_deaths": detect_process_deaths(traj), "tokens": tokens}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, default=1)
    args = ap.parse_args()
    tasks = json.load(open(os.path.join(R, "e3-pilot-tasks-v3.json")))["tasks"]
    n = 10 if args.stage == 1 else 14
    sel = [t for t in tasks if not t["is_canary"]][:n]
    rows, tokens, pd_count = [], 0, 0
    for t in sel:
        res = run_episode(t)
        tokens += res["tokens"]
        pd_count += len(res["process_deaths"])
        rows.append({"task_id": t["task_id"], "family": t["template_family"],
                     "verdict": res["verdict"], "failure_class": res["failure_class"],
                     "process_deaths": res["process_deaths"], "steps": len(res["trajectory"]),
                     "tokens": res["tokens"]})
    fail = sum(1 for r in rows if not r["verdict"])
    fail_rate = round(fail / len(rows), 3) if rows else 0
    out = {"note": f"多步 agent 先导 阶段{args.stage}", "n": len(rows), "fail": fail,
           "fail_rate": fail_rate, "tokens": tokens,
           "process_death_total": pd_count,
           "difficulty_axis_ok": 0.20 <= fail_rate <= 0.70,
           "process_axis_ok": pd_count > 0,
           "rows": rows}
    json.dump(out, open(os.path.join(R, f"e3-pilot-multi-stage{args.stage}.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, ensure_ascii=False, indent=1))
    for r in rows:
        print("  ", r["task_id"], "v=", r["verdict"], "pd=", r["process_deaths"], "steps=", r["steps"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
