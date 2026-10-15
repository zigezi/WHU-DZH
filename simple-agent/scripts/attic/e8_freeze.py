#!/usr/bin/env python3
"""P5a.30/31/33 工单 D/E：e8 矩阵冻结 + 两臂形态平衡 + 达标线（零 token）。

- 臂分配：任务级纯随机 1/3（blake2b(seed|req_id) % 3），不受任何配额影响；
- 臂内选择：C.select_for_arm（同域同族→近族→ineligible；unrelated 形态匹配）；k=3 臂内；
- 达标线：top-1 覆盖率 ≤15% ∧ distinct ≥20 ∧ 同域覆盖率 ≥60%；
- 形态平衡表：sibling vs unrelated 计划长度/首工具类型。

运行（需 tau venv 取 GT 参考长度）：
  PYTHONPATH=.agent/vendor/tau-bench .agent/venv/tau/bin/python scripts/e8_freeze.py --epoch 7 --seed e8-20260929
"""
import argparse
import dataclasses
import hashlib
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
from monitor import precedent_select as ps  # noqa: E402

R = os.path.join(ROOT, ".agent", "reports")
REQ = os.path.join(BACKEND, "requirements", "tau")
ARMS = ["direct", "sibling", "unrelated"]
MUT = {"cancel_reservation", "book_reservation", "update_reservation_flights",
       "update_reservation_baggages", "send_certificate", "cancel_pending_order",
       "modify_pending_order_address", "modify_pending_order_items",
       "modify_pending_order_payment", "exchange_delivered_order_items",
       "return_delivered_order_items"}


def domain_of(req_id):
    req_id = req_id or ""
    if req_id.startswith("TAU-A-"):
        return "airline"
    if req_id.startswith("TAU-R-"):
        return "retail"
    return None


def run_epoch_of(ts):
    for p, v in (("2026-09-11", 1), ("2026-09-14", 3), ("2026-09-15", 4),
                 ("2026-09-16", 5), ("2026-09-29", 6)):
        if ts and ts.startswith(p):
            return v
    return None


def load_run_meta(con):
    """P5a.40 §二/§三.3：源 run verdict + 工具调用数。"""
    verd, calls = {}, {}
    for t in con.execute("SELECT task_id,req_id,created_at FROM tasks WHERE req_id LIKE 'TAU-%'"):
        e = run_epoch_of(t["created_at"])
        if e is None:
            continue
        for s in con.execute("SELECT attributes FROM spans WHERE trace_id=? AND type='verdict'",
                             (t["task_id"],)):
            try:
                a = json.loads(s["attributes"]) if s["attributes"] else {}
            except Exception:
                a = {}
            verd[(t["req_id"], e)] = a.get("decision")
        calls[(t["req_id"], e)] = con.execute(
            "SELECT count(*) FROM spans WHERE trace_id=? AND type='tool_call'",
            (t["task_id"],)).fetchone()[0]
    return verd, calls


def gt_ref(env, tid):
    if env == "airline":
        from tau_bench.envs.airline.tasks_test import TASKS
    else:
        from tau_bench.envs.retail.tasks_test import TASKS_TEST as TASKS
    t = TASKS[tid]
    d = dataclasses.asdict(t) if dataclasses.is_dataclass(t) else t.__dict__
    acts = d.get("actions", [])
    names = [a.get("name") if isinstance(a, dict) else getattr(a, "name", None) for a in acts]
    return len(acts), names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epoch", type=int, default=7)
    ap.add_argument("--seed", default="e8-20260929")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--near", type=float, default=0.6)
    args = ap.parse_args()

    deid = json.load(open(os.path.join(R, "e8-deid-snapshot.json")))
    import sqlite3
    con = sqlite3.connect(os.path.join(BACKEND, "logs", "trace.db"))
    con.row_factory = sqlite3.Row
    verd, calls = load_run_meta(con)
    cands = []
    rejected_fail, extract_defects = 0, []
    for r in con.execute("SELECT req_id,sig,plan_json,created_at FROM precedent_snapshots WHERE epoch=?",
                         (args.epoch,)):
        dom = domain_of(r["req_id"])
        if not dom:
            continue
        # D3：池合格性 = 源 run verdict=PASS
        e = run_epoch_of(r["created_at"])
        if verd.get((r["req_id"], e)) != "PASS":
            rejected_fail += 1
            continue
        try:
            plan = json.loads(r["plan_json"]) if r["plan_json"] else []
        except Exception:
            plan = []
        oh = ps.content_hash(plan)
        if oh not in deid:
            continue
        # 提取保真：计划工具数 vs 源 run tool_call 数
        n_calls = calls.get((r["req_id"], e))
        if n_calls is not None and n_calls != len(plan):
            extract_defects.append({"req_id": r["req_id"], "epoch": e,
                                    "plan_tools": len(plan), "run_tool_calls": n_calls})
        cands.append({"req_id": r["req_id"], "sig": r["sig"], "domain": dom, "plan": plan,
                      "hash": deid[oh]["deid_hash"], "orig_hash": oh})
    # dedup candidates by hash (keep first req)
    seen, uniq = set(), []
    for c in cands:
        if c["hash"] in seen:
            continue
        seen.add(c["hash"]); uniq.append(c)
    cands = uniq
    fam_types = {}
    for c in cands:
        fam_types.setdefault((c["domain"], c["sig"]), [])
        fam_types[(c["domain"], c["sig"])] += ps.plan_types(c["plan"])

    # tasks
    tasks = []
    for fn in sorted(os.listdir(REQ)):
        if not fn.endswith(".json"):
            continue
        spec = json.load(open(os.path.join(REQ, fn)))
        if spec.get("split") != "train" or not spec.get("tau_env"):
            continue
        tasks.append(spec)
    tasks.sort(key=lambda s: s["req_id"])

    from collections import Counter, defaultdict

    def lenbin(n):
        return "b0(1-3)" if n <= 3 else "b1(4-6)" if n <= 6 else "b2(7-10)" if n <= 10 else "b3(11+)"

    def endcls(plan):
        t = [s.get("tool", "").replace("tau__", "") for s in (plan or [])]
        if not t:
            return "empty"
        last = t[-1]
        if last == "transfer_to_human_agents":
            return "transfer_end"
        return "state_change_end" if last in MUT else "query_end"

    def cell(c):
        return (lenbin(len(c["plan"])), endcls(c["plan"])) if c else (None, None)

    used = {a: {} for a in ARMS}
    rows = []
    for t in tasks:
        rid, sig, env = t["req_id"], t["sig"], t["tau_env"]
        h = hashlib.blake2b(f"{args.seed}|{rid}".encode(), digest_size=4).digest()
        arm = ARMS[int.from_bytes(h, "big") % 3]
        refl, reft = gt_ref(env, t["tau_task_id"])
        if arm == "unrelated":
            chosen, reason = None, "r1_pending"           # R1 稍后分层匹配
        else:
            chosen, reason = ps.select_for_arm(
                cands, rid, sig, env, arm,
                random.Random(hashlib.sha256((args.seed + rid).encode()).hexdigest()),
                used[arm], k=args.k, fam_types=fam_types, near=args.near,
                ref_len=refl, ref_types=reft)
        if chosen:
            used[arm][chosen["hash"]] = used[arm].get(chosen["hash"], 0) + 1
        rows.append({"req_id": rid, "tau_env": env, "sig": sig, "arm": arm,
                     "reason": reason,
                     "injectant": chosen["req_id"] if chosen else None,
                     "injectant_env": chosen["domain"] if chosen else None,
                     "deid_hash": chosen["hash"] if chosen else None,
                     "len": len(chosen["plan"]) if chosen else 0,
                     "cell": list(cell(chosen)) if chosen else None,
                     "first_tool": (ps.plan_types(chosen["plan"]) or [None])[0] if chosen else None})

    # R1：仅重抽 unrelated 臂注入物，对齐 sibling 实测分布（长度分箱 + 结尾动作三类），一发成稿
    sib_cells = Counter(tuple(r["cell"]) for r in rows if r["arm"] == "sibling" and r["deid_hash"])
    n_sib = sum(sib_cells.values())
    un_tasks = [r for r in rows if r["arm"] == "unrelated"]
    n_un = len(un_tasks)
    sib_used = {r["deid_hash"] for r in rows if r["arm"] == "sibling" and r["deid_hash"]}
    pool = [c for c in cands if c["hash"] not in sib_used]
    pool_by_cell = defaultdict(list)
    for c in pool:
        pool_by_cell[cell(c)].append(c)
    for v in pool_by_cell.values():
        v.sort(key=lambda c: c["orig_hash"])
    # 目标配额（largest remainder）
    props = {k: v / n_sib for k, v in sib_cells.items()} if n_sib else {}
    raw = {k: props[k] * n_un for k in props}
    quota = {k: int(raw[k]) for k in props}
    remc = n_un - sum(quota.values())
    for k in sorted(props, key=lambda c: -(raw[c] - int(raw[c])))[:remc]:
        quota[k] += 1
    assigned, used_un, changes = Counter(), {}, []
    def avail(c):
        return used_un.get(c["hash"], 0) < args.k
    for r in un_tasks:
        # 选当前最欠配额的 cell（确定：差值大者优先，平局按 cell 名）
        best, bestdef = None, None
        for k in sorted(set(list(quota) + list(pool_by_cell))):
            d = quota.get(k, 0) - assigned[k]
            if bestdef is None or d > bestdef:
                bestdef, best = d, k
        cand = next((c for c in pool_by_cell.get(best, []) if avail(c)), None)
        if cand is None:
            cand = next((c for c in pool for c in [c] if avail(c)), None)
        if cand:
            used_un[cand["hash"]] = used_un.get(cand["hash"], 0) + 1
            assigned[best] += 1
            r["injectant"] = cand["req_id"]; r["injectant_env"] = cand["domain"]
            r["deid_hash"] = cand["hash"]; r["len"] = len(cand["plan"])
            r["cell"] = list(cell(cand)); r["reason"] = "r1_stratified"
            r["first_tool"] = (ps.plan_types(cand["plan"]) or [None])[0]
            changes.append(r["req_id"])

    # gates
    inj = [r for r in rows if r["deid_hash"]]
    cov = Counter(r["deid_hash"] for r in inj)
    top1 = max(cov.values()) / len(inj) if inj else 0
    distinct = len(cov)
    sib = [r for r in rows if r["arm"] == "sibling"]
    sib_cov = [r for r in sib if r["injectant_env"] == r["tau_env"]]
    same_cov = len(sib_cov) / len(sib) if sib else 0

    def hist(rs):
        b = Counter(r["cell"][0] for r in rs if r["cell"])
        e = Counter(r["cell"][1] for r in rs if r["cell"])
        ln = [r["len"] for r in rs if r["deid_hash"]]
        return {"n": len(ln), "mean": round(sum(ln) / len(ln), 1) if ln else 0,
                "len_bins": dict(b), "end_class": dict(e),
                "len_bin_pct": {k: round(v / max(len(ln), 1) * 100, 1) for k, v in b.items()},
                "end_class_pct": {k: round(v / max(len(ln), 1) * 100, 1) for k, v in e.items()}}
    balance = {"sibling": hist([r for r in rows if r["arm"] == "sibling"]),
               "unrelated": hist([r for r in rows if r["arm"] == "unrelated"])}
    # R1 达标：逐箱/逐类差 ≤10pp，均值差 ≤1.0
    sb, ub = balance["sibling"], balance["unrelated"]
    bin_gap = max(abs(sb["len_bin_pct"].get(k, 0) - ub["len_bin_pct"].get(k, 0))
                  for k in set(sb["len_bin_pct"]) | set(ub["len_bin_pct"]))
    end_gap = max(abs(sb["end_class_pct"].get(k, 0) - ub["end_class_pct"].get(k, 0))
                  for k in set(sb["end_class_pct"]) | set(ub["end_class_pct"]))
    r1 = {"bin_gap_pp": round(bin_gap, 1), "end_gap_pp": round(end_gap, 1),
          "mean_gap": round(abs(sb["mean"] - ub["mean"]), 1),
          "pass": bin_gap <= 10 and end_gap <= 10 and abs(sb["mean"] - ub["mean"]) <= 1.0}
    gates = {"top1_coverage": round(top1, 3), "top1_pass": top1 <= 0.15,
             "distinct": distinct, "distinct_pass": distinct >= 20,
             "same_domain_coverage": round(same_cov, 3), "same_domain_pass": same_cov >= 0.60,
             "r1": r1,
             "arms": {a: sum(1 for r in rows if r["arm"] == a) for a in ARMS}}
    gates["all_pass"] = (gates["top1_pass"] and gates["distinct_pass"]
                         and gates["same_domain_pass"] and r1["pass"])

    matrix_hash = hashlib.sha256(
        json.dumps([(r["req_id"], r["arm"], r["deid_hash"]) for r in rows],
                   ensure_ascii=False).encode()).hexdigest()[:16]
    # R2 分母台账
    ledger = {
        "snapshot_epoch7_rows": con.execute(
            "SELECT count(*) FROM precedent_snapshots WHERE epoch=?", (args.epoch,)).fetchone()[0],
        "tau_tool_candidates": len(uniq) + rejected_fail,
        "rejected_nonpass_rows": rejected_fail,      # 源 run verdict != PASS
        "eligible_candidates": len(uniq),
        "distinct_injectants_used": distinct,
        "matrix_rows": len(rows),
        "arms": {a: sum(1 for r in rows if r["arm"] == a) for a in ARMS},
        "ineligible": sum(1 for r in rows if r["arm"] in ("sibling", "unrelated")
                          and not r["deid_hash"]),
        "ineligible_by_arm": {a: sum(1 for r in rows if r["arm"] == a and not r["deid_hash"])
                              for a in ("sibling", "unrelated")},
        "note": "ITT：ineligible 任务按所分臂进入分析（assigned=analyzed），剔除会致脱落偏倚",
    }
    out = {"note": "e8 矩阵冻结（a30/a31/a33/a40/a42）；R1 形态再匹配 + 台账",
           "seed": args.seed, "k": args.k, "near_jaccard": args.near,
           "matrix_hash": matrix_hash,
           "pool_rejected_nonpass": rejected_fail,
           "extraction_defects": extract_defects[:20],
           "extraction_defect_n": len(extract_defects),
           "r1_changed_tasks": len(changes),
           "r1_change_list": changes,
           "gates": gates, "form_balance": balance, "ledger": ledger, "matrix": rows}
    json.dump(out, open(os.path.join(R, "e8-matrix-freeze.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps({"gates": gates, "form_balance": balance, "ledger": ledger},
                     ensure_ascii=False, indent=1))
    print("-> .agent/reports/e8-matrix-freeze.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
