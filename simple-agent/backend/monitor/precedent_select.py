"""P5a.20 便签 3：测量模式 precedent 选择器（纯函数）。

修复 P5a.19 工单 1/3 发现的缺陷：原选择器因占位 content 相似度恒 1.0 + `ORDER BY id DESC`
而**恒取最新**（=上一任务）。新规则：
  1. 仅同族（sig 精确相等）；
  2. 仅先前 epoch（由调用方按 cutoff / 快照过滤后传入）；
  3. 确定性 tie-break：id 最小（最早沉积）；
  4. 无同族 → 不注入（返回 None）。
"""
import hashlib
import json
from typing import List, Optional


def select(candidates: List[dict], sig_family: str) -> Optional[dict]:
    same = [p for p in candidates if p.get("sig") == sig_family]
    if not same:
        return None
    return min(same, key=lambda p: p.get("id", 0))


def content_hash(plan) -> str:
    return hashlib.sha256(
        json.dumps(plan, ensure_ascii=False, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]


def summary_of(plan, cap: int = 2000) -> str:
    return json.dumps(plan, ensure_ascii=False)[:cap]
