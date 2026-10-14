#!/usr/bin/env python3
"""P5a.69：ring_draft LLM 起草器联调（管线唯一 LLM 格子；双效：器官成熟 + 尸体来源）。

纪律：
- 硬顶 0.1M tokens，任务间累计运行时闸（SA_RINGDRAFT_CAP）；
- 输入只用**已有语料**（τ 已裁决候选 + 负先例），known-answer 自检；
- **不产生新开采**；草稿一律进证据域（.agent/reports/ring-drafts/），不部署、不出生、不进注册册；
- 宪法边界照旧（不碰 reward/verifier、不改测试、不自改死因分类法）。
验收：端到端贯通 + 草稿要素齐全（谓词文本/点火条件/可观测性声明/误伤面自评/干预语义型）；**不判质量**。
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
R = os.path.join(ROOT, ".agent", "reports")
DRAFT_DIR = os.path.join(R, "ring-drafts")
sys.path.insert(0, BACKEND)
from monitor.organ import Pipeline  # noqa: E402

CLUSTERS_EXPECT = {  # known-answer 自检（干预语义型）
    "lock_order": "benign-reissue", "repeat_failure": "benign-reissue",
    "items_count": "behavior-reroute", "non_delivered": "behavior-reroute",
    "payment_sum": "behavior-reroute", "certificate_update": "behavior-reroute",
    "flight_availability": "benign-reissue", "gift_card_balance": "behavior-reroute",
}
REQUIRED = ["predicate_text", "firing_condition", "observability_declaration",
            "false_positive_self_assessment", "intervention_semantics"]


def client():
    env = {}
    with open(os.path.join(BACKEND, ".env"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1); env[k.strip()] = v.strip()
    from openai import OpenAI
    return OpenAI(api_key=env["DEEPSEEK_API_KEY"],
                  base_url=env.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"))


def draft(cli, model, pattern, disposition):
    prompt = ("你是免疫资产的谓词起草器。给定一条死亡模式的分诊处置，输出一个**拦截器资产规格**初稿。\n"
              f"死亡模式: {json.dumps(pattern, ensure_ascii=False)}\n"
              f"分诊处置: {disposition}\n"
              "只输出 JSON，字段：\n"
              '- predicate_text: 一句话规则文本\n'
              '- firing_condition: 确定性点火条件（须可由 args/可观测状态计算）\n'
              '- observability_declaration: 点火条件的可观测性声明\n'
              '- false_positive_self_assessment: 误伤面自评（哪些合法形状会被撞）\n'
              '- intervention_semantics: "benign-reissue" 或 "behavior-reroute"\n')
    r = cli.chat.completions.create(model=model, temperature=0,
                                    messages=[{"role": "user", "content": prompt}])
    toks = getattr(getattr(r, "usage", None), "total_tokens", 0) or 0
    txt = r.choices[0].message.content or ""
    m = re.search(r"\{.*\}", txt, re.S)
    try:
        obj = json.loads(m.group(0)) if m else {}
    except Exception:  # noqa: BLE001
        obj = {}
    return obj, toks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=int(os.getenv("SA_RINGDRAFT_CAP", "100000")))
    args = ap.parse_args()
    patterns = json.load(open(os.path.join(R, "p5a36-death-patterns.json")))["patterns"]
    pipe = Pipeline()
    cli = client()
    model = os.getenv("MODEL_NAME", "deepseek-chat")
    os.makedirs(DRAFT_DIR, exist_ok=True)
    tokens, drafts, stopped = 0, [], None
    for p in patterns[:25]:
        if tokens >= args.cap:
            stopped = f"budget_cap_reached:{tokens}>={args.cap}"; break
        disp = pipe.classify_disposition(p)
        obj, tk = draft(cli, model, {"pattern_id": p["pattern_id"], "kind": p["kind"]}, disp)
        tokens += tk
        missing = [k for k in REQUIRED if not obj.get(k)]
        # known-answer 自检：干预语义型是否与预期一致（仅自检，不判质量）
        exp = CLUSTERS_EXPECT.get(p.get("kind"), None)
        match = (exp is None) or (obj.get("intervention_semantics") == exp)
        did = re.sub(r"\W+", "_", p["pattern_id"])[:40]
        json.dump({"pattern": p["pattern_id"], "kind": p["kind"], "disposition": disp,
                   "draft": obj, "tokens": tk}, open(os.path.join(DRAFT_DIR, did + ".json"), "w"),
                  ensure_ascii=False, indent=1)
        drafts.append({"pattern_id": p["pattern_id"], "disposition": disp, "missing": missing,
                       "semantics": obj.get("intervention_semantics"), "expected": exp,
                       "known_answer_match": match, "tokens": tk})
    elements_ok = all(not d["missing"] for d in drafts)
    e2e_ok = len(drafts) > 0 and all(os.path.exists(os.path.join(DRAFT_DIR, re.sub(r"\W+", "_", d["pattern_id"])[:40] + ".json")) for d in drafts)
    ka = [d for d in drafts if d["expected"]]
    ka_ok = all(d["known_answer_match"] for d in ka) if ka else None
    out = {"note": "P5a.69 ring_draft 联调（唯一 LLM 格子；草稿入证据域，不部署）",
           "cap": args.cap, "stopped": stopped, "tokens": tokens,
           "drafts": len(drafts), "end_to_end_ok": e2e_ok,
           "elements_complete_ok": elements_ok,
           "known_answer_semantics_ok": ka_ok,
           "acceptance_ok": e2e_ok and elements_ok,
           "rows": drafts}
    json.dump(out, open(os.path.join(R, "ring-draft-integration.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
