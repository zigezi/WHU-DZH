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
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
sys.path.insert(0, os.path.join(BACKEND, "requirements", "adapters", "tau"))

import sqlite3  # noqa: E402
from deident import (DeIdentifier, classify_lint, field_class, lint_db_dictionary,  # noqa: E402
                     lint_db_nonmember, lint_lint_parse_and_names, lint_no_residual,
                     lint_price_residual, membership_proof, prefix_for)

_ID_KEY = re.compile(r"^(#W\d{6,}|[A-Z0-9]{6}|[a-z]+_[a-z]+_\d{3,5}|"
                     r"(?:credit_card|gift_card|certificate|paypal)_\d+)$")

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


def build_enums():
    """P5a.35 IV 类封闭词表（机场码/舱位/枚举）。"""
    import dataclasses as dc
    E = {k: set() for k in ("origin", "destination", "cabin", "flight_type",
                            "insurance", "trip_type", "status", "source")}
    try:
        from tau_bench.envs.airline.tasks_test import TASKS as AT
        from tau_bench.envs.airline.data import load_data as adata
        for t in AT:
            d = dc.asdict(t) if dc.is_dataclass(t) else t.__dict__
            for a in d.get("actions", []):
                kw = a.get("kwargs", {}) if isinstance(a, dict) else getattr(a, "kwargs", {})
                for k in E:
                    if k in kw:
                        E[k].add(str(kw[k]))
        for f in adata().get("flights", []):
            E["origin"].add(f.get("origin")); E["destination"].add(f.get("destination"))
    except Exception as e:  # noqa: BLE001
        print("[warn] enums airline:", e)
    try:
        from tau_bench.envs.retail.data import load_data as rdata
        d = rdata()
        for o in d["orders"].values():
            E["status"].add(o.get("status"))
        for u in d["users"].values():
            for p in (u.get("payment_methods") or {}).values():
                E["source"].add(p.get("source"))
    except Exception as e:  # noqa: BLE001
        print("[warn] enums retail:", e)
    E["cabin"] |= {"economy", "business", "basic economy", "first", "premium economy"}
    E["flight_type"] |= {"round_trip", "one_way"}
    E["insurance"] |= {"yes", "no"}
    return {k: {v for v in vs if v} for k, vs in E.items()}


def collect_db_sets():
    """P5a.37/40：DB 全量实体字典（按类别前缀分组）——**定向采集**（商品名归 PROD，人名归 NAME）。"""
    sets = {}

    def add(pref, v):
        if v and isinstance(v, str) and len(v) >= 3:
            sets.setdefault(pref, set()).add(v)

    try:
        from tau_bench.envs.retail.data import load_data as rdata
        d = rdata()
        for uid, u in d["users"].items():
            add("USR", uid)
            nm = u.get("name") or {}
            add("NAME", nm.get("first_name")); add("NAME", nm.get("last_name"))
            add("EMAIL", nm.get("email") or u.get("email"))
            ad = u.get("address") or {}
            for k in ("address1", "address2"):
                add("ADDR", ad.get(k))
            add("ADDR", ad.get("city")); add("ADDR", ad.get("zip"))
            for pid in (u.get("payment_methods") or {}):
                add("PAY", pid)
        for oid, o in d["orders"].items():
            add("ORD", oid); add("USR", o.get("user_id"))
            for it in o.get("items", []):
                add("ITEM", it.get("item_id")); add("PROD", it.get("product_id"))
                if it.get("price") is not None:
                    add("PRICE", str(it.get("price")))
            for ph in o.get("payment_history", []):
                add("PAY", ph.get("payment_method_id"))
        for pid, p in d["products"].items():
            add("PROD", pid); add("PROD", p.get("name"))
            for v in (p.get("variants") or {}).values():
                if isinstance(v, dict) and v.get("price") is not None:
                    add("PRICE", str(v.get("price")))
    except Exception as e:  # noqa: BLE001
        print("[warn] retail db_sets:", e)

    try:
        from tau_bench.envs.airline.data import load_data as adata
        d = adata()
        for uid, u in (d.get("users") or {}).items():
            add("USR", uid)
            nm = u.get("name") or {}
            add("NAME", nm.get("first_name")); add("NAME", nm.get("last_name"))
            add("EMAIL", nm.get("email") or u.get("email"))
            ad = u.get("address") or {}
            for k in ("address1", "address2"):
                add("ADDR", ad.get(k))
            add("ADDR", ad.get("city")); add("ADDR", ad.get("zip"))
            for pid in (u.get("payment_methods") or {}):
                add("PAY", pid)
        for rid, r in (d.get("reservations") or {}).items():
            add("RES", rid); add("USR", r.get("user_id"))
            for f in r.get("flights", []):
                add("FLT", f.get("flight_number"))
            for pa in r.get("passengers", []):
                add("NAME", pa.get("first_name")); add("NAME", pa.get("last_name"))
        fl = d.get("flights")
        if isinstance(fl, dict):
            for fid, f in fl.items():
                add("FLT", (f or {}).get("flight_number") or fid)
        elif isinstance(fl, list):
            for f in fl:
                if isinstance(f, dict):
                    add("FLT", f.get("flight_number"))
    except Exception as e:  # noqa: BLE001
        print("[warn] airline db_sets:", e)
    return sets


def name_vocab():
    names = set()
    for mod, fn in (("retail", "rdata"), ("airline", "adata")):
        try:
            if mod == "retail":
                from tau_bench.envs.retail.data import load_data
            else:
                from tau_bench.envs.airline.data import load_data
            for u in load_data().get("users", {}).values():
                nm = u.get("name") or {}
                for k in ("first_name", "last_name"):
                    if nm.get(k):
                        names.add(str(nm[k]))
        except Exception as e:  # noqa: BLE001
            print(f"[warn] names {mod}:", e)
    return names


def _bykey(unclassified):
    from collections import Counter
    c = Counter()
    samples = {}
    for (k, v), n in unclassified.items():
        c[k] += n
        samples.setdefault(k, []).append(v)
    return {k: {"n": c[k], "samples": sorted(set(samples[k]))[:6]}
            for k, _ in c.most_common()}


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
    enums = build_enums()
    NAMES = name_vocab()
    DB_SETS = collect_db_sets()
    SCRUB_SETS = {k: v for k, v in DB_SETS.items() if k != "PRICE"}
    DB_VALUES = set().union(*SCRUB_SETS.values()) if SCRUB_SETS else set()  # 价格另判
    PRICES = DB_SETS.get("PRICE", set())
    PRICE_SCALED = {f"{round(float(p) * 1.37, 2):.2f}" for p in PRICES if p}
    print(f"[db-sets] scrub={ {k: len(v) for k, v in SCRUB_SETS.items()} } "
          f"machine4_total={len(DB_VALUES)}")
    deid_lib, lint_rows, mapping = {}, [], {}
    unclassified = {}
    non_tau = 0
    proof_n = cover_n = 0
    for h, p in sorted(plans.items()):
        if not all(str(s.get("tool", "")).startswith("tau__") for s in p):
            non_tau += 1
            continue
        d = DeIdentifier(seed=SEED, name_vocab=NAMES, db_sets=SCRUB_SETS)
        dp = d.plan(p)
        for (t, real), fake in d.mapping.items():
            mapping.setdefault(t, {})[real] = fake
        l1 = lint_no_residual(p, dp)
        l2 = lint_lint_parse_and_names(dp)
        l3 = lint_db_nonmember(dp, members)
        l4 = classify_lint(dp, enums)
        l5 = lint_db_dictionary(dp, DB_VALUES)
        l5p = lint_price_residual(dp, p)
        l5["ok"] = l5["ok"] and l5p["ok"]
        l5["price_residual"] = l5p["hits"]
        proof, not_in_dict = membership_proof(d.mapping, SCRUB_SETS)   # P5a.40 §三.1
        proof_n += len(proof); cover_n += len(not_in_dict)
        for k, v in l4["unclassified"]:
            unclassified.setdefault((k, v), 0)
            unclassified[(k, v)] += 1
        lint_rows.append({"orig_hash": h, "deid_hash": chash(dp),
                          "tools": len(dp), "no_residual": l1["ok"],
                          "json_ok": l2["json_ok"], "bad_tools": l2["bad_tools"],
                          "db_nonmember": l3["ok"], "iv_bare": len(l4["iv_bare"]),
                          "unclassified_n": l4["unclassified_n"],
                          "db_dict_hits": l5["n"], "db_dict_ok": l5["ok"],
                          "proof_fails": len(proof), "not_in_dict": len(not_in_dict)})
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
        "all_pass": all(r["no_residual"] and r["json_ok"] and r["db_nonmember"]
                        and r["db_dict_ok"] and not r["bad_tools"] and r["proof_fails"] == 0
                        for r in lint_rows),
        "iv_unclassified_by_key": _bykey(unclassified),
        "membership_proof_fails": proof_n,
        "not_in_static_dict_total": cover_n,
        "rows": lint_rows,
    }
    json.dump(lint, open(os.path.join(R, "e8-deid-lint.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in lint.items() if k != "rows"}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
