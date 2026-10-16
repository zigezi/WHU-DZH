#!/usr/bin/env python3
"""P5a.58 生成器官自检（零 token）：宪法墙 + 出生门 + 影子毕业/回炉。"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from monitor import provenance as prov  # noqa: E402
from monitor import organ  # noqa: E402

# 隔离存储：把 provenance 指向临时文件（不污染真实资产库）
prov.FILE = os.path.join(tempfile.mkdtemp(prefix="organ-test-"), "assets.json")

CHECKS = []


def chk(name, cond):
    CHECKS.append({"check": name, "pass": bool(cond)})


def main():
    # 1) 宪法墙
    for bad in ("backend/requirements/adapters/tau/scoring.py", "scripts/e9_canary_battery.py",
                "scripts/e3_executor.py"):
        try:
            organ.assert_in_scope(bad); chk(f"constitution_deny::{bad}", False)
        except PermissionError:
            chk(f"constitution_deny::{bad}", True)
    try:
        organ.assert_in_scope("backend/monitor/organ.py"); chk("constitution_allow::organ", True)
    except PermissionError:
        chk("constitution_allow::organ", False)

    # 2) 出生门：缺可观测性证明 → 拒
    ok1, errs = organ.can_birth({"asset_id": "x", "type": "interceptor_rule",
                                 "validated_domain": "tau", "trigger": "t", "evidence": "e"})
    chk("birth_gate_reject_no_observability", (not ok1) and any("observability_proof" in e for e in errs))

    # 3) 出生门：齐备 → 出生为 shadow
    cand = {"asset_id": "proto_v1", "type": "interceptor_rule", "validated_domain": "tau",
            "trigger": "tool X without obs Y", "observability_proof": "点火=观测缺失(可观测)",
            "evidence": "selftest", "text": "x"}
    rec = organ.birth(cand)
    chk("birth_status_shadow", rec["status"] == "shadow" and rec["credit_level"] == "T1_candidate")

    # 4) 影子毕业：≥10 FAIL 点火 ∧ 0 误伤 → active
    for _ in range(10):
        organ.shadow_fire("proto_v1", "FAIL")
    a = next(x for x in prov.list_assets() if x["asset_id"] == "proto_v1")
    chk("shadow_graduate_at_10_0", a["status"] == "active" and a["shadow_firings"] == 10)

    # 5) 影子回炉：另建一个，1 次误伤 → pending_revalidation
    organ.birth({**cand, "asset_id": "proto_bad_v1"})
    organ.shadow_fire("proto_bad_v1", "FAIL")
    organ.shadow_fire("proto_bad_v1", "PASS")
    b = next(x for x in prov.list_assets() if x["asset_id"] == "proto_bad_v1")
    chk("shadow_demote_on_misfire", b["status"] == "pending_revalidation" and b["shadow_misfires"] == 1)

    n = len(CHECKS); passed = sum(1 for c in CHECKS if c["pass"])
    out = {"note": "P5a.58 器官自检（零 token）", "n": n, "passed": passed,
           "all_pass": passed == n, "results": CHECKS}
    import json
    json.dump(out, open(os.path.join(ROOT, ".agent", "reports", "organ-selftest.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
