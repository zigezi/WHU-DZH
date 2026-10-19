#!/usr/bin/env python3
"""E2 独立召回探针（P5a.92 §2.1 / a96 A3）：从 raw 直接抽候选，查 deid 残留。

独立于脱敏器的候选源：PII 正则 + 公司全称（折叠）/核心 + 姓氏表格格（原文，姓名+空格+数字）+ 长号。
量程声明：只覆盖**上述候选源**；未入表/无候选特征者由人工锚覆盖。
  /root/miniconda3/envs/mini-agent/bin/python scripts/e2_deid_recall_probe.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import e2_deident as D  # noqa: E402

RAW = "/root/e2-corpus/raw"
DEID = "/root/e2-corpus/deid"
R = os.path.join(ROOT, ".agent", "reports")


def candidates(texts):
    cand = set()
    folded = [D._fold(t) for t in texts]
    for f in folded:
        for kind, pat in D.PII:
            for m in pat.finditer(f):
                cand.add(m.group(0))
        for m in re.compile(r"\d{4}\s*年\s*第\s*[A-Z]?\d+\s*号").finditer(f):
            cand.add(m.group(0))
        for m in D.COMPANY.finditer(f):
            cand.add(D._clean_company(m.group(1)))
            for c in D._company_cores(D._clean_company(m.group(1))):
                cand.add(c)
    for t in texts:                                     # 表格姓名格（原文）
        for m in re.finditer(r"(?<![\u4e00-\u9fa5])([\u4e00-\u9fa5]{2,3})\s{2,}\d", t):
            if m.group(1)[0] in D.SURNAME:
                cand.add(m.group(1))
    return {c for c in cand if len(c) >= 2}


def main():
    raws = {f: open(os.path.join(RAW, f), encoding="utf-8", errors="replace").read()
            for f in os.listdir(RAW) if f.endswith(".txt")}
    cand = candidates(list(raws.values()))
    wl = D.load_whitelist()
    cand = {c for c in cand if c not in wl}          # 白名单词非 PII，剔除假阳性
    residual = []
    for fn, t in raws.items():
        dd = os.path.join(DEID, fn)
        deid = open(dd, encoding="utf-8", errors="replace").read() if os.path.exists(dd) else ""
        for c in cand:
            hit = (c in deid) or (any(ch.isascii() and ch.isalpha() for ch in c) and c.lower() in deid.lower())
            if hit:
                residual.append({"file": fn, "token": c})
    out = {"note": "E2 独立召回探针",
           "candidates": len(cand), "residual_count": len(residual),
           "residual_sample": residual[:30], "recall_clean": not residual,
           "coverage_declaration": "召回残留 {}（量程：PII 正则 + 公司全称/核心 + 姓氏表格格 + 长号 + 大小写折叠；"
                                   "**不覆盖**：未入表实体的发现 / 引用块内英文作者 / 域尾与电话碎片 / 表内嵌入——"
                                   "上述由推测层标记清单 + 人工校正覆盖；本残留即校正队列）".format(len(residual))}
    json.dump(out, open(os.path.join(R, "e2-deid-recall-probe.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"candidates": len(cand), "residual_count": len(residual),
                      "recall_clean": out["recall_clean"], "sample": residual[:15]},
                     ensure_ascii=False, indent=1))
    return 0 if out["recall_clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
