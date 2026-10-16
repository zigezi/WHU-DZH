#!/usr/bin/env python3
"""任务族复发率统计（P0.5 决策点）。

读 trace.db 的全部 task_content，用「分词 → Top10 关键词排序 → md5」生成
任务签名并聚类，输出各族计数与占比到 .agent/reports/family-stats.md。

决策规则：Top 族占比 > 50% → P3 的编译固化全量做；否则 P3 只做路由表，编译留桩。
"""
import hashlib
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "backend", "logs", "trace.db")
REPORT_DIR = os.path.join(ROOT, ".agent", "reports")
REPORT_PATH = os.path.join(REPORT_DIR, "family-stats.md")

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with",
    "is", "are", "be", "this", "that", "it", "as", "by", "at", "from",
    "please", "then", "use", "using", "into", "create", "make",
    "的", "了", "和", "与", "在", "把", "给", "一个", "并且", "然后",
    "请", "将", "到", "中", "里", "为", "是", "对",
}


def tokenize(text: str):
    text = (text or "").lower()
    ascii_words = re.findall(r"[a-z0-9_]+", text)
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", text)
    return [t for t in (ascii_words + cjk_chars) if t not in STOPWORDS]


def sign(text: str) -> str:
    """简化版签名：Top10 关键词排序拼接后取 md5 前 12 位。"""
    tokens = tokenize(text)
    if not tokens:
        return "empty"
    counts = Counter(tokens)
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    key = "|".join(word for word, _ in sorted(top))
    return hashlib.md5(key.encode("utf-8")).hexdigest()[:12]


def load_task_contents():
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT task_content FROM traces WHERE task_content IS NOT NULL"
        ).fetchall()
        return [r[0] for r in rows]
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def main():
    contents = load_task_contents()
    families = defaultdict(list)
    for content in contents:
        families[sign(content)].append(content)

    total = len(contents)
    ranked = sorted(families.items(), key=lambda kv: len(kv[1]), reverse=True)

    os.makedirs(REPORT_DIR, exist_ok=True)
    lines = [
        "# 任务族复发率统计",
        "",
        f"- 总任务数：{total}",
        f"- 任务族数：{len(ranked)}",
        "",
        "| 排名 | 签名 | 数量 | 占比 | 代表任务 |",
        "|---|---|---|---|---|",
    ]
    for idx, (sig, items) in enumerate(ranked, 1):
        ratio = len(items) / total if total else 0
        sample = (items[0] or "").replace("\n", " ")[:60]
        lines.append(
            f"| {idx} | {sig} | {len(items)} | {ratio:.1%} | {sample} |"
        )

    top_ratio = (len(ranked[0][1]) / total) if ranked and total else 0
    lines += ["", "## 决策结论", ""]
    if total == 0:
        conclusion = "无历史任务数据，P3 仅做路由表，编译留桩。"
    elif top_ratio > 0.5:
        conclusion = (
            f"Top 族占比 {top_ratio:.1%} > 50% → **P3 的编译固化全量做**。"
        )
    else:
        conclusion = (
            f"Top 族占比 {top_ratio:.1%} ≤ 50% → **P3 只做路由表，编译留桩**。"
        )
    lines.append(conclusion)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"[family_stats] total={total} families={len(ranked)} top_ratio={top_ratio:.1%}")
    print(f"[family_stats] report -> {REPORT_PATH}")
    print(conclusion)
    return 0


if __name__ == "__main__":
    sys.exit(main())
