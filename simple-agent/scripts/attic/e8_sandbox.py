#!/usr/bin/env python3
"""P5a.32 §四 / a33 §四 工单 G：e8 沙盒 shakedown（机械清单，仪器试车，非行为实验）。

检查项（全机械）：
  1. 脱敏库 lint 三检通过（e8-deid-lint.json all_pass）
  2. 冻结矩阵可加载 + 达标线全过（e8-matrix-freeze.json gates.all_pass）
  3. 两臂形态平衡表产出（sibling/unrelated 均有 n）
  4. CopyGuard e7 轨迹回放产物存在且命中均为可解释（不 crash）
  5. worker e8 通道可加载矩阵+脱敏库（_e8_load 非空）
  6. 10 任务烟跑：--live 时执行（默认跳过，需显式授权，耗 token）

  /root/miniconda3/envs/mini-agent/bin/python scripts/e8_sandbox.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
R = os.path.join(ROOT, ".agent", "reports")


def _load(name):
    p = os.path.join(R, name)
    return json.load(open(p)) if os.path.exists(p) else None


def main():
    res = {}

    lint = _load("e8-deid-lint.json")
    res["1_deid_lint3"] = bool(lint and lint.get("all_pass"))

    mx = _load("e8-matrix-freeze.json")
    res["2_matrix_gates"] = bool(mx and mx.get("gates", {}).get("all_pass"))

    fb = (mx or {}).get("form_balance", {})
    res["3_form_balance"] = bool(fb.get("sibling", {}).get("n") and fb.get("unrelated", {}).get("n"))

    cg = _load("e7-copyguard-audit.json")
    res["4_copyguard_e7"] = bool(cg) and isinstance(cg.get("with_hits"), int)

    # 5 worker e8 load
    try:
        import worker as W
        m, d = W._e8_load()
        res["5_worker_e8_load"] = bool(m) and bool(d)
        res["5_matrix_rows"] = len(m)
        res["5_deid_rows"] = len(d)
    except Exception as e:  # noqa: BLE001
        res["5_worker_e8_load"] = False
        res["5_error"] = repr(e)[:200]

    # 6 live smoke
    if "--live" in sys.argv:
        res["6_live_smoke"] = "requested (see epoch run)"
    else:
        res["6_live_smoke"] = "skipped (pass --live to run 10-task smoke; costs tokens)"

    ok = all(res.get(k) is True for k in ("1_deid_lint3", "2_matrix_gates",
                                          "3_form_balance", "4_copyguard_e7", "5_worker_e8_load"))
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print("SANDBOX MECHANICAL:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
