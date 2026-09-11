"""任务签名器（P3.1）。

不引入 embedding 依赖：分词（正则）→ 去停用词 → Top10 关键词排序拼接 → md5 前 12 位；
similarity 用关键词集合的 Jaccard。接口预留，后续可替换为向量相似度。
"""
import hashlib
import re
from collections import Counter
from typing import List

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with",
    "is", "are", "be", "this", "that", "it", "as", "by", "at", "from",
    "please", "then", "use", "using", "into",
    "的", "了", "和", "与", "在", "把", "给", "一个", "并且", "然后",
    "请", "将", "到", "中", "里", "为", "是", "对",
}


def tokens(text: str) -> List[str]:
    text = (text or "").lower()
    ascii_words = re.findall(r"[a-z0-9_]+", text)
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", text)
    return [t for t in (ascii_words + cjk_chars) if t not in STOPWORDS]


def keywords(text: str, k: int = 10) -> List[str]:
    counts = Counter(tokens(text))
    if not counts:
        return []
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:k]
    return sorted(word for word, _ in top)


def sign(text: str) -> str:
    kws = keywords(text)
    if not kws:
        return "empty"
    return hashlib.md5("|".join(kws).encode("utf-8")).hexdigest()[:12]


def similarity(a: str, b: str) -> float:
    sa, sb = set(keywords(a)), set(keywords(b))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)
