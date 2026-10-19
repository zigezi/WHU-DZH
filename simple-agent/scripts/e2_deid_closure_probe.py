#!/usr/bin/env python3
"""E2 变体闭包探针（P5a.96 条款三）：扫已入表实体的变体残留。

量程声明（必含，a96 A3）：**本探针只管"已入表实体的变体残留"；未入表实体的发现不在本量程，
由召回 fixture + 人工锚覆盖。** 变体仅从映射表实体生成（禁全局形近扫描）。
  /root/miniconda3/envs/mini-agent/bin/python scripts/e2_deid_closure_probe.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import e2_deident as D  # noqa: E402

DEID = "/root/e2-corpus/deid"
MAP = os.path.join(ROOT, ".agent", "local", "e2-deid-mapping.json")
R = os.path.join(ROOT, ".agent", "reports")


def variants(value, kind):
    v = set()
    v.add(value)
    v.add(re.sub(r"\s+", "", value))                       # 断行折叠
    if kind == "COMPANY":
        for c in D._company_cores(value):
            v.add(c)
    return {x for x in v if len(x) >= 2}


def main():
    if not os.path.exists(MAP):
        print(json.dumps({"error": "no mapping"})); return 2
    m = json.load(open(MAP, encoding="utf-8"))
    entities = [(k.split("\x00", 1)[0], k.split("\x00", 1)[1]) for k in m]
    deid = {}
    for fn in os.listdir(DEID):
        if fn.endswith(".txt") and fn != "STATUS":
            deid[fn] = open(os.path.join(DEID, fn), encoding="utf-8", errors="replace").read()
    residual = []
    for kind, val in entities:
        for var in variants(val, kind):
            if var == "unknown":
                continue
            for fn, t in deid.items():
                hit = (var in t) or (any(ch.isascii() and ch.isalpha() for ch in var) and var.lower() in t.lower())
                if hit:
                    residual.append({"entity": val, "kind": kind, "variant": var, "file": fn})
                    break
    # a101 §四.3：代号紧邻中文字符且该字符属映射表人名 → 半遮蔽残留报警
    for kind, val in entities:
        if kind != "PERSON" or len(val) < 2 or D._name_clean(val) is None:
            continue
        chars = {val[-1]}
        for fn, t in deid.items():
            for m in re.finditer(r"([\u4e00-\u9fa5])【[A-Z]+-\d+】|【[A-Z]+-\d+】([\u4e00-\u9fa5])", t):
                ch = m.group(1) or m.group(2)
                if ch in chars:
                    residual.append({"entity": val, "kind": "adjacent_residue", "char": ch, "file": fn})

    out = {"note": "E2 变体闭包探针（a96 条款三 + a101 §四.3 残留校验）",
           "entities": len(entities), "residual": residual[:50], "residual_count": len(residual),
           "closure_clean": not residual,
           "coverage_declaration": "闭包残留 {}（量程：已入表实体之变体[全称/折叠/短名/大小写折叠]；"
                                   "**不覆盖**：未入表实体、引用块英文作者、域尾/电话碎片、表内嵌入——"
                                   "由 fixture + 人工锚覆盖）".format(len(residual))}
    json.dump(out, open(os.path.join(R, "e2-deid-closure-probe.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"entities": len(entities), "residual_count": len(residual),
                      "closure_clean": out["closure_clean"], "sample": residual[:15]},
                     ensure_ascii=False, indent=1))
    return 0 if out["closure_clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
