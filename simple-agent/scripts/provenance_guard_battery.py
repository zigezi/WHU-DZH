#!/usr/bin/env python3
"""P5a.82 §四：DC-9 写路径守卫电池（全部写路径 × 沙盒/生产授权；零 token）。

隔离：把 provenance 的 PRODUCTION_FILE/FILE 指向临时文件，**绝不触碰真实注册表**。
验证：
  A. 沙盒路径（SA_REGISTRY_PATH）下，所有写函数可写；
  B. 生产路径（env 未设）下，所有写函数**缺省拒绝**（PermissionError）；
  C. 生产路径 + SA_REGISTRY_PRODUCTION=1 / production=True → 允许。

  /root/miniconda3/envs/mini-agent/bin/python scripts/provenance_guard_battery.py
"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from monitor import provenance as p  # noqa: E402

R = os.path.join(ROOT, ".agent", "reports")
SEED = {"asset_id": "a1", "type": "interceptor_rule", "validated_domain": "tau",
        "credit_level": "T1_candidate", "status": "active", "evidence": "seed"}
NEW = dict(SEED, asset_id="a2")

# 隔离：PRODUCTION_FILE 与 FILE 都指向同一临时文件（即"伪生产"）
_prod = tempfile.mktemp(suffix="-prod.json")
json.dump({"assets": [SEED]}, open(_prod, "w"))
p.PRODUCTION_FILE = _prod
p.FILE = _prod

WRITERS = {
    "register_asset": lambda prod=False: p.register_asset(dict(NEW), production=prod),
    "set_credit": lambda prod=False: p.set_credit("a1", "field_validated", "e", production=prod),
    "shadow_event": lambda prod=False: p.shadow_event("a1", "FAIL", production=prod),
    "patch_asset": lambda prod=False: p.patch_asset("a1", production=prod, note="x"),
    "supersede": lambda prod=False: p.supersede("a1", "a2", "r", production=prod),
    "revoke": lambda prod=False: p.revoke("a1", "r", production=prod),
    "revalidate": lambda prod=False: p.revalidate("a1", "e", production=prod),
}

checks = []


def run(fn, prod=False):
    try:
        fn(prod)
        return "ok"
    except PermissionError:
        return "refused"
    except Exception as e:  # noqa: BLE001
        return f"err:{type(e).__name__}"


def main():
    # A) 沙盒：全部可写
    os.environ["SA_REGISTRY_PATH"] = tempfile.mktemp(suffix="-sandbox.json")
    for name, fn in WRITERS.items():
        r = run(fn)
        checks.append({"check": f"sandbox_ok::{name}", "pass": r == "ok", "got": r})

    # B) 生产（env 未设）：全部缺省拒绝
    os.environ.pop("SA_REGISTRY_PATH", None)
    os.environ.pop("SA_REGISTRY_PRODUCTION", None)
    for name, fn in WRITERS.items():
        r = run(fn)
        checks.append({"check": f"production_refused::{name}", "pass": r == "refused", "got": r})

    # C) 生产 + 显式授权：允许
    for name in ("set_credit", "revalidate"):
        r = run(WRITERS[name], prod=True)
        checks.append({"check": f"production_allowed_kwarg::{name}", "pass": r == "ok", "got": r})
    os.environ["SA_REGISTRY_PRODUCTION"] = "1"
    r = run(WRITERS["shadow_event"])
    checks.append({"check": "production_allowed_env::shadow_event", "pass": r == "ok", "got": r})

    # 收尾：清环境，避免影响后续（本进程独立，安全）
    os.environ.pop("SA_REGISTRY_PRODUCTION", None)

    n, passed = len(checks), sum(1 for c in checks if c["pass"])
    out = {"note": "P5a.82 §四 DC-9 写路径守卫电池（隔离临时注册表；零 token）",
           "n": n, "passed": passed, "all_pass": passed == n, "results": checks}
    json.dump(out, open(os.path.join(R, "provenance-guard-battery.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
