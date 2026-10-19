#!/usr/bin/env python3
"""P5a.101 §四.1：字符级全量断言（raw↔deid 逐字可解释；水印带外删除=0）。

- removed = Counter(raw) - Counter(deid)：每个被删字符须能由映射表**条目值**解释；
- added = Counter(deid) - Counter(raw)：新增字符须为代号字面（【】A-Z 0-9 -）；
- 水印类字符删除计数必须为 0（a101 §四.5 回炉期挂起）。
  /root/miniconda3/envs/mini-agent/bin/python scripts/e2_deid_char_assert.py
"""
import json
import os
import re
import string
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = "/root/e2-corpus/raw"
DEID = "/root/e2-corpus/deid"
MAP = os.path.join(ROOT, ".agent", "local", "e2-deid-mapping.json")
WM = os.path.join(ROOT, ".agent", "local", "e2-watermark.json")
R = os.path.join(ROOT, ".agent", "reports")

CODE_CHARS = set("【】-0123456789") | set(string.ascii_uppercase)


def main():
    mp = json.load(open(MAP, encoding="utf-8"))
    vals = [k.split("\x00", 1)[1] for k in mp]
    allowed_removed = set("".join(vals))
    wm = set(json.load(open(WM, encoding="utf-8"))["watermark_chars"]) if os.path.exists(WM) else set()
    REF_ALLOW = os.path.join(ROOT, ".agent", "local", "e2-refs-allowance.json")
    ref_chars = set(json.load(open(REF_ALLOW, encoding="utf-8"))) if os.path.exists(REF_ALLOW) else set()
    allowed_removed |= ref_chars          # REF 整块遮蔽的字符由 REF 允差解释

    docs = []
    total_unexplained = 0
    for fn in sorted(f for f in os.listdir(RAW) if f.endswith(".txt")):
        raw = open(os.path.join(RAW, fn), encoding="utf-8", errors="replace").read()
        dd = os.path.join(DEID, fn)
        deid = open(dd, encoding="utf-8", errors="replace").read() if os.path.exists(dd) else ""
        r, d = Counter(raw), Counter(deid)
        removed, added = r - d, d - r
        unexp_r = {ch: n for ch, n in removed.items() if not ch.isspace() and ch not in allowed_removed}
        unexp_a = {ch: n for ch, n in added.items() if not ch.isspace() and ch not in CODE_CHARS}
        wm_del = {c: removed.get(c, 0) for c in wm if removed.get(c, 0) > 0 and c not in allowed_removed}
        ok = not unexp_r and not unexp_a and not wm_del
        total_unexplained += len(unexp_r) + len(unexp_a) + len(wm_del)
        docs.append({"doc": fn, "removed_chars": sum(removed.values()), "added_chars": sum(added.values()),
                     "unexplained_removed": unexp_r, "unexplained_added": unexp_a,
                     "watermark_deleted": wm_del, "pass": ok})
    out = {"note": "P5a.101 §四.1 字符级全量断言（水印删除挂起期）",
           "watermark": sorted(wm), "docs": docs, "all_pass": total_unexplained == 0,
           "coverage": "逐字多重集：removed 须由映射条目值解释；added 须为代号字面；水印删除须为 0"}
    json.dump(out, open(os.path.join(R, "e2-deid-char-assert.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"all_pass": out["all_pass"],
                      "fails": [d for d in docs if not d["pass"]][:5]}, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
