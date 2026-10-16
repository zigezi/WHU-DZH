#!/usr/bin/env python3
"""P5a.77 §二.2：全量电池回归扫（常设卫生，零 token）+ 注册表不变性断言。

- 发现 `scripts/*_battery.py` + `scripts/firing_audit.py`，逐个 subprocess 跑；
- 扫前/扫后对生产注册表 `.agent/reports/assets.json` 取 sha256，**不等即 RED**（DC-9 封堵）；
- 输出 `.agent/reports/battery-regression-sweep.json`。

  /root/miniconda3/envs/mini-agent/bin/python scripts/regression_sweep.py
"""
import glob
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, ".agent", "reports")
REGISTRY = os.path.join(R, "assets.json")


def _sha(path):
    if not os.path.exists(path):
        return None
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def main():
    scripts = sorted(glob.glob(os.path.join(ROOT, "scripts", "*_battery.py")))
    scripts += [os.path.join(ROOT, "scripts", "firing_audit.py")]
    reg_before = _sha(REGISTRY)
    results = []
    for s in scripts:
        p = subprocess.run([sys.executable, s], capture_output=True, text=True, cwd=ROOT)
        results.append({"file": os.path.basename(s), "rc": p.returncode})
    reg_after = _sha(REGISTRY)
    invariant_ok = (reg_before == reg_after)
    all_rc_ok = all(r["rc"] == 0 for r in results)
    out = {
        "note": "P5a.77 §二.2 全量电池回归扫（零 token；注册表不变性断言）",
        "token": 0,
        "batteries": len(scripts) - 1,
        "firing_audit": True,
        "results": results,
        "all_rc_ok": all_rc_ok,
        "registry_sha_before": reg_before,
        "registry_sha_after": reg_after,
        "registry_invariant_ok": invariant_ok,
        "verdict": "GREEN" if (all_rc_ok and invariant_ok) else "RED",
    }
    json.dump(out, open(os.path.join(R, "battery-regression-sweep.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["verdict"] == "GREEN" else 1


if __name__ == "__main__":
    sys.exit(main())
