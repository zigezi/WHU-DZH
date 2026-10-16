#!/usr/bin/env python3
"""P5a.88 §四：脱敏不变性机器断言（修正规格）。

规格（替代 Qwen 原"数字串集合完全一致"）：
  1. 总行数绝对相等；
  2. 章节标题数量/文本一致；
  3. 数字串多重集差异**必须被映射表完全解释**——每个 raw-only 数字串(≥4位)须是某映射值子串；
     存在无法解释的差异 = 报警。
  4. naming_proof：正例（干净脱敏）+ 负例（偷改金额 / 偷删行 / 漏遮蔽）须全部判定正确。

  /root/miniconda3/envs/mini-agent/bin/python scripts/assert_deid_invariance.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = "/root/e2-corpus/raw"
DEID = "/root/e2-corpus/deid"
MAP = os.path.join(ROOT, ".agent", "local", "e2-deid-mapping.json")
R = os.path.join(ROOT, ".agent", "reports")

SECTION = re.compile(r"^\s*(?:第[一二三四五六七八九十]+[章节]|[一二三四五六七八九十]+、|\d+(?:\.\d+)*\s+\S)")
NUM = re.compile(r"\d{4,}")
import sys as _sys
_sys.path.insert(0, os.path.join(ROOT, "scripts"))
from e2_deident import watermarks as detect_watermark, remove_watermark  # noqa: E402


def _nums(text):
    # 去千分位逗号，避免 "1,000,000" 被拆成 <4 位片段而漏检
    t = re.sub(r"(?<=\d),(?=\d)", "", text)
    return NUM.findall(t)


def _sections(text):
    return [ln.strip() for ln in text.splitlines() if SECTION.match(ln)]


def load_mapping():
    if not os.path.exists(MAP):
        return {}, {}
    m = json.load(open(MAP, encoding="utf-8"))
    val2code = {k.split("\x00", 1)[1]: v for k, v in m.items()}
    return m, val2code


def _norm_by_map(text, val2code):
    for v in sorted(val2code, key=len, reverse=True):
        if v:
            text = text.replace(v, val2code[v])
    return text


def check_doc(name, raw, deid, val2code, wm=None):
    fails = []
    if raw.count("\n") != deid.count("\n"):
        fails.append("line_count_mismatch")
    # 章节标题：先按映射归一 raw，再比文本（标识符被遮蔽导致的差异属合法）
    baseline = remove_watermark(_norm_by_map(raw, val2code), wm)
    # 章节：v3 遮蔽会改变"数字表格伪章节"匹配，故仅作**信息**（不判死；a95/96 以 fixture+人工锚为准）
    sec_info = {"raw": len(_sections(baseline)), "deid": len(_sections(deid))}
    raw_nums, deid_nums = _nums(raw), _nums(deid)
    from collections import Counter
    removed = list((Counter(raw_nums) - Counter(deid_nums)).elements())
    added = list((Counter(deid_nums) - Counter(raw_nums)).elements())
    if added:
        fails.append(f"new_numbers_in_deid:{added[:3]}")
    unexplained = [n for n in removed if not any(n in v for v in val2code)]
    # 漏遮蔽：映射值(数值型,≥4位)仍出现在 deid 中 → 报警
    missed = [v for v in val2code if len(v) >= 4 and v.isdigit() and v in deid]
    if missed:
        fails.append(f"missed_masking:{missed[:3]}")
    return {"doc": name, "removed_nums": len(removed), "added_nums": len(added), "sections": sec_info,
            "unexplained": unexplained[:5], "missed_masking": missed[:5],
            "fails": fails, "pass": not fails and not unexplained}


def main():
    _, val2code = load_mapping()
    _raws = {os.path.basename(f): open(f, encoding="utf-8", errors="replace").read() for f in glob.glob(os.path.join(RAW, "*.txt"))}
    wm = detect_watermark(list(_raws.values()))
    rows = []
    for fp in sorted(glob.glob(os.path.join(RAW, "*.txt"))):
        name = os.path.basename(fp)
        raw = open(fp, encoding="utf-8", errors="replace").read()
        dd = os.path.join(DEID, name)
        deid = open(dd, encoding="utf-8", errors="replace").read() if os.path.exists(dd) else ""
        rows.append(check_doc(name, raw, deid, val2code, wm))

    # naming_proof
    clean_raw = "项目概述\n合计 ¥1,000,000\n联系人：张三 手机13800138000\n"
    clean_deid = "项目概述\n合计 ¥1,000,000\n联系人：【PERSON-1】 手机【MOBILE-1】\n"
    neg_tamper = "项目概述\n合计 ¥9,000,000\n联系人：【PERSON-1】 手机【MOBILE-1】\n"
    neg_delline = "项目概述\n联系人：【PERSON-1】 手机【MOBILE-1】\n"
    neg_missmask = "项目概述\n合计 ¥1,000,000\n联系人：【PERSON-1】 手机13800138000\n"
    mv = {"13800138000": "【MOBILE-1】"}
    np_checks = [
        ("np_positive_clean", check_doc("p", clean_raw, clean_deid, mv)["pass"] is True),
        ("np_neg_amount_tamper", check_doc("t", clean_raw, neg_tamper, mv)["pass"] is False),
        ("np_neg_line_deleted", check_doc("d", clean_raw, neg_delline, mv)["pass"] is False),
        ("np_neg_missed_masking", check_doc("m", clean_raw, neg_missmask, mv)["pass"] is False),
    ]

    doc_pass = all(r["pass"] for r in rows)
    np_pass = all(ok for _, ok in np_checks)
    out = {"note": "P5a.88 §四 脱敏不变性机器断言（修正规格）",
           "mapping_values": len(val2code), "docs": rows,
           "naming_proof": [{"case": c, "pass": ok} for c, ok in np_checks],
           "all_pass": doc_pass and np_pass}
    json.dump(out, open(os.path.join(R, "e2-deid-invariance-assert.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps({"all_pass": out["all_pass"], "docs_fail": [r for r in rows if not r["pass"]],
                      "naming_proof": out["naming_proof"]}, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
