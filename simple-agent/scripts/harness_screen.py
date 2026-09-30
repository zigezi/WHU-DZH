#!/usr/bin/env python3
"""P5a.20 便签 2（第 0 步）— 线束保真初筛器 harness-fidelity screen。

机器**只产"候选隔离 + 理由"**，不附 PASS/FAIL 判定（防锚定协议，MR-7）；人审签字后才约束。

检查项：
  C1 GT 自洽重放        : 从初始 data 依序 replay GT actions（排除 terminate）→ reward 必须=1
  C2 instruction⇄GT     : instruction 提及的实体 vs GT 动作集（启发式，低置信）
  C3 模拟器⇄GT          : 每轮 user turn 的日期/航点/数量 vs GT args（启发式，低置信）
  C4 GT 前提可达性      : GT replay 中任一步返回 Error / 抛异常
  C5 臂与注入标注       : 跨 epoch arm 是否一致

运行（需 tau venv，自带 litellm）：
  PYTHONPATH=.agent/vendor/tau-bench .agent/venv/tau/bin/python scripts/harness_screen.py \
      --epoch 4 5 --req TAU-A-008 TAU-A-019 TAU-R-105 TAU-A-027 TAU-A-007

红线：不落 instruction 明文；env.user 置为 StubUser，避免 HUMAN 策略回显指令。
"""
import argparse
import dataclasses
import hashlib
import json
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)

DB_PATH = os.path.join(BACKEND, "logs", "trace.db")
REQ_DIR = os.path.join(BACKEND, "requirements", "tau")
OUT_DIR = os.path.join(ROOT, ".agent", "reports")

RESPOND = "respond"
DATE_ISO = re.compile(r"\d{4}-\d{2}-\d{2}")
DATE_MD = re.compile(r"\b(\d{1,2})/(\d{1,2})\b")
AAA = re.compile(r"\b[A-Z]{3}\b")
ORDER_ID = re.compile(r"#W\d{6,}")
RESV_ID = re.compile(r"\b(?=[A-Z0-9]*\d)[A-Z0-9]{6}\b")
RETURN_VERB = re.compile(r"\b(return|exchange|swap|refund)\b", re.I)

_PRODUCT_NAMES = None
_ITEM_NAME = None


class StubUser:
    """Zero-LLM replay stub; 防 HUMAN 策略打印 instruction。"""

    def reset(self, instruction=None):
        return "###STOP###"

    def step(self, content):
        return "###STOP###"

    def get_total_cost(self):
        return 0.0


# --------------------------------------------------------------------------- #
# tau env helpers
# --------------------------------------------------------------------------- #
def make_env(env_name, split, idx):
    from tau_bench.envs.user import UserStrategy
    if env_name == "airline":
        from tau_bench.envs.airline.env import MockAirlineDomainEnv as EnvCls
    elif env_name == "retail":
        from tau_bench.envs.retail.env import MockRetailDomainEnv as EnvCls
    else:
        raise ValueError(env_name)
    env = EnvCls(user_strategy=UserStrategy.HUMAN, user_model="n/a",
                 user_provider=None, task_split=split, task_index=idx)
    env.user = StubUser()  # 关键：覆盖 HUMAN，避免回显/读 stdin
    return env


def load_gt(env_name, split, idx):
    if env_name == "airline":
        from tau_bench.envs.airline.tasks_test import TASKS
    else:
        from tau_bench.envs.retail.tasks_test import TASKS_TEST as TASKS
    t = TASKS[idx]
    return dataclasses.asdict(t) if dataclasses.is_dataclass(t) else t.__dict__


def a_name(a):
    return a.get("name") if isinstance(a, dict) else getattr(a, "name", None)


def a_kwargs(a):
    return a.get("kwargs", {}) if isinstance(a, dict) else getattr(a, "kwargs", {})


def kwargs_walk(obj):
    out = []
    if isinstance(obj, dict):
        for v in obj.values():
            out += kwargs_walk(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            out += kwargs_walk(v)
    elif isinstance(obj, str):
        out.append(obj)
    return out


def retail_maps():
    global _PRODUCT_NAMES, _ITEM_NAME
    if _PRODUCT_NAMES is None:
        from tau_bench.envs.retail.data import load_data
        d = load_data()
        _ITEM_NAME = {}
        for o in d["orders"].values():
            for it in o["items"]:
                _ITEM_NAME[it["item_id"]] = d["products"][it["product_id"]]["name"]
        _PRODUCT_NAMES = sorted({p["name"] for p in d["products"].values()})
    return _PRODUCT_NAMES, _ITEM_NAME


def gt_replay(env_name, split, idx):
    """C1+C4：GT 重放。

    C1 判据 = **确定性**（两次重放 DB hash 相等）；不用 calculate_reward().reward，
    因为带 outputs 的任务 replay 无 RESPOND → outputs 检查必失败，会误报。
    C4 判据 = 任一步返回 Error / 抛异常（前提不可达）。
    """
    hashes, errors = [], []
    for _ in range(2):
        env = make_env(env_name, split, idx)
        env.reset(task_index=idx)
        for a in env.task.actions:
            if a.name in env.terminate_tools or a.name == RESPOND:
                continue
            try:
                obs = env.step(a)
                if "error" in str(obs).lower():
                    errors.append({"action": a.name,
                                   "observation": str(obs).split("info=")[0][:120]})
            except Exception as e:  # noqa: BLE001
                errors.append({"action": a.name, "exception": repr(e)[:120]})
        hashes.append(env.get_data_hash())
    return {"deterministic": hashes[0] == hashes[1], "errors": errors}


# --------------------------------------------------------------------------- #
# trace access
# --------------------------------------------------------------------------- #
def epoch_of(ts):
    if ts and ts.startswith("2026-09-15"):
        return 4
    if ts and ts.startswith("2026-09-16"):
        return 5
    return None


def load_traces(con, epochs, reqs=None):
    rows = []
    for r in con.execute(
        "SELECT task_id,req_id,created_at FROM tasks"
        " WHERE req_id LIKE 'TAU-%' ORDER BY created_at"
    ):
        e = epoch_of(r["created_at"])
        if e not in epochs or (reqs and r["req_id"] not in reqs):
            continue
        arm = inj = verd = None
        user_turns = []
        for s in con.execute(
            "SELECT type,attributes FROM spans WHERE trace_id=?", (r["task_id"],)
        ):
            try:
                a = json.loads(s["attributes"]) if s["attributes"] else {}
            except Exception:
                a = {}
            if s["type"] == "arm_choice":
                arm = {"arm": a.get("arm"), "exploration": a.get("exploration")}
            elif s["type"] == "precedent_injected":
                inj = {"sig": a.get("precedent_sig"),
                       "tokens_injected": a.get("tokens_injected")}
            elif s["type"] == "verdict":
                verd = a.get("decision")
            elif s["type"] == "dialogue_turn" and a.get("role") == "user":
                user_turns.append(a.get("text") or "")
        rows.append({"epoch": e, "req_id": r["req_id"], "trace_id": r["task_id"],
                     "arm": arm, "injection": inj, "verdict": verd,
                     "user_turns": user_turns})
    return rows


# --------------------------------------------------------------------------- #
# entity collection + heuristics
# --------------------------------------------------------------------------- #
def collect_gt(env_name, gt):
    kws = []
    for a in gt.get("actions", []):
        kws += kwargs_walk(a_kwargs(a))
    dates = set()
    airports = set()
    orders = set()
    names = set()
    product_names, item_name = retail_maps() if env_name == "retail" else (set(), {})
    for s in kws:
        dates |= set(DATE_ISO.findall(s))
        for m, d in DATE_MD.findall(s):
            dates.add(f"2024-{int(m):02d}-{int(d):02d}")
        orders |= set(ORDER_ID.findall(s))
        airports |= set(AAA.findall(s))
        if s in item_name:
            names.add(item_name[s])
        if s in product_names:
            names.add(s)
    return {"dates": dates, "airports": airports, "orders": orders,
            "products": names, "raw": kws}


def check_c2(env_name, gt, ent):
    instr = gt.get("instruction") or ""
    cands = []
    if env_name == "retail":
        product_names, _ = retail_maps()
        mentioned = set()
        for sent in re.split(r"(?<=[.!?])\s+", instr):
            if not RETURN_VERB.search(sent):
                continue
            low = sent.lower()
            for pn in product_names:
                toks = [w for w in re.split(r"[^a-z]+", pn.lower()) if len(w) >= 4]
                if pn.lower() in low or any(t in low for t in toks):
                    mentioned.add(pn)
        missing = sorted(mentioned - ent["products"])
        for pn in missing:
            cands.append({"check": "C2", "confidence": "low", "human_ratify": True,
                          "reason": f"instruction 退货语境内提及商品 {pn!r}，但 GT 动作未退货该商品"})
    else:
        instr_resv = set(RESV_ID.findall(instr.upper()))
        gt_resv = set(RESV_ID.findall(" ".join(ent["raw"]).upper()))
        for rid in sorted(instr_resv - gt_resv):
            if rid in ("MIGHT", "WOULD", "COULD"):
                continue
            cands.append({"check": "C2", "confidence": "low", "human_ratify": True,
                          "reason": f"instruction 提及预订号 {rid}，但 GT 动作未涉及"})
    return cands


def check_c3(env_name, gt, ent, user_turns):
    cands = []
    if not ent["dates"] and not ent["airports"]:
        return cands
    for i, ut in enumerate(user_turns):
        u_dates = set(DATE_ISO.findall(ut)) | {
            f"2024-{int(m):02d}-{int(d):02d}" for m, d in DATE_MD.findall(ut)}
        bad = sorted(d for d in u_dates if d not in ent["dates"])
        if bad and ent["dates"]:
            cands.append({"check": "C3", "confidence": "low", "human_ratify": True,
                          "turn": i, "reason": f"user 日期 {bad} 不在 GT {sorted(ent['dates'])}"})
        if env_name == "airline" and ent["airports"]:
            u_air = {t for t in AAA.findall(ut)}
            bad_air = sorted(u_air - ent["airports"])
            if bad_air:
                cands.append({"check": "C3", "confidence": "low", "human_ratify": True,
                              "turn": i, "reason": f"user 航点 {bad_air} 不在 GT {sorted(ent['airports'])}"})
        if env_name == "airline" and re.search(r"\b(just|only)\s+[A-Z][a-z]+", ut):
            n_pax = sum(len(a_kwargs(a).get("passengers", [])) for a in gt.get("actions", [])
                        if a_name(a) == "book_reservation")
            if n_pax > 1:
                cands.append({"check": "C3", "confidence": "low", "human_ratify": True,
                              "turn": i, "reason": f"'just/only <name>' 收窄，但 GT book 乘客={n_pax}"})
    # dedup
    seen, ded = set(), []
    for c in cands:
        k = c["reason"]
        if k not in seen:
            seen.add(k)
            ded.append(c)
    return ded


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def screen(epochs, reqs):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    traces = load_traces(con, epochs, reqs)
    rid_list = sorted({t["req_id"] for t in traces})
    results = []
    for rid in rid_list:
        spec = json.load(open(os.path.join(REQ_DIR, f"{rid}.json")))
        env_name, split, idx = spec["tau_env"], spec["tau_task_split"], spec["tau_task_id"]
        gt = load_gt(env_name, split, idx)
        ent = collect_gt(env_name, gt)
        try:
            rp = gt_replay(env_name, split, idx)
        except Exception as e:  # noqa: BLE001
            rp = {"reward": None, "errors": [{"exception": repr(e)[:200]}]}
        checks = []
        if not rp["deterministic"]:
            checks.append({"check": "C1", "confidence": "high",
                           "reason": "GT 重放非确定（两次 DB hash 不等）"})
        if rp["errors"]:
            acts = sorted({e.get("action") or e.get("exception", "?") for e in rp["errors"]})
            checks.append({"check": "C4", "confidence": "high",
                           "reason": f"GT replay 报错: {acts}",
                           "detail": rp["errors"][:4]})
        checks += check_c2(env_name, gt, ent)
        rows = [t for t in traces if t["req_id"] == rid]
        arms = {t["epoch"]: (t["arm"] or {}).get("arm") for t in rows}
        if len(set(a for a in arms.values() if a)) > 1:
            checks.append({"check": "C5", "confidence": "high",
                           "reason": f"跨 epoch arm 不一致: {arms}"})
        for t in rows:
            for c in check_c3(env_name, gt, ent, t["user_turns"]):
                checks.append({**c, "epoch": t["epoch"], "trace_id": t["trace_id"]})
        results.append({
            "req_id": rid, "tau_env": env_name, "tau_task_id": idx,
            "instruction_sha256_16": hashlib.sha256(
                (gt.get("instruction") or "").encode()).hexdigest()[:16],
            "arms": arms,
            "verdicts": {t["epoch"]: t["verdict"] for t in rows},
            "quarantine_candidate": len(checks) > 0,
            "checks": checks,
        })
    return {"epochs": epochs, "note": "机器初筛候选，人审签字后方为约束清单（MR-7）",
            "counts": {"tasks": len(results),
                       "candidates": sum(1 for r in results if r["quarantine_candidate"])},
            "tasks": results}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epoch", nargs="+", type=int, default=[4, 5])
    ap.add_argument("--req", nargs="*", default=None)
    args = ap.parse_args()
    out = screen(args.epoch, args.req or None)
    os.makedirs(OUT_DIR, exist_ok=True)
    p = os.path.join(OUT_DIR, "p5a20-screen.json")
    json.dump(out, open(p, "w"), ensure_ascii=False, indent=1)
    print(f"[screen] {out['counts']['candidates']}/{out['counts']['tasks']} candidates -> {p}")
    for r in out["tasks"]:
        if r["quarantine_candidate"]:
            print(f"  {r['req_id']:11} {r['arms']} {r['verdicts']} -> "
                  + "; ".join(c["reason"][:70] for c in r["checks"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
