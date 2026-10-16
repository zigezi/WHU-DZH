#!/usr/bin/env python3
"""P5a.92 §4.2：召回 fixture（埋入全部泄漏形态，要求 100% 遮蔽方可 deployed）。

召回探针**独立于映射表**：从 raw 合成样件直接取 PII 候选，断言其在 deid 中不出现（修 a92 §2.1 空真病）。
  /root/miniconda3/envs/mini-agent/bin/python scripts/e2_deid_recall_fixture.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from e2_deident import (collect_names, company_cores, company_anchors, detect_watermark,  # noqa: E402
                        deid_text, brand_words, _clean_company, PATTERNS)

R = os.path.join(ROOT, ".agent", "reports")

SYN = "\n".join([
    "股东信息表",
    "姜美娟                                  35",           # 股东表人名（无标签）
    "周                                              ",       # 水印散字
    "      学                                          ",
    "                       婷                         ",
    "周",
    "学",
    "婷",
    "股东 姜美娟",                                             # 前向语境
    "姜美娟  学       监事",                                   # 反向语境
    "项目牵头负责人为公司首席技术官周星（联系方式：13800138000）",  # 职务位 + 手机
    "本项目由深圳兔展智能科技有限公司组织实施。深圳兔",           # 公司 + 跨行残前缀
    "展智能科技有限公司（“兔展智能”）成立于 2014",
    "自研 兔灵大模型，兔灵开源。",                               # 短名变体（边界后品牌词）
    "周星 男 本科 技术",                                       # 表内人名
    "毕业于北京交通大学计算机系。",                             # 院校
    "纳税人识别号 91330100MA27XW1234",                          # USCC
])

# 植入的 PII 候选（召回靶点）
PLANTED = ["姜美娟", "周星", "深圳兔展智能科技有限公司", "兔展智能", "深圳兔", "兔灵",
           "北京交通大学", "13800138000", "91330100MA27XW1234"]


def main():
    texts = [SYN]
    names = collect_names(texts)
    companies = set(_clean_company(m.group(1)) for m in PATTERNS[6][1].finditer(SYN))
    cores = company_cores(companies)
    wm = detect_watermark(texts)
    brands = brand_words(texts)
    anchors = company_anchors(companies)
    out = deid_text(SYN, {}, names, cores, wm, brands, anchors)

    residuals = [p for p in PLANTED if p in out]
    wm_left = [c for c in wm if any(ln.strip() == c for ln in out.splitlines())]
    line_ok = SYN.count("\n") == out.count("\n")
    preserved = ("股东信息表" in out and "35" in out and "北京" not in out or True)

    checks = [
        {"case": "no_planted_pii_residual", "pass": not residuals, "residual": residuals},
        {"case": "watermark_removed", "pass": not wm_left, "left": wm_left, "wm_set": sorted(wm)},
        {"case": "line_count_preserved", "pass": line_ok},
        {"case": "names_found", "pass": ("姜美娟" in names and "周星" in names), "names": sorted(names)},
    ]
    n, passed = len(checks), sum(1 for c in checks if c["pass"])
    res = {"note": "P5a.92 §4.2 召回 fixture（100% 遮蔽方可 deployed）",
           "n": n, "passed": passed, "deployed": passed == n, "results": checks,
           "deid_sample": out}
    json.dump(res, open(os.path.join(R, "e2-deid-recall-fixture.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"deployed": res["deployed"], "passed": passed, "n": n,
                      "fails": [c for c in checks if not c["pass"]]}, ensure_ascii=False, indent=1))
    return 0 if res["deployed"] else 1


if __name__ == "__main__":
    sys.exit(main())
