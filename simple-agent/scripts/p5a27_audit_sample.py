#!/usr/bin/env python3
"""P5a.27 §六.2 / P5a.28 §二 用户人工抽检样本包生成（零 token）。

产出：
  .agent/reports/p5a27-audit-sample-blind.md  —— 19 例盲化样本（9 self + 10 sibling）
      每例：注入计划文本 + 该任务 trace 的关键动作段（不含臂别/结局，供 S/A/U 盲评）
  .agent/reports/p5a27-audit-sample-key.json  —— 解盲键（case -> task/arm/verdict/injectant）

  /root/miniconda3/envs/mini-agent/bin/python scripts/p5a27_audit_sample.py
"""
import hashlib
import json
import os
import random
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "backend", "logs", "trace.db")
R = os.path.join(ROOT, ".agent", "reports")
BLIND = os.path.join(R, "p5a27-audit-sample-blind.md")
KEY = os.path.join(R, "p5a27-audit-sample-key.json")


def chash(plan):
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
            (t["task_id"],)):
            a = json.loads(s["attributes"]) if s["attributes"] else {}
            inj[t["req_id"]] = {"task_id": t["task_id"],
                                "injectant": a.get("precedent_req"),
                                "hash": a.get("content_sha256_16")}
    snap = {}
    for r in con.execute("SELECT id,req_id,plan_json FROM precedent_snapshots WHERE epoch=7"):
        try:
            plan = json.loads(r["plan_json"]) if r["plan_json"] else []
        except Exception:
            plan = []
        snap[(r["req_id"], chash(plan))] = plan
    # verdict
    verd = {}
    for k, v in inj.items():
        for s in con.execute(
            "SELECT attributes FROM spans WHERE trace_id=? AND type='verdict'",
            (v["task_id"],)):
            a = json.loads(s["attributes"]) if s["attributes"] else {}
            verd[k] = a.get("decision")
    self_cases = [k for k, v in inj.items() if v["injectant"] == k]
    sib = [k for k, v in inj.items() if v["injectant"] != k]
    random.seed(20260929)
    sample = self_cases + random.sample(sib, min(10, len(sib)))
    random.shuffle(sample)

    lines = ["# P5a.27/28 人工抽检样本（盲化：不含臂别与结局）", "",
             "> 判读：S=结构帮助 / A=答案抄袭 / U=判不明（见 P5a.26 §四）。",
             "> 解盲键：`p5a27-audit-sample-key.json`（评完再看）。", ""]
    key = []
    for i, task in enumerate(sample, 1):
        v = inj[task]
        plan = snap.get((v["injectant"], v["hash"]), [])
        lines += [f"## Case {i:02d}", "", "**注入的计划（工具序列摘要）**：", "```",
                  json.dumps(plan, ensure_ascii=False, indent=1)[:4000], "```", "",
                  "**该任务 trace 的关键动作段（agent 实际调用）**：", "```"]
        for s in con.execute(
            "SELECT attributes FROM spans WHERE trace_id=? AND type='tool_call' ORDER BY start_time",
            (v["task_id"],)):
            a = json.loads(s["attributes"]) if s["attributes"] else {}
            err = " [ERR]" if "Error:" in str(a.get("output") or "") else ""
            lines.append(f"{a.get('tool')} {json.dumps(a.get('args'), ensure_ascii=False)}{err}")
        lines += ["```", ""]
        key.append({"case": i, "task": task, "injectant": v["injectant"],
                    "self": task == v["injectant"], "verdict": verd.get(task),
                    "content_sha256_16": v["hash"]})
    os.makedirs(R, exist_ok=True)
    open(BLIND, "w").write("\n".join(lines))
    json.dump({"note": "解盲键；评完 S/A/U 再看", "cases": key},
              open(KEY, "w"), ensure_ascii=False, indent=1)
    print(f"wrote {len(sample)} cases -> {BLIND}")
    print(f"key -> {KEY}")
    print("self:", len(self_cases), "sibling sampled:", len(sample) - len(self_cases))
    return 0


if __name__ == "__main__":
    sys.exit(main())
