#!/usr/bin/env python3
"""P5a.87 §二：脱敏器结构不变性验证 + naming_proof（零 token）。

证明 e2_deident 只是脱敏（不动任务负载）：
  1) 确定性：同输入同输出；
  2) 结构保持：行数 / 金额集合 / 日期集合 / 章节标题数——raw vs deid 逐一致；
  3) naming_proof：含已知 PII 的合成样件 → 只碰标识符字段，其余字节不变。

  /root/miniconda3/envs/mini-agent/bin/python scripts/e2_deid_invariance.py
"""
import json
import os
import re
import sys
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from e2_deident import deid_text  # noqa: E402
from e2_unit_norm import extract_amounts  # noqa: E402

RAW = "/root/e2-corpus/raw"
DEID = "/root/e2-corpus/deid"
R = os.path.join(ROOT, ".agent", "reports")

DATE = re.compile(r"\d{4}\s*[-年/]\s*\d{1,2}\s*[-月/]\s*\d{1,2}")
SECTION = re.compile(r"^\s*(?:第[一二三四五六七八九十]+[章节]|[一二三四五六七八九十]+、|\d+(?:\.\d+)*\s+\S)")


def _amounts(text):
    return sorted(a[1] for a in extract_amounts(text))


def _dates(text):
    return sorted(DATE.findall(text))


def _sections(text):
    return sum(1 for ln in text.splitlines() if SECTION.match(ln))


def main():
    checks = []
    # 1) 确定性
    sample = open(sorted(glob.glob(os.path.join(RAW, "*.txt")))[0], encoding="utf-8", errors="replace").read()
    checks.append({"check": "deterministic", "pass": deid_text(sample, {}) == deid_text(sample, {})})

    # 2) 结构保持（逐文档）
    per_doc = []
    for fp in sorted(glob.glob(os.path.join(RAW, "*.txt"))):
        name = os.path.basename(fp)
        raw = open(fp, encoding="utf-8", errors="replace").read()
        dd = os.path.join(DEID, name)
        deid = open(dd, encoding="utf-8", errors="replace").read() if os.path.exists(dd) else ""
        row = {
            "doc": name,
            "lines_equal": raw.count("\n") == deid.count("\n"),
            "amounts_equal": _amounts(raw) == _amounts(deid),
            "dates_equal": _dates(raw) == _dates(deid),
            "sections_equal": _sections(raw) == _sections(deid),
        }
        row["pass"] = all(row[k] for k in ("lines_equal", "amounts_equal", "dates_equal", "sections_equal"))
        per_doc.append(row)
    checks.append({"check": "structure_preserved_all_docs", "pass": all(r["pass"] for r in per_doc),
                   "per_doc": per_doc})

    # 3) naming_proof：合成样件
    syn = "联系人：张三 手机13800138000 统一社会信用代码91330100MA27XW1234 邮编：310000。合计 100 万元。"
    out = deid_text(syn, {})
    touched_ids = ("张三" not in out and "13800138000" not in out and "91330100MA27XW1234" not in out)
    non_id_intact = ("邮编：310000" in out and "合计 100 万元" in out)
    checks.append({"check": "naming_proof_only_identifiers",
                   "pass": touched_ids and non_id_intact, "out": out})

    n, passed = len(checks), sum(1 for c in checks if c["pass"])
    out = {"note": "P5a.87 §二 脱敏结构不变性验证（naming_proof）",
           "n": n, "passed": passed, "all_pass": passed == n, "results": checks}
    json.dump(out, open(os.path.join(R, "e2-deid-invariance.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"all_pass": out["all_pass"], "passed": passed, "n": n,
                      "fails": [c for c in checks if not c["pass"]]}, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
