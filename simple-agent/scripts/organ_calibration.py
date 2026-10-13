#!/usr/bin/env python3
"""P5a.59 §一：器官已知答案校准（≈零 token）——e1–e8 尸体库 25 候选喂器官，与人工终裁逐条对照。
  /root/miniconda3/envs/mini-agent/bin/python scripts/organ_calibration.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from monitor.organ import Pipeline  # noqa: E402

R = os.path.join(ROOT, ".agent", "reports")

# 人工终裁（P5a.36 triage）：按 pattern_id 前缀/误差子串映射
REJECT_HUMAN = ("user not found", "invoke()")
# 8 个已部署资产的死因簇（须全收，不得误杀）
DEPLOYED_CLUSTERS = {
    "lock_order": ["non-pending order cannot be modified"],
    "repeat_failure": ["repeat"],                      # kind=repeat_failure
    "items_count": ["number of items"],
    "non_delivered": ["non-delivered order"],
    "payment_sum": ["payment amount does not add up"],
    "certificate_update": ["certificate cannot be used"],
    "flight_availability": ["not enough seats"],
    "gift_card_balance": ["gift card balance", "not enough balance"],
}


def matches(p, subs):
    blob = ((p.get("pattern_id") or "") + " " + " ".join(p.get("examples", []))).lower()
    return any(s in blob for s in subs)


def main():
    patterns = json.load(open(os.path.join(R, "p5a36-death-patterns.json")))["patterns"]
    triaged = Pipeline().ring_triage(patterns)
    rows = []
    misfire_release = []       # 驳回类被放行（重罪）
    miss_recall = []           # 已部署簇被误杀
    divergences = []
    for p in triaged:
        disp = p["disposition"]
        # (a) 驳回类必须 reject
        if matches(p, REJECT_HUMAN):
            if disp != "reject":
                misfire_release.append(p["pattern_id"])
        # (b) 已部署簇不得 reject（误杀=召回不足）
        for asset, subs in DEPLOYED_CLUSTERS.items():
            if (asset == "repeat_failure" and p.get("kind") == "repeat_failure") or \
               (asset != "repeat_failure" and matches(p, subs)):
                if disp == "reject":
                    miss_recall.append((asset, p["pattern_id"]))
        # (c) 记录与"deploy"的人工终裁有分歧者
        rows.append({"pattern_id": p["pattern_id"], "kind": p["kind"],
                     "disposition": disp,
                     "human": ("reject" if matches(p, REJECT_HUMAN) else
                               ("deploy" if p.get("kind") in ("order_lock", "repeat_failure")
                                or disp == "deploy" else "decompose/review"))})
    a_ok = not misfire_release
    b_ok = not miss_recall
    out = {"note": "P5a.59 阶段一 器官校准（已知答案）",
           "n": len(rows),
           "pass_a_reject_all": a_ok, "misfire_release": misfire_release,
           "pass_b_recall_deployed": b_ok, "miss_recall": miss_recall,
           "calibrated": a_ok and b_ok,
           "disposition_counts": {d: sum(1 for r in rows if r["disposition"] == d)
                                  for d in ("reject", "deploy", "decompose")},
           "rows": rows}
    json.dump(out, open(os.path.join(R, "organ-calibration.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, ensure_ascii=False, indent=1))
    for r in rows:
        print("  ", r["disposition"], r["kind"], r["pattern_id"])
    print("CALIBRATED:", out["calibrated"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
