#!/usr/bin/env python3
"""P5a.59 §二：阶段二 小规模活体验证批（陷阱富集，7 哨兵在岗，硬顶 1.5M tokens）。
  /root/miniconda3/envs/mini-agent/bin/python scripts/organ_stage2.py
"""
import json
import os
import sqlite3
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
R = os.path.join(ROOT, ".agent", "reports")
sys.path.insert(0, BACKEND)
import requests  # noqa: E402

BASE = os.getenv("SA_BASE_URL", "http://localhost:8000")
DB = os.path.join(BACKEND, "logs", "trace.db")

# P5a.59 §六 重跑批：锁死 5 + giftcard 2 + 对照 3（硬顶 1.5M，运行时闸强制）
BATCH = ["TAU-R-041", "TAU-R-072", "TAU-R-098", "TAU-R-105", "TAU-R-058",   # 锁死 5
         "TAU-A-023", "TAU-A-022",                                          # 礼品卡余额 2
         "TAU-A-007", "TAU-R-019", "TAU-A-002"]                             # 对照 3
BUDGET_CAP = int(os.getenv("SA_BUDGET_CAP", "1500000"))
ASSETS = ["lock_order_v1", "repeat_failure_v1", "items_count_match_v1",
          "non_delivered_exchange_v1", "flight_availability_enforce_v1",
          "payment_amount_sum_enforce_v1", "gift_card_balance_enforce_v1"]


def submit(req_id):
    r = requests.post(f"{BASE}/task/submit", json={"content": "你好，我需要帮助", "req_id": req_id}, timeout=30)
    r.raise_for_status()
    return r.json()["task_id"]


def wait(task_id, timeout_s=1200):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            j = requests.get(f"{BASE}/task/{task_id}", timeout=30).json()
        except Exception:  # noqa: BLE001
            time.sleep(2); continue
        if j.get("status") in ("success", "failed", "g_halted", "abstained"):
            return j
        time.sleep(3)
    return {"status": "timeout"}


def fires(con, task_id):
    out = []
    for s in con.execute("SELECT attributes FROM spans WHERE trace_id=? AND type='interceptor_fire'", (task_id,)):
        a = json.loads(s["attributes"]) if s["attributes"] else {}
        out.append(a.get("rule"))
    return out


def verdict(con, task_id):
    r = con.execute("SELECT attributes FROM spans WHERE trace_id=? AND type='verdict'", (task_id,)).fetchone()
    return (json.loads(r["attributes"]).get("decision") if r and r["attributes"] else None)


def main():
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    rows, tokens = [], 0
    stopped = None
    for rid in BATCH:
        if tokens >= BUDGET_CAP:                 # P5a.59 §三：运行时预算闸（任务间累计检查，触顶即停）
            stopped = f"budget_cap_reached:{tokens}>={BUDGET_CAP}"
            print("[budget] STOP:", stopped); break
        tid = submit(rid)
        j = wait(tid)
        v = verdict(con, tid)
        f = fires(con, tid)
        rows.append({"req_id": rid, "task_id": tid, "status": j.get("status"),
                     "verdict": v, "fires": f, "tokens": j.get("llm_tokens") or 0})
        tokens += j.get("llm_tokens") or 0
        print(f"  {rid} status={j.get('status')} verdict={v} fires={f} tok={j.get('llm_tokens')}")
    by = {a: {"fires": 0, "on_pass": 0, "on_fail": 0} for a in ASSETS}
    for r in rows:
        for rule in r["fires"]:
            if rule in by:
                by[rule]["fires"] += 1
                by[rule]["on_pass" if r["verdict"] == "PASS" else "on_fail"] += 1
    lock_batch = [r for r in rows if r["req_id"] in ("TAU-R-041", "TAU-R-072", "TAU-R-098", "TAU-R-105", "TAU-R-058")]
    out = {"note": "P5a.59 阶段二 重跑批（10 题，7 哨兵在岗，无 A/B，运行时预算闸）",
           "budget_cap": BUDGET_CAP, "stopped": stopped,
           "n": len(rows), "tokens": tokens,
           "passed": sum(1 for r in rows if r["verdict"] == "PASS"),
           "fire_table": by, "lock_batch": [{"req": r["req_id"], "verdict": r["verdict"], "fires": r["fires"]} for r in lock_batch],
           "rows": rows}
    # P5a.61 §三.2 立法：批次结束时 ring_mine 自动消化本批全部 FAIL 尸体
    try:
        import subprocess
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "organ_ingest_corpses.py")],
                       cwd=ROOT, capture_output=True, text=True, timeout=120)
        cj = os.path.join(R, "organ-corpse-triage.json")
        if os.path.exists(cj):
            out["corpse_triage"] = json.load(open(cj))
    except Exception as e:  # noqa: BLE001
        out["corpse_triage_error"] = repr(e)[:120]
    json.dump(out, open(os.path.join(R, "organ-stage2.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
