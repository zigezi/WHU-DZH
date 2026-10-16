#!/usr/bin/env python3
"""P5a.92 §2.1/§4.3：召回探针（独立于映射表）——从 raw 直接抽 PII 候选，断言 deid 中不出现。

修 a92 §2.1 空真病：旧"残留扫描"只查映射值（精度侧），看不见从未入表的 PII（召回侧）。
  /root/miniconda3/envs/mini-agent/bin/python scripts/e2_deid_recall_probe.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from e2_deident import (collect_names, company_cores, _clean_company, detect_watermark,  # noqa: E402
                        PATTERNS)

RAW = "/root/e2-corpus/raw"
DEID = "/root/e2-corpus/deid"
R = os.path.join(ROOT, ".agent", "reports")


def candidates(texts):
    cand = set()
    cand |= collect_names(texts)
    for t in texts:
        for m in PATTERNS[6][1].finditer(t):
            cand.add(_clean_company(m.group(1)))
        for kind in ("MOBILE", "LANDLINE", "IDCARD", "USCC", "EMAIL", "BANKACCT"):
            pat = dict(PATTERNS)[kind]
            for m in pat.finditer(t):
                cand.add(m.group(0))
    return cand


_SURNAME = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛范彭郎鲁韦昌马苗凤花方俞任袁柳唐罗薛伍余米贝姚孟高夏蔡田樊胡凌霍虞万支柯管卢莫房裘缪程邢翁储靳段富巫乌焦巴牧山谷车侯全班仰秋仲伊宫宁仇栾甘厉祖武符刘景詹龙叶幸司黎印白蒲从鄂索咸赖卓屠蒙池乔能苍双闻党翟谭贡劳姬申扶堵冉P雍桑桂牛通边燕冀浦尚农温庄晏柴瞿阎连茹习宦艾容向古易慎戈廖庾居衡步都耿满弘匡国文寇广禄阙东欧沃利蔚越隆师巩聂晁勾敖融冷辛阚那简饶空曾沙养鞠须丰巢关蒯相查后荆红游竺权盖益桓"


def surname_tokens(texts):
    """独立召回靶点：表格姓名格（2–3 字姓名 + 空格 + 数字，如 '姜美娟   35'）+ 首字为常见姓。"""
    out = set()
    for t in texts:
        for m in re.finditer(r"(?<![\u4e00-\u9fa5])([\u4e00-\u9fa5]{2,3})\s{2,}\d", t):
            tok = m.group(1)
            if tok[0] in _SURNAME:
                out.add(tok)
    return out


def main():
    raws = {f: open(os.path.join(RAW, f), encoding="utf-8", errors="replace").read()
            for f in os.listdir(RAW) if f.endswith(".txt")}
    companies = set()
    for t in raws.values():
        for m in PATTERNS[6][1].finditer(t):
            companies.add(_clean_company(m.group(1)))
    cand = candidates(list(raws.values())) | company_cores(companies) | surname_tokens(list(raws.values()))
    wm = detect_watermark(list(raws.values()))

    residual = []
    for fn, t in raws.items():
        dd = os.path.join(DEID, fn)
        deid = open(dd, encoding="utf-8", errors="replace").read() if os.path.exists(dd) else ""
        for c in cand:
            if len(c) >= 2 and c in deid:
                residual.append({"file": fn, "token": c})
        for c in wm:
            if any(ln.strip() == c for ln in deid.splitlines()):
                residual.append({"file": fn, "token": f"wm:{c}"})

    out = {"note": "P5a.92 召回探针（独立于映射表）",
           "candidates": len(cand), "watermark": sorted(wm),
           "residual_count": len(residual), "residual_sample": residual[:30],
           "recall_clean": not residual}
    json.dump(out, open(os.path.join(R, "e2-deid-recall-probe.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"candidates": len(cand), "residual_count": len(residual),
                      "recall_clean": out["recall_clean"],
                      "sample": residual[:15]}, ensure_ascii=False, indent=1))
    return 0 if out["recall_clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
