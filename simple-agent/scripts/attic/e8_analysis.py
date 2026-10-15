#!/usr/bin/env python3
"""P5a.43 e8 判读：Δ2 主终点（family 簇 wild bootstrap）+ 臂间 Δ1/Δ3 + 骨架分解。

  /root/miniconda3/envs/mini-agent/bin/python scripts/e8_analysis.py
"""
import json
import os
import random
import sqlite3
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
R = os.path.join(ROOT, ".agent", "reports")
DB = os.path.join(BACKEND, "logs", "trace.db")
MUT = {"cancel_reservation", "book_reservation", "update_reservation_flights",
       "update_reservation_baggages", "send_certificate", "cancel_pending_order",
       "modify_pending_order_address", "modify_pending_order_items",
       "modify_pending_order_payment", "exchange_delivered_order_items",
       "return_delivered_order_items"}


def endcls(plan):
    t = [s.get("tool", "").replace("tau__", "") for s in (plan or [])]
    if not t:
        return "empty"
    last = t[-1]
    if last == "transfer_to_human_agents":
        return "transfer_end"
    return "state_change_end" if last in MUT else "query_end"


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    matrix = {r["req_id"]: r for r in json.load(open(os.path.join(R, "e8-matrix-freeze.json")))["matrix"]}
    raw = json.load(open(os.path.join(R, "e8-deid-snapshot.json")))
    deid = {v["deid_hash"]: v["deid_plan"] for v in raw.values()}
    sig = {}
    for fn in os.listdir(os.path.join(BACKEND, "requirements", "tau")):
        if fn.endswith(".json"):
            s = json.load(open(os.path.join(BACKEND, "requirements", "tau", fn)))
            sig[s["req_id"]] = s["sig"]

    W = "req_id LIKE 'TAU-%' AND created_at>='2026-10-10'"
    rows = []
    for t in con.execute(f"SELECT task_id,req_id FROM tasks WHERE {W}"):
        arm = None
        deid_hash = None
        verdict = None
        for s in con.execute("SELECT type,attributes FROM spans WHERE trace_id=?", (t["task_id"],)):
            a = json.loads(s["attributes"]) if s["attributes"] else {}
            if s["type"] == "arm_choice":
                arm = a.get("arm")
            elif s["type"] == "precedent_injected":
                deid_hash = a.get("content_sha256_16")
            elif s["type"] == "verdict":
                verdict = a.get("decision")
        if arm is None:
            continue
        inj = matrix.get(t["req_id"], {}).get("injectant")
        rows.append({"task": t["req_id"], "arm": arm, "verdict": verdict,
                     "pass": 1 if verdict == "PASS" else 0,
                     "ending": endcls(deid.get(deid_hash)) if deid_hash in deid else None,
                     "sig": sig.get(t["req_id"])})

    def rate(arms):
        sel = [r for r in rows if r["arm"] in arms]
        return (sum(r["pass"] for r in sel) / len(sel) * 100 if sel else 0), len(sel)

    d_rate, d_n = rate({"direct"})
    s_rate, s_n = rate({"sibling"})
    u_rate, u_n = rate({"unrelated"})
    d2 = s_rate - u_rate
    d1 = s_rate - d_rate
    d3 = u_rate - d_rate

    # family cluster wild bootstrap for Δ1/Δ2/Δ3
    fams = {}
    for r in rows:
        fams.setdefault(r["sig"], []).append(r)
    fam_list = list(fams)
    random.seed(20261010)

    def boot(pairs_index):
        s_arm, u_arm = pairs_index
        boots = []
        for _ in range(5000):
            sample = []
            for _f in fam_list:
                sample += fams[random.choice(fam_list)]
            a = [r["pass"] for r in sample if r["arm"] == s_arm]
            b = [r["pass"] for r in sample if r["arm"] == u_arm]
            if a and b:
                boots.append(sum(a) / len(a) * 100 - sum(b) / len(b) * 100)
        boots.sort()
        ci = (boots[int(0.025 * len(boots))], boots[int(0.975 * len(boots))]) if boots else (None, None)
        p_le0 = sum(1 for x in boots if x <= 0) / len(boots) if boots else None
        return [round(ci[0], 1), round(ci[1], 1)], round(p_le0, 4)

    ci, p_le0 = boot(("sibling", "unrelated"))
    ci1, p1 = boot(("sibling", "direct"))
    ci3, p3 = boot(("unrelated", "direct"))

    # skeleton decomposition: Δ2 within each injectant ending class
    decomp = {}
    for cls in ("state_change_end", "transfer_end", "query_end"):
        s = [r["pass"] for r in rows if r["arm"] == "sibling" and r["ending"] == cls]
        u = [r["pass"] for r in rows if r["arm"] == "unrelated" and r["ending"] == cls]
        decomp[cls] = {"sibling": f"{sum(s)}/{len(s)}", "unrelated": f"{sum(u)}/{len(u)}",
                       "delta_pp": round((sum(s) / len(s) - sum(u) / len(u)) * 100, 1) if s and u else None}

    out = {
        "note": "P5a.43 e8 判读；不做跨 epoch 对比",
        "n": len(rows),
        "arms": {"direct": {"pass": f"{int(d_rate*d_n/100)}/{d_n}", "rate": round(d_rate, 1)},
                 "sibling": {"pass": f"{int(round(s_rate*s_n/100))}/{s_n}", "rate": round(s_rate, 1)},
                 "unrelated": {"pass": f"{int(round(u_rate*u_n/100))}/{u_n}", "rate": round(u_rate, 1)}},
        "delta2_sibling_minus_unrelated_pp": round(d2, 1),
        "delta2_cluster_bootstrap_95CI": [round(ci[0], 1), round(ci[1], 1)],
        "delta2_p_le0": round(p_le0, 4),
        "delta2_win": (ci[0] is not None and ci[0] > 0),
        "delta1_sibling_minus_direct_pp": round(d1, 1),
        "delta1_cluster_bootstrap_95CI": ci1, "delta1_p_le0": p1,
        "delta3_unrelated_minus_direct_pp": round(d3, 1),
        "delta3_cluster_bootstrap_95CI": ci3, "delta3_p_le0": p3,
        "placebo_band_ref_pp": [2.6, 11.5],
        "skeleton_decomposition": decomp,
        "families": len(fam_list),
        "itt_note": "136 行按所分臂全量分析（ineligible 2 例 sibling 留在分母）",
    }
    json.dump(out, open(os.path.join(R, "e8-analysis.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
