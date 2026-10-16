#!/usr/bin/env python3
"""E2 评测器标定（a83 §四 / a85 §七.2）：缺陷注入夹具 → 灵敏度/特异度。

只用**脱敏副本** /root/e2-corpus/deid（原始 raw 只读封存，a86 §二.3）。
规则集为**框架演示（provisional）**——内容待裁者随任务书冻结（a85 §四）。
零 token。

  /root/miniconda3/envs/mini-agent/bin/python scripts/e2_eval_calibration.py
"""
import glob
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from e2_eval import check, eval_fingerprint  # noqa: E402
from e2_defect_injector import make_fixtures  # noqa: E402

DEID = "/root/e2-corpus/deid"
R = os.path.join(ROOT, ".agent", "reports")

# provisional ruleset（框架演示；内容非最终，待裁者冻结）
# number_fields 暂用单列重复字段"阶段总计"（含 ¥ 后缀，可公正判定）；
# 裸数多列表（合计 100 110 210）需列/勾稽语义，属规则集内容，待裁者冻结（a87 §四）。
RULESET = {
    "required_sections": ["项目"],
    "dimensions": [{"name": "风险-承诺", "require": ["风险"], "forbid": ["无风险"]}],
    "number_fields": ["阶段总计", "合计金额"],
}


def synthetic_number_docs():
    """夹具池合成：真实勾稽模板（同一金额在两处出现须相等，R2.2 型），数值可虚构。
    标 tier=fixture，只标定仪器，不入基线统计（a83 §四 / a89 §四）。"""
    docs = {}
    for i, v in enumerate(["2,000,000", "3,500,000", "1,280,000"], 1):
        docs[f"SYN-NUM-{i}"] = (
            "一、经费说明\n"
            f"项目总经费 合计金额 ¥{v}\n"
            "二、明细\n"
            "说明文字若干。\n"
            f"复核：项目总经费 合计金额 ¥{v}\n"
        )
    return docs


def main():
    docs = {}
    for f in sorted(glob.glob(os.path.join(DEID, "*.txt")))[:8]:
        docs[os.path.basename(f)[:-4]] = open(f, encoding="utf-8", errors="replace").read()

    # 只以"原始即通过"的文档作 clean 基（否则该 doc 本就违规，不洁）
    clean_bases = {n: t for n, t in docs.items() if check(t, RULESET)["pass"]}
    all_fixtures = []
    for n, t in clean_bases.items():
        all_fixtures += make_fixtures({n: t}, RULESET)
    # 夹具池合成 number 夹具（≥3 例，补样本薄；a89 §四 / a90 §五）
    syn = synthetic_number_docs()
    syn_n = 0
    for n, t in syn.items():
        fs = make_fixtures({n: t}, RULESET)
        all_fixtures += fs
        syn_n += sum(1 for f in fs if f["kind"] == "number_inconsistent")

    per_kind = defaultdict(lambda: {"n": 0, "flagged": 0})
    clean_n = clean_flagged = 0
    for fx in all_fixtures:
        verdict = check(fx["doc"], RULESET)
        if fx["label"] == "clean":
            clean_n += 1
            clean_flagged += (not verdict["pass"])
        else:
            per_kind[fx["kind"]]["n"] += 1
            per_kind[fx["kind"]]["flagged"] += (not verdict["pass"])

    def rate(a, b):
        return round(a / b, 3) if b else None

    out = {
        "note": "E2 评测器标定（provisional ruleset；缺陷注入夹具灵敏度/特异度）",
        "eval_fingerprint": eval_fingerprint(),
        "docs_total": len(docs), "clean_bases": len(clean_bases),
        "specificity": rate(clean_n - clean_flagged, clean_n),
        "sensitivity_by_kind": {
            k: {"n": v["n"], "flagged": v["flagged"], "rate": rate(v["flagged"], v["n"])}
            for k, v in per_kind.items()},
        "fixtures": len(all_fixtures),
        "synthetic_number_fixtures": syn_n,
        "ruleset_provisional": RULESET,
    }
    json.dump(out, open(os.path.join(R, "e2-eval-calibration.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
