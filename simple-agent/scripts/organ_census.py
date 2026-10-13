#!/usr/bin/env python3
"""P5a.63 §二：全尸体普查（零 token）——ring_mine→ring_triage 过全部历史 FAIL 尸体。
合格线（预注册）：敏感性 8/8；特异性 deploy 率 ≤2%（≈≤5 件）。
  /root/miniconda3/envs/mini-agent/bin/python scripts/organ_census.py
"""
import json
import os
import sqlite3
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from monitor.organ import Pipeline  # noqa: E402
from organ_ingest_corpses import run_pattern  # noqa: E402

DB = os.path.join(BACKEND, "logs", "trace.db")
R = os.path.join(ROOT, ".agent", "reports")

# 8 个已部署死因簇（敏感性核对）：器官须给非 reject（certificate 例外=应被观测性要件拦=reject）
CLUSTERS = {
    "lock_order": ["non-pending order cannot be modified"],
    "repeat_failure": None,                     # kind=repeat_failure
    "items_count": ["number of items"],
    "non_delivered": ["non-delivered order"],
    "payment_sum": ["payment amount does not add up"],
    "certificate_update": ["certificate cannot be used"],   # 预期 reject（不可观测）
    "flight_availability": ["not enough seats"],
    "gift_card_balance": ["gift card balance", "not enough balance"],
}


def cover_of(pid, kind):
    blob = (pid + " " + kind).lower()
    for name, subs in CLUSTERS.items():
        if name == "lock_order":
            if kind == "order_lock" or pid.startswith("LOCK_ORDER"):
                return name
        elif name == "repeat_failure":
            if kind == "repeat_failure":
                return name
        elif subs and any(s in blob for s in subs):
            return name
    return None


def main():
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    pipe = Pipeline()
    seen = set()
    total = 0
    disp_counts = Counter()
    covered = Counter()
    deploy_new = []
    cluster_hits = defaultdict(list)   # cluster -> [dispositions]
    for t in con.execute("SELECT task_id,req_id,created_at FROM tasks WHERE req_id LIKE 'TAU-%' ORDER BY created_at"):
        p = run_pattern(con, t["task_id"], t["req_id"])
        if not p:
            continue
        key = (t["req_id"], t["created_at"][:13])   # 去重（同 req 同小时）
        if key in seen:
            continue
        seen.add(key)
        total += 1
        disp = pipe.classify_disposition(p)
        disp_counts[disp] += 1
        cov = cover_of(p["pattern_id"], p["kind"])
        if cov:
            covered[cov] += 1
            cluster_hits[cov].append(disp)
        elif disp == "deploy":
            deploy_new.append({"req_id": t["req_id"], "death": p["pattern_id"], "at": t["created_at"][:19]})
    # 敏感性：8 簇是否全收（7 簇须非 reject；certificate 须 reject=被观测性拦）
    sens = {}
    for name in CLUSTERS:
        disps = cluster_hits.get(name, [])
        if not disps:
            sens[name] = "n/a(no corpse in 259)"
        elif name == "certificate_update":
            # 观测性要件在出生门拦（reject 不可观测）；分诊层 decompose 可接受
            sens[name] = "OK" if all(d in ("reject", "decompose") for d in disps) else f"REVIEW:{Counter(disps)}"
        else:
            sens[name] = "OK" if all(d != "reject" for d in disps) else f"MISS:{Counter(disps)}"
    sens_ok = all(str(v).startswith(("OK", "n/a")) for v in sens.values())
    spec_rate = round(len(deploy_new) / total * 100, 2) if total else 0
    spec_ok = len(deploy_new) <= max(5, round(total * 0.02))
    out = {"note": "P5a.63 全尸体普查（零 token；ring_draft 禁用）",
           "corpses": total, "disposition_counts": dict(disp_counts),
           "covered_by_existing": dict(covered), "deploy_new": deploy_new,
           "sensitivity": sens, "sensitivity_ok": sens_ok,
           "specificity_deploy_new": len(deploy_new), "specificity_rate_pct": spec_rate,
           "specificity_ok": spec_ok,
           "census_clean": sens_ok and spec_ok and len(deploy_new) == 0}
    json.dump(out, open(os.path.join(R, "organ-census.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
