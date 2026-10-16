#!/usr/bin/env python3
"""P5a.86 §二.2：E2 语料脱敏（PII 遮蔽 → 代号；映射本地 gitignored）。

- 输入：/root/e2-corpus/raw/*.txt（正文层）
- 输出：/root/e2-corpus/deid/*.txt（PII 替换为【KIND-n】代号）
- 映射：.agent/local/e2-deid-mapping.json（**gitignored，绝不入证据/仓库**，P5a.33）
零 token、确定性。

  /root/miniconda3/envs/mini-agent/bin/python scripts/e2_deident.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = "/root/e2-corpus/raw"
DEID = "/root/e2-corpus/deid"
MAP = os.path.join(ROOT, ".agent", "local", "e2-deid-mapping.json")

# 顺序敏感：长/特定模式优先
PATTERNS = [
    ("EMAIL", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("MOBILE", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("LANDLINE", re.compile(r"(?<!\d)0\d{2,3}-\d{7,8}(?!\d)")),
    ("IDCARD", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")),
    ("USCC", re.compile(r"(?<![0-9A-Z])[0-9A-HJ-NPQRTUWXY]{18}(?![0-9A-Z])")),
    ("BANKACCT", re.compile(r"(?<!\d)\d{16,19}(?!\d)")),
    ("COMPANY", re.compile(r"[\u4e00-\u9fa5]{2,20}(?:有限公司|股份有限公司|集团|研究院|设计院|事务所|银行|大学|学院|中心)")),
]

# 姓名上下文（收集候选名 → 全局替换，堵"同名词在别处漏遮蔽"，P5a.88 §四）
NAME_CTX = re.compile(
    r"(?:联系人|法定代表人|负责人|项目负责人|项目总部责任人|责任人|项目经理|项目总监|技术负责人|"
    r"编制人|审核人|批准人|签字|签名|姓名)[：:\s]+([\u4e00-\u9fa5]{2,4})")


def _mk_mapper(mapping):
    counters = {}
    for k in mapping:                       # 从既有映射恢复计数，避免跨文件代号冲突
        kind = k.split("\x00", 1)[0]
        counters[kind] = counters.get(kind, 0) + 1

    def repl(kind, value):
        key = f"{kind}\u0000{value}"
        if key not in mapping:
            counters[kind] = counters.get(kind, 0) + 1
            mapping[key] = f"【{kind}-{counters[kind]:03d}】"
        return mapping[key]
    return repl


def deid_text(text, mapping, names=None):
    repl = _mk_mapper(mapping)
    for kind, pat in PATTERNS:
        text = pat.sub(lambda m: repl(kind, m.group(0)), text)
    # 全局替换已收集姓名（含无上下文的同名出现）
    for nm in (names or []):
        if nm and nm in text:
            text = text.replace(nm, repl("PERSON", nm))
    return text


def collect_names(texts):
    names = set()
    for t in texts:
        for m in NAME_CTX.finditer(t):
            names.add(m.group(1))
    return sorted(names, key=len, reverse=True)


def main():
    os.makedirs(DEID, exist_ok=True)
    os.makedirs(os.path.dirname(MAP), exist_ok=True)
    files = sorted(f for f in os.listdir(RAW) if f.endswith(".txt"))
    raws = {fn: open(os.path.join(RAW, fn), encoding="utf-8", errors="replace").read() for fn in files}
    names = collect_names(raws.values())
    mapping = {}
    for fn in files:
        open(os.path.join(DEID, fn), "w", encoding="utf-8").write(deid_text(raws[fn], mapping, names))
    json.dump(mapping, open(MAP, "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"raw_txt": len(files), "deid_dir": DEID, "mapping": MAP,
                      "names_collected": len(names), "mapping_entries": len(mapping)},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
