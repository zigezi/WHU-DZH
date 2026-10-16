#!/usr/bin/env python3
"""P5a.79 §二.2：采集钩子自证电池（naming_proof 式 + 关闭回归；零 token）。

- naming_proof：构造**必败命令**（`bash -c 'false'`），断言 code-ops.jsonl 出现对应条目
  （钩子先证明自己接在真实执行路径上）。
- 行为保真：钩子在位时命令 rc / stdout 不变（不拦截、不改行为）。
- 关闭回归：CODE_OPS_HOOK_DISABLE=1 时**不误记**且行为不变。

  /root/miniconda3/envs/mini-agent/bin/python scripts/op_log_hook_battery.py
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "scripts", "op_log_hook.sh")
R = os.path.join(ROOT, ".agent", "reports")


def _run(cmd, log, *, disabled=False, capture_stderr=False):
    env = dict(os.environ)
    env["BASH_ENV"] = HOOK
    env["CODE_OPS_LOG"] = log
    if disabled:
        env["CODE_OPS_HOOK_DISABLE"] = "1"
    if capture_stderr:
        env["CODE_OPS_CAPTURE_STDERR"] = "1"
    return subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, env=env)


def _read(log):
    if not os.path.exists(log):
        return []
    return [json.loads(x) for x in open(log) if x.strip()]


def main():
    checks = []

    # 1) naming_proof：必败命令须入日志
    t1 = tempfile.mktemp(suffix=".jsonl")
    p = _run("false", t1)
    ev = _read(t1)
    hit = next((e for e in ev if e["exit_code"] != 0), None)
    checks.append({"check": "naming_proof_failing_cmd_logged",
                   "pass": bool(hit) and "false" in hit["command"], "detail": hit})

    # 2) 成功命令也记录，且 rc 保真
    t2 = tempfile.mktemp(suffix=".jsonl")
    p2 = _run("printf hello", t2)
    ev2 = _read(t2)
    checks.append({"check": "success_logged_and_stdout_preserved",
                   "pass": (p2.stdout == "hello" and p2.returncode == 0
                            and len(ev2) == 1 and ev2[0]["exit_code"] == 0)})

    # 3) 行为保真：退出码不被钩子改动
    t3 = tempfile.mktemp(suffix=".jsonl")
    p3 = _run("exit 7", t3)
    checks.append({"check": "exit_code_preserved", "pass": p3.returncode == 7})

    # 4) 关闭回归：禁用路径不误记、行为不变
    t4 = tempfile.mktemp(suffix=".jsonl")
    p4 = _run("false", t4, disabled=True)
    checks.append({"check": "disabled_no_log_no_intercept",
                   "pass": (p4.returncode == 1 and not os.path.exists(t4))})

    # 5) stderr 摘要（可选开启）
    t5 = tempfile.mktemp(suffix=".jsonl")
    _run("echo boom 1>&2", t5, capture_stderr=True)
    ev5 = _read(t5)
    checks.append({"check": "stderr_digest_captured",
                   "pass": bool(ev5) and "boom" in (ev5[0].get("error") or "")})

    n = len(checks)
    passed = sum(1 for c in checks if c["pass"])
    out = {"note": "P5a.79 §二.2 采集钩子自证（naming_proof + 关闭回归；零 token）",
           "hook": "scripts/op_log_hook.sh", "n": n, "passed": passed,
           "all_pass": passed == n, "results": checks}
    json.dump(out, open(os.path.join(R, "op-log-hook-battery.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
