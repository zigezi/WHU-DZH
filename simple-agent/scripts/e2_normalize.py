#!/usr/bin/env python3
"""P5a.100 §二：quote 证据定位的**空白归一化**（参数级锚定；并入 eval_fingerprint）。

规格（可审计）：
- 全角→半角：全角空格 U+3000 → ASCII 空格；全角 ASCII（U+FF01–FF5E）→ 半角；
- 空白折叠：ASCII 空格 / 制表符 / 换行 / 全角空格 → 单个空格；
- 串首尾修剪；
- 仅用于**证据定位**（quote 是否能在原文找到），**永不用于结论判定**（a100 §二.3）。
"""
import re
import unicodedata

SPEC = {
    "fullwidth_to_halfwidth": "U+FF01–FF5E -> ASCII; U+3000 -> space",
    "whitespace_fold": "space/tab/newline/fullwidth-space -> single ' '",
    "trim": "strip leading/trailing",
    "scope": "evidence-location only; never conclusion",
}


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.replace("\u3000", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def locate_quote(doc: str, quote: str) -> bool:
    if not quote:
        return False
    return normalize(quote) in normalize(doc)
