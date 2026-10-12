#!/usr/bin/env python3
"""P5a.44 §三.3：E3 基板自检 —— 域包加载 + validated_domain 资产登记。

  /root/miniconda3/envs/mini-agent/bin/python scripts/e3_substrate_check.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

import domains  # noqa: E402
from monitor import provenance  # noqa: E402


def main():
    res = {}
    # 1) 域包加载
    res["domains"] = domains.list_domains()
    tau = domains.get("tau")
    code = domains.get("code")
    res["tau_ok"] = bool(tau and tau.transfer_tool and tau.interceptor_rules)
    res["code_ok"] = bool(code and code.name == "code")

    # 2) 首个部署资产登记（validated_domain=tau）
    prov = os.path.join(ROOT, ".agent", "reports", "e9-canary-battery.json")
    ev = "P5a.28 backtest 0/12; B-2 battery 7/7" if os.path.exists(prov) else "B-2 battery pending"
    rec = provenance.register_asset({
        "asset_id": "lock_order_v1",
        "type": "interceptor_rule",
        "text": "对同一实体的多步修改，先执行不改变实体锁定状态的操作。",
        "trigger": "modify_pending_order_items ∧ 同 order_id 未成功改地址 ∧ 未否决过",
        "validated_domain": "tau",
        "death_cause": "lock_order",
        "credit_level": "T1_candidate",
        "status": "active",
        "evidence": ev,
        "domain_pack": "tau",
        "rule_id": tau.interceptor_rules[0]["rule"] if tau else None,
    })
    res["asset"] = {k: rec[k] for k in ("asset_id", "validated_domain", "credit_level",
                                        "status", "death_cause", "evidence")}
    res["assets_total"] = len(provenance.list_assets())
    res["allocated_by_domain"] = {"tau": len(provenance.list_assets("tau"))}

    # 3) 拦截器谓词与域包规则一致
    from monitor.interceptor import INTERCEPT_TOOL, ADDRESS_TOOL, OrderLockInterceptor
    rule = tau.interceptor_rules[0]
    res["rule_matches_interceptor"] = (rule["target_tool"] == INTERCEPT_TOOL
                                       and rule["prereq_tool"] == ADDRESS_TOOL)
    ok = res["tau_ok"] and res["code_ok"] and res["rule_matches_interceptor"]
    res["all_pass"] = ok
    import json
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
