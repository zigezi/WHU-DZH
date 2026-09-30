#!/usr/bin/env python3
"""P5a.27 §六.2 工单：e7 注入物 F1 逆向 lint 初版（零 token）。

对 e7 每个 precedent 注入的计划，自动标注是否含"答案值"
（航班号/订单号/用户ID/支付ID/日期/金额/姓名），产出交用户人工终裁。
**脚本标的不作数，人标才作数。**

  /root/miniconda3/envs/mini-agent/bin/python scripts/p5a27_injectant_lint.py
"""
import hashlib
import json
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "backend", "logs", "trace.db")
OUT = os.path.join(ROOT, ".agent", "reports", "p5a27-injectant-lint.json")

PATTERNS = {
    "order_id": re.compile(r"#W\d+"),
    "user_id": re.compile(r"\b[a-z]+_[a-z]+_\d{3,5}\b"),
    "payment_id": re.compile(r"\b(?:credit_card|gift_card|certificate)_\d+\b"),
    "flight_no": re.compile(r"\b[A-Z]{2,3}\d{2,4}\b"),
    "date": re.compile(r"\d{4}-\d{2}-\d{2}"),
    "reservation_id": re.compile(r"\b[A-Z0-9]{6}\b"),
}
NAME="__name__"


def content_hash(plan):
    return hashlib.sha256(
        json.dumps(plan, ensure_ascii=False, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    # e7 injected spans
    W = "req_id LIKE 'TAU-%' AND created_at>='2026-09-29T14:30'"
    inj = {}
    for t in con.execute(f"SELECT task_id,req_id FROM tasks WHERE {W}"):
        for s in con.execute(
            "SELECT attributes FROM spans WHERE trace_id=? AND type='precedent_injected'",
            (t["task_id"],),
        ):
            a = json.loads(s["attributes"]) if s["attributes"] else {}
            inj[t["req_id"]] = (a.get("precedent_req"), a.get("content_sha256_16"))
    # snapshot plans for epoch 7
    snap = {}
    for r in con.execute("SELECT id,sig,req_id,plan_json FROM precedent_snapshots WHERE epoch=7"):
        try:
            plan = json.loads(r["plan_json"]) if r["plan_json"] else []
        except Exception:
            plan = []
        snap.setdefault((r["req_id"], content_hash(plan)), r["plan_json"])

    rows = []
    for task, (prec_req, ch) in sorted(inj.items()):
        pj = snap.get((prec_req, ch))
        plan = json.loads(pj) if pj else []
        text = json.dumps(plan, ensure_ascii=False)
        flags = {k: sorted(set(p.findall(text)))[:6] for k, p in PATTERNS.items()
                 if p.search(text)}
        # names come as values under first_name/last_name keys
        names = re.findall(r'"(?:first_name|last_name)":\s*"([^"]+)"', text)
        if names:
            flags["name"] = sorted(set(names))[:6]
        rows.append({
            "task": task, "injectant": prec_req, "self": task == prec_req,
            "content_sha256_16": ch, "plan_bytes": len(pj or ""),
            "answer_value_flags": flags,
            "has_answer_values": bool(flags),
        })
    out = {
        "note": "P5a.27 §六.2 F1 逆向 lint 初版；脚本初筛，人工终裁（S/A/U）",
        "n_injected": len(rows),
        "n_self": sum(1 for r in rows if r["self"]),
        "n_with_answer_values": sum(1 for r in rows if r["has_answer_values"]),
        "rows": rows,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"injected={out['n_injected']} self={out['n_self']} with_answer_values={out['n_with_answer_values']}")
    print("sample (self + first siblings):")
    for r in rows[:12]:
        print(f"  {r['task']:11} <- {r['injectant']:11} self={str(r['self']):5} flags={list(r['answer_value_flags'])}")
    print("->", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
