#!/usr/bin/env python3
"""P5a.47 §二：C-1 冷启动复现门（零 token）。

全新环境（干净容器），只装入：**资产注册表 + harness + 验证器**，不带任何会话历史/本地卷宗；
跑 B-2 金丝雀电池或锁死 5 任务型；**资产点火且正确 = 资产真实可移植**。
每个资产登记后必过 C-1，作为出生证最后一栏。

  /root/miniconda3/envs/mini-agent/bin/python scripts/c1_coldstart_gate.py --asset lock_order_v1
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
from monitor import provenance  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asset", default="lock_order_v1")
    ap.add_argument("--battery", default="e9_canary_battery.py")
    ap.add_argument("--battery-json", default="e9-canary-battery.json")
    args = ap.parse_args()

    clean = tempfile.mkdtemp(prefix="c1-clean-", dir="/tmp/opencode")
    # 只装入：harness（monitor 资产模块） + 资产注册表 + 验证器（电池）
    os.makedirs(os.path.join(clean, "backend", "monitor"), exist_ok=True)
    os.makedirs(os.path.join(clean, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(clean, ".agent", "reports"), exist_ok=True)
    open(os.path.join(clean, "backend", "monitor", "__init__.py"), "w").close()
    for mod in os.listdir(os.path.join(BACKEND, "monitor")):
        if mod.endswith(".py"):
            shutil.copy(os.path.join(BACKEND, "monitor", mod),
                        os.path.join(clean, "backend", "monitor", mod))
    shutil.copy(os.path.join(ROOT, ".agent", "reports", "assets.json"),
                os.path.join(clean, ".agent", "reports", "assets.json"))
    shutil.copy(os.path.join(ROOT, "scripts", args.battery),
                os.path.join(clean, "scripts", args.battery))

    env = {"PATH": os.environ.get("PATH", ""), "HOME": clean,
           "PYTHONPATH": os.path.join(clean, "backend")}
    proc = subprocess.run([sys.executable, os.path.join(clean, "scripts", args.battery)],
                          cwd=clean, env=env, capture_output=True, text=True, timeout=120)
    bpath = os.path.join(clean, ".agent", "reports", args.battery_json)
    battery = json.load(open(bpath)) if os.path.exists(bpath) else {}
    # 资产注册表在干净环境里可加载且存在该资产
    reg = json.load(open(os.path.join(clean, ".agent", "reports", "assets.json")))
    present = any(a.get("asset_id") == args.asset for a in reg.get("assets", []))

    # P5a.59 §五 保真度增修：名称型守卫须经真实 execute_tool、按生产命名(tau__)过零 token 点火证明
    name_proc = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "sentinel_wiring_battery.py")],
                               cwd=ROOT, capture_output=True, text=True, timeout=180)
    np_path = os.path.join(ROOT, ".agent", "reports", "sentinel-wiring-battery.json")
    naming = json.load(open(np_path)) if os.path.exists(np_path) else {}
    naming_ok = bool(naming.get("all_pass"))
    fired = bool(battery.get("all_pass")) and present and naming_ok
    line = (f"C-1 冷启动复现门：{'PASS' if fired else 'FAIL'}（干净容器 {clean}；"
            f"电池 {battery.get('passed','?')}/{battery.get('n','?')}；资产在场={present}；零 token）")
    if fired:
        provenance.revalidate(args.asset, evidence=line, result="pass")
    line += f"；naming_proof={naming_ok}"
    out = {"asset": args.asset, "clean_dir": clean, "battery": battery.get("all_pass"),
           "battery_passed": battery.get("passed"), "asset_present": present,
           "naming_proof": naming_ok, "c1_pass": fired, "birth_cert_line": line,
           "rc": proc.returncode, "name_rc": name_proc.returncode,
           "stderr": (proc.stderr or "")[-300:]}
    json.dump(out, open(os.path.join(ROOT, ".agent", "reports", "c1-coldstart-gate.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if fired else 1


if __name__ == "__main__":
    sys.exit(main())
