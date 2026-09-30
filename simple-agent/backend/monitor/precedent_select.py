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


def plan_types(plan) -> list:
    return [s.get("tool") for s in (plan or []) if isinstance(s, dict)]


def _jaccard(a, b) -> float:
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if (a or b) else 0.0


def select_for_arm(candidates, task_req, task_sig, task_env, arm, rng, used,
                   k: int = 3, fam_types=None, near: float = 0.6,
                   ref_len: int = None, ref_types=None):
    """P5a.30/31/33：三臂臂内选择器。

    candidates: [{"req_id","sig","domain","plan","hash"}]
    used: {hash: count}（k=3 上限，臂内共享）
    fam_types: {(domain,sig): [tool,...]} 用于"同域近族"Jaccard
    返回 (chosen_or_None, reason)。
    """
    fam_types = fam_types or {}

    def avail(c):
        return used.get(c["hash"], 0) < k

    if arm == "direct":
        return None, "direct"

    if arm == "sibling":
        pool = [c for c in candidates if c["req_id"] != task_req
                and c["domain"] == task_env and c["sig"] == task_sig and avail(c)]
        if pool:
            return rng.choice(pool), "same_family"
        ts = set(fam_types.get((task_env, task_sig), []))
        pool = [c for c in candidates if c["req_id"] != task_req
                and c["domain"] == task_env and c["sig"] != task_sig and avail(c)
                and _jaccard(ts, set(fam_types.get((task_env, c["sig"]), []))) >= near]
        if pool:
            return rng.choice(pool), "near_family"
        return None, "ineligible"

    if arm == "unrelated":
        # 形态匹配：优先异域；按 (长度差, 类型不匹配) 选最近邻
        pool = [c for c in candidates if c["domain"] != task_env and avail(c)]
        if not pool:
            pool = [c for c in candidates if c["domain"] == task_env
                    and c["sig"] != task_sig and avail(c)]
        if not pool:
            pool = [c for c in candidates if avail(c)]
        if not pool:
            return None, "ineligible"
        rt = set(ref_types or [])

        def score(c):
            ln = len(c["plan"] or [])
            ldiff = abs(ln - (ref_len if ref_len else ln))
            tover = _jaccard(rt, set(plan_types(c["plan"]))) if rt else 0.0
            return (ldiff, -tover)

        return min(pool, key=score), ("form_matched" if ref_len else "cross_domain")

    return None, "unknown_arm"


def content_hash(plan) -> str:
    return hashlib.sha256(
        json.dumps(plan, ensure_ascii=False, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]


def summary_of(plan, cap: int = 2000) -> str:
    return json.dumps(plan, ensure_ascii=False)[:cap]
