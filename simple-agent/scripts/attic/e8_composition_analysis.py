#!/usr/bin/env python3
"""P5a.41 §二 工单：任务集组成 + 注入池组成分析（零 token，E 门审查附件）。

  PYTHONPATH=.agent/vendor/tau-bench .agent/venv/tau/bin/python scripts/e8_composition_analysis.py --epoch 7

输出 .agent/reports/e8-composition.json / .md
"""
import argparse
import dataclasses
import hashlib
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
R = os.path.join(ROOT, ".agent", "reports")

MUT = {
    "cancel_reservation", "book_reservation", "update_reservation_flights",
    "update_reservation_baggages", "update_reservation_passengers",
    "send_certificate", "cancel_pending_order", "modify_pending_order_address",
    "modify_pending_order_items", "modify_pending_order_payment",
    "exchange_delivered_order_items", "return_delivered_order_items",
    "update_order", "modify_user_address",
}
READP = ("get_", "search_", "list_", "find_", "calculate", "think")
TRANSFER = "transfer_to_human_agents"


def run_epoch_of(ts):
    for p, v in (("2026-09-11", 1), ("2026-09-14", 3), ("2026-09-15", 4),
                 ("2026-09-16", 5), ("2026-09-29", 6)):
        if ts and ts.startswith(p):
            return v
    return None


def chash(p):
    return hashlib.sha256(json.dumps(p, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()[:16]


def gt_actions(env, tid):
    if env == "airline":
        from tau_bench.envs.airline.tasks_test import TASKS
    else:
        from tau_bench.envs.retail.tasks_test import TASKS_TEST as TASKS
    t = TASKS[tid]
    d = dataclasses.asdict(t) if dataclasses.is_dataclass(t) else t.__dict__
    return [a.get("name") if isinstance(a, dict) else getattr(a, "name", None) for a in d.get("actions", [])]


def task_class(actions):
    acts = [a for a in actions if a and a != "respond"]
    if any(a in MUT for a in acts):
        return "state_change"
    if not acts:
        return "correct_refusal"
    return "read_only"


def ending_class(plan):
    tools = [s.get("tool", "").replace("tau__", "") for s in (plan or [])]
    if not tools:
        return "empty"
    last = tools[-1]
    if last == TRANSFER:
        return "transfer_end"
    if last in MUT:
        return "state_change_end"
    return "query_end"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epoch", type=int, default=7)
    args = ap.parse_args()
    con = sqlite3.connect(os.path.join(BACKEND, "logs", "trace.db"))
    con.row_factory = sqlite3.Row

    # ---- task-set composition ----
    from collections import Counter
    reqs = []
    for fn in os.listdir(os.path.join(BACKEND, "requirements", "tau")):
        if fn.endswith(".json"):
            s = json.load(open(os.path.join(BACKEND, "requirements", "tau", fn)))
            if s.get("split") == "train" and s.get("tau_env"):
                reqs.append(s)
    task = {"airline": Counter(), "retail": Counter()}
    for s in reqs:
        c = task_class(gt_actions(s["tau_env"], s["tau_task_id"]))
        task[s["tau_env"]][c] += 1
    task_total = Counter()
    for e in task:
        task_total += task[e]

    # ---- injection-pool composition ----
    verd = {}
    for t in con.execute("SELECT task_id,req_id,created_at FROM tasks WHERE req_id LIKE 'TAU-%'"):
        e = run_epoch_of(t["created_at"])
        if e is None:
            continue
        for s in con.execute("SELECT attributes FROM spans WHERE trace_id=? AND type='verdict'", (t["task_id"],)):
            try:
                a = json.loads(s["attributes"]) if s["attributes"] else {}
            except Exception:
                a = {}
            verd[(t["req_id"], e)] = a.get("decision")
    allc, passc = Counter(), Counter()
    seen = set()
    for r in con.execute("SELECT req_id,plan_json,created_at FROM precedent_snapshots WHERE epoch=?", (args.epoch,)):
        if not (r["req_id"] or "").startswith("TAU-"):
            continue
        try:
            plan = json.loads(r["plan_json"]) if r["plan_json"] else []
        except Exception:
            plan = []
        if not all(str(s.get("tool", "")).startswith("tau__") for s in plan):
            continue
        key = (r["req_id"], chash(plan))
        if key in seen:
            continue
        seen.add(key)
        ec = ending_class(plan)
        allc[ec] += 1
        if verd.get((r["req_id"], run_epoch_of(r["created_at"]))) == "PASS":
            passc[ec] += 1

    sc_pass = passc["state_change_end"]
    tot_pass = sum(passc.values())
    report = {
        "note": "P5a.41 §二 组成分析；E 门审查附件",
        "task_set": {"airline": dict(task["airline"]), "retail": dict(task["retail"]),
                     "total": dict(task_total), "n": len(reqs)},
        "pool_all": dict(allc), "pool_pass_only": dict(passc),
        "pool_pass_only_n": tot_pass,
        "state_change_share_pass_only": round(sc_pass / tot_pass * 100, 1) if tot_pass else 0,
        "stratification_required": (sc_pass / tot_pass < 0.5) if tot_pass else True,
    }
    json.dump(report, open(os.path.join(R, "e8-composition.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
