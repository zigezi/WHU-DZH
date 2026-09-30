#!/usr/bin/env python3
"""P5a.33 §一 工单 A：构建伪真值脱敏库 + lint 三检 + 达标线初判（零 token）。

运行（需 tau venv 读 DB dump 做非成员断言）：
  PYTHONPATH=.agent/vendor/tau-bench .agent/venv/tau/bin/python scripts/e8_build_deident.py --epoch 7

产物：
  .agent/reports/e8-deid-snapshot.json  脱敏库（tracked；已脱敏，安全）
  .agent/reports/e8-deid-lint.json      lint 三检 + seed + mapping_sha256（tracked）
  .agent/local/e8-deident-mapping.json  真实↔伪真值映射（**未跟踪，敏感**）
"""
import argparse
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
sys.path.insert(0, os.path.join(BACKEND, "requirements", "adapters", "tau"))

import sqlite3  # noqa: E402
from deident import DeIdentifier, lint_db_nonmember, lint_lint_parse_and_names, lint_no_residual  # noqa: E402

DB = os.path.join(BACKEND, "logs", "trace.db")
R = os.path.join(ROOT, ".agent", "reports")
LOCAL = os.path.join(ROOT, ".agent", "local")
SEED = "e8-20260929"


def chash(plan):
    return hashlib.sha256(
        json.dumps(plan, ensure_ascii=False, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]


def db_members():
    out = set()
    try:
        from tau_bench.envs.retail.data import load_data as retail
        _walk(retail(), out)
    except Exception as e:  # noqa: BLE001
        print("[warn] retail data:", e)
    try:
        from tau_bench.envs.airline.data import load_data as airline
        _walk(airline(), out)
    except Exception as e:  # noqa: BLE001
        print("[warn] airline data:", e)
    return out


def _walk(o, s):
    if isinstance(o, dict):
        for k, v in o.items():
            s.add(str(k)); _walk(v, s)
    elif isinstance(o, list):
        for v in o:
            _walk(v, s)
    else:
        s.add(str(o))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epoch", type=int, default=7)
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    # distinct plans in snapshot
    plans = {}
    for r in con.execute("SELECT plan_json FROM precedent_snapshots WHERE epoch=?", (args.epoch,)):
        try:
            p = json.loads(r["plan_json"]) if r["plan_json"] else []
        except Exception:
            p = []
        plans.setdefault(chash(p), p)

    members = db_members()
    deid_lib, lint_rows, mapping = {}, [], {}
    non_tau = 0
    for h, p in sorted(plans.items()):
        if not all(str(s.get("tool", "")).startswith("tau__") for s in p):
            non_tau += 1
            continue
        d = DeIdentifier(seed=SEED)
        dp = d.plan(p)
        for (t, real), fake in d.mapping.items():
            mapping.setdefault(t, {})[real] = fake
        l1 = lint_no_residual(p, dp)
        l2 = lint_lint_parse_and_names(dp)
        l3 = lint_db_nonmember(dp, members)
        lint_rows.append({"orig_hash": h, "deid_hash": chash(dp),
                          "tools": len(dp), "no_residual": l1["ok"],
                          "json_ok": l2["json_ok"], "bad_tools": l2["bad_tools"],
                          "db_nonmember": l3["ok"]})
        deid_lib[h] = {"deid_hash": chash(dp), "deid_plan": dp}

    os.makedirs(LOCAL, exist_ok=True)
    mtxt = json.dumps(mapping, ensure_ascii=False, sort_keys=True)
    open(os.path.join(LOCAL, "e8-deident-mapping.json"), "w").write(mtxt)
    json.dump(deid_lib, open(os.path.join(R, "e8-deid-snapshot.json"), "w"),
              ensure_ascii=False, indent=1)
    lint = {
        "note": "P5a.33 §一 lint 三检；映射表存 .agent/local/（未跟踪）",
        "seed": SEED,
        "mapping_sha256": hashlib.sha256(mtxt.encode()).hexdigest(),
        "distinct_orig_plans": len(plans),
        "non_tau_plans_skipped": non_tau,
        "distinct_deid_plans": len({v["deid_hash"] for v in deid_lib.values()}),
        "all_pass": all(r["no_residual"] and r["json_ok"] and r["db_nonmember"] and not r["bad_tools"]
                        for r in lint_rows),
        "rows": lint_rows,
    }
    json.dump(lint, open(os.path.join(R, "e8-deid-lint.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in lint.items() if k != "rows"}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
