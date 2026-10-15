#!/usr/bin/env python3
"""P5a.49 §三.C2：E3 先导跑（两阶段）。阶段一=10 题校准探针（含 2 金丝雀）。

真实 agent：单次 DeepSeek 调用产算子（仅函数定义）。判分=隐藏单测（子进程，结构化失败类别）。
  /root/miniconda3/envs/mini-agent/bin/python scripts/e3_pilot.py --stage 1
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
R = os.path.join(ROOT, ".agent", "reports")
sys.path.insert(0, BACKEND)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from e3_executor import build_prompt, build_prompt_v2, build_prompt_v3, run_task  # noqa: E402

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


def extract_code(text):
    text = text or ""
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.S)
    code = m.group(1) if m else text
    return code.strip()


def agent_fn(prompt, task):
    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": "You are a Python operator generator. "
                   "Reply with ONLY the function definition, no prose, no markdown fences."},
                  {"role": "user", "content": prompt}],
        temperature=0)
    usage = getattr(r, "usage", None)
    toks = getattr(usage, "total_tokens", 0) if usage else 0
    return extract_code(r.choices[0].message.content), toks


def run_stage(stage, n_self, n_canary, v2=False, v3=False):
    fname = ("e3-pilot-tasks-v3.json" if v3 else
             "e3-pilot-tasks-v2.json" if v2 else "e3-pilot-tasks.json")
    tasks = json.load(open(os.path.join(R, fname)))["tasks"]
    self_t = [t for t in tasks if not t["is_canary"]]
    can_t = [t for t in tasks if t["is_canary"]]
    sel = self_t[:n_self] + can_t[:n_canary]
    rows = []
    tokens = 0
    for t in sel:
        prompt = (build_prompt_v3(t) if v3 else build_prompt_v2(t) if v2 else build_prompt(t))
        code, tk = agent_fn(prompt, t)
        tokens += tk
        res = run_task(t, code)
        rows.append({"task_id": t["task_id"], "family": t["template_family"],
                     "is_canary": t["is_canary"], "verdict": res["verdict"],
                     "failure_class": res["failure_class"], "tokens": tk,
                     "stderr": res["stderr_tail"][:120]})
    n = len(rows)
    fails = sum(1 for r in rows if not r["verdict"])
    canary = [r for r in rows if r["is_canary"]]
    out = {"note": f"E3 先导阶段{stage}{'-v2' if v2 else ''}", "n": n, "fail": fails,
           "fail_rate": round(fails / n, 3) if n else 0, "tokens": tokens,
           "canary_n": len(canary),
           "canary_fail": sum(1 for r in canary if not r["verdict"]),
           "rows": rows}
    suffix = "-v3" if v3 else "-v2" if v2 else ""
    json.dump(out, open(os.path.join(R, f"e3-pilot-stage{stage}{suffix}.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, ensure_ascii=False, indent=1))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, default=1)
    ap.add_argument("--v2", action="store_true")
    ap.add_argument("--v3", action="store_true")
    args = ap.parse_args()
    if args.v3:
        if args.stage == 1:
            return run_stage(1, n_self=10, n_canary=0, v3=True)
        return run_stage(2, n_self=30, n_canary=0, v3=True)
    if args.stage == 1:
        return run_stage(1, n_self=8, n_canary=2, v2=args.v2)
    return run_stage(2, n_self=30, n_canary=0, v2=args.v2)


if __name__ == "__main__":
    sys.exit(main())
