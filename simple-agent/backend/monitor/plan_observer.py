"""规划面观测（B 段）：记录规划器产出 plan 的结构化摘要。

规划器尚未落地，先固定 schema；规划器接入后自动出数。
plan_json 结构约定：
    {"nodes": [{"id": "n1", "agent": "coder", "deps": [], "owns": ["a.txt"]}]}
"""
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .collector import add_event
from .trace_store import trace_store

REPORT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    ".agent", "reports",
)


def _nodes_of(plan_json: Any) -> List[dict]:
    if isinstance(plan_json, dict):
        return list(plan_json.get("nodes") or [])
    if isinstance(plan_json, list):
        return list(plan_json)
    return []


def _schema_valid(nodes: List[dict]) -> bool:
    ids = [n.get("id") for n in nodes]
    if any(not i for i in ids) or len(ids) != len(set(ids)):
        return False
    idset = set(ids)
    adj = {n["id"]: [] for n in nodes}
    for n in nodes:
        if not n.get("agent"):
            return False
        for dep in n.get("deps", []) or []:
            if dep not in idset:
                return False
            adj[dep].append(n["id"])

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {i: WHITE for i in ids}

    def dfs(u: str) -> bool:
        color[u] = GRAY
        for v in adj[u]:
            if color[v] == GRAY:
                return False
            if color[v] == WHITE and not dfs(v):
                return False
        color[u] = BLACK
        return True

    return all(dfs(i) for i in ids if color[i] == WHITE)


def _max_depth(nodes: List[dict]) -> int:
    by_id = {n["id"]: n for n in nodes if n.get("id")}
    depth: Dict[str, int] = {}

    def d(nid: str, stack: set) -> int:
        if nid in depth:
            return depth[nid]
        if nid in stack:
            return 0
        node = by_id.get(nid, {})
        deps = [x for x in (node.get("deps", []) or []) if x in by_id]
        value = 1 + max([d(x, stack | {nid}) for x in deps], default=0)
        depth[nid] = value
        return value

    return max([d(i, set()) for i in by_id], default=0)


def _owns_disjoint(nodes: List[dict]) -> bool:
    seen = {}
    for n in nodes:
        for path in (n.get("owns", []) or []):
            if path in seen:
                return False
            seen[path] = n.get("id")
    return True


def record_plan(trace_id: str, req_id: Optional[str], plan_json: Any,
                planner_model: str, prompt_version: str, usage: Any = None,
                latency_ms: float = 0,
                parent_span_id: Optional[str] = None):
    nodes = _nodes_of(plan_json)
    if isinstance(usage, dict):
        tokens = usage.get("total_tokens", 0)
    else:
        tokens = getattr(usage, "total_tokens", 0) or 0
    plan_id = str(uuid.uuid4())
    attrs = {
        "plan_id": plan_id,
        "req_id": req_id,
        "planner_model": planner_model,
        "prompt_version": prompt_version,
        "tokens": tokens,
        "latency_ms": latency_ms,
        "node_count": len(nodes),
        "max_depth": _max_depth(nodes),
        "schema_valid": _schema_valid(nodes),
        "owns_disjoint": _owns_disjoint(nodes),
        "deps": {n.get("id"): list(n.get("deps", []) or []) for n in nodes if n.get("id")},
        "owns": {n.get("id"): list(n.get("owns", []) or []) for n in nodes if n.get("id")},
    }
    add_event(trace_id=trace_id, name="规划", layer="L", span_type="plan",
              parent_span_id=parent_span_id, attributes=attrs)
    return plan_id, attrs


# ---------------------------------------------------------------------- #
# C 段：切分质量打分（用 A/B 数据算出来的派生指标）
# ---------------------------------------------------------------------- #
def _cv(values: List[float]) -> float:
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return 0.0
    mean = sum(vals) / len(vals)
    if mean == 0:
        return 0.0
    var = sum((v - mean) ** 2 for v in vals) / len(vals)
    return (var ** 0.5) / mean


def _find_plan_span(plan_id: str):
    for span in trace_store.find_spans_by_type("plan", limit=10000):
        if (span.attributes or {}).get("plan_id") == plan_id:
            return span
    return None


def _latest_plan_span(trace_id: str):
    for span in trace_store.find_spans_by_type("plan", limit=10000):
        if span.trace_id == trace_id:
            return span
    return None


def _ancestors(node_id: str, deps: Dict[str, List[str]]) -> set:
    seen, stack = set(), [node_id]
    while stack:
        cur = stack.pop()
        for dep in deps.get(cur, []) or []:
            if dep not in seen:
                seen.add(dep)
                stack.append(dep)
    return seen


def _independent(a: str, b: str, deps: Dict[str, List[str]]) -> bool:
    return (b not in _ancestors(a, deps)) and (a not in _ancestors(b, deps))


def decomposition_report(trace_id: str, write_span: bool = True) -> Optional[dict]:
    plan_span = _latest_plan_span(trace_id)
    if not plan_span:
        return None
    attrs = plan_span.attributes or {}
    deps = attrs.get("deps") or {}
    spans = trace_store.get_spans_by_trace(trace_id)
    exec_spans = [s for s in spans if (s.attributes or {}).get("plan_node_id")]

    by_node: Dict[str, List] = {}
    for s in exec_spans:
        by_node.setdefault(s.attributes["plan_node_id"], []).append(s)

    # owns_conflicts：**无依赖关系**的节点对之间 effect_diff 的文件交集。
    # 线性链所有节点对都有上下游依赖 → 恒 0（这才是"恒为 0"成立的前提）。
    node_files: Dict[str, set] = {}
    for nid, ss in by_node.items():
        files = set()
        for s in ss:
            effect = (s.attributes or {}).get("effect_diff") or {}
            for key in ("created", "modified", "deleted"):
                files.update(effect.get(key, []))
        node_files[nid] = files
    file_to_nodes: Dict[str, set] = {}
    for nid, files in node_files.items():
        for f in files:
            file_to_nodes.setdefault(f, set()).add(nid)
    owns_conflicts = 0
    for _f, touching in file_to_nodes.items():
        nodes_list = sorted(touching)
        conflict = False
        for i in range(len(nodes_list)):
            for j in range(i + 1, len(nodes_list)):
                if _independent(nodes_list[i], nodes_list[j], deps):
                    conflict = True
                    break
            if conflict:
                break
        if conflict:
            owns_conflicts += 1

    # 节点成功率
    if by_node:
        ok = sum(1 for ss in by_node.values()
                 if not any(s.status == "failed" for s in ss))
        node_success_rate = ok / len(by_node)
    else:
        node_success_rate = 0.0

    # 平均重试（以 E 层执行次数 - 1 估算）
    exec_counts = [len([s for s in ss if s.type == "sandbox_exec"])
                   for ss in by_node.values()]
    avg_retries = (sum(max(c - 1, 0) for c in exec_counts) / len(exec_counts)
                   if exec_counts else 0.0)

    # rework_edges：feedback_injected 触发后同一 plan 节点再次出现 E span（同节点重入）。
    # 故意失败任务（如 REQ-004）必然非 0——真实信号。
    rework_edges = 0
    for fb in spans:
        if fb.type != "feedback_injected":
            continue
        parent = trace_store.get_span(fb.parent_span_id) if fb.parent_span_id else None
        nid = (parent.attributes or {}).get("plan_node_id") if parent else None
        if not nid:
            continue
        if any((s.attributes or {}).get("plan_node_id") == nid
               and (s.start_time or 0) > (fb.start_time or 0) for s in exec_spans):
            rework_edges += 1

    # token 变异系数（各节点 LLM token 的 CV；无则用 span 数）
    per_node_tokens = [
        sum((s.attributes or {}).get("total_tokens") or 0
            for s in ss if s.type == "llm_call")
        for ss in by_node.values()
    ]
    if not any(per_node_tokens):
        per_node_tokens = [len(ss) for ss in by_node.values()]
    token_cv = _cv([float(x) for x in per_node_tokens])

    # 重规划次数：同一 trace 内相同 req_id 的 plan 数 - 1
    same_req = [s for s in spans if s.type == "plan"
                and (s.attributes or {}).get("req_id") == attrs.get("req_id")]
    replan_count = max(len(same_req) - 1, 0)

    report = {
        "trace_id": trace_id,
        "plan_id": attrs.get("plan_id"),
        "req_id": attrs.get("req_id"),
        "node_success_rate": round(node_success_rate, 4),
        "avg_retries": round(avg_retries, 4),
        "rework_edges": rework_edges,
        "owns_conflicts": owns_conflicts,
        "token_cv": round(token_cv, 4),
        "critical_path": attrs.get("max_depth", 0),
        "replan_count": replan_count,
    }
    if write_span:
        add_event(trace_id=trace_id, name="切分质量评估", layer="O",
                  span_type="decomposition_eval", attributes=report)
    return report


def planning_health() -> Dict[str, Any]:
    plans = trace_store.find_spans_by_type("plan", limit=10000)
    if not plans:
        return {"plan_schema_valid_rate": 0.0, "avg_node_count": 0.0,
                "plan_count": 0}
    valid = sum(1 for s in plans if (s.attributes or {}).get("schema_valid"))
    node_counts = [(s.attributes or {}).get("node_count") or 0 for s in plans]
    return {
        "plan_schema_valid_rate": round(valid / len(plans), 4),
        "avg_node_count": round(sum(node_counts) / len(plans), 2),
        "plan_count": len(plans),
    }


def decomposition_health() -> Dict[str, Any]:
    plans = trace_store.find_spans_by_type("plan", limit=1000)
    reports = []
    for span in plans:
        pid = (span.attributes or {}).get("plan_id")
        if not pid:
            continue
        report = decomposition_report(span.trace_id, write_span=False)
        if report:
            reports.append((span, report))
    if not reports:
        return {"owns_conflict_rate": 0.0, "rework_edge_rate": 0.0,
                "planner_leaderboard": []}

    conflict_rate = sum(1 for _, r in reports if r["owns_conflicts"] > 0) / len(reports)
    rework_rate = sum(r["rework_edges"] for _, r in reports) / len(reports)

    leaderboard: Dict[tuple, dict] = {}
    for span, report in reports:
        attrs = span.attributes or {}
        key = (attrs.get("planner_model"), attrs.get("prompt_version"))
        entry = leaderboard.setdefault(key, {"n": 0, "success": 0.0, "conflicts": 0})
        entry["n"] += 1
        entry["success"] += report["node_success_rate"]
        entry["conflicts"] += report["owns_conflicts"]

    lb = [
        {
            "planner_model": k[0], "prompt_version": k[1], "n": v["n"],
            "avg_node_success_rate": round(v["success"] / v["n"], 4),
            "total_conflicts": v["conflicts"],
        }
        for k, v in leaderboard.items()
    ]
    lb.sort(key=lambda x: x["avg_node_success_rate"], reverse=True)
    return {
        "owns_conflict_rate": round(conflict_rate, 4),
        "rework_edge_rate": round(rework_rate, 4),
        "planner_leaderboard": lb,
    }


def write_decomposition_report(trace_id: str) -> Optional[str]:
    """C 段产物写盘者（v2.2 §5.0.2）：生成/追加 .agent/reports/decomposition-report.md。"""
    report = decomposition_report(trace_id, write_span=False)
    if not report:
        return None
    health = decomposition_health()
    os.makedirs(REPORT_DIR, exist_ok=True)
    path = os.path.join(REPORT_DIR, "decomposition-report.md")

    lines = [
        "# 切分质量报告（decomposition-report）",
        "",
        f"- 生成时间：{datetime.now().isoformat()}",
        f"- 最近 trace：{trace_id}",
        "",
        "## 最近一次切分",
        "",
        "| metric | value |",
        "|---|---|",
    ]
    for key in ("plan_id", "req_id", "node_success_rate", "avg_retries",
                "rework_edges", "owns_conflicts", "token_cv",
                "critical_path", "replan_count"):
        lines.append(f"| {key} | {report.get(key)} |")
    lines += [
        "",
        "## planner 排行表",
        "",
        "| planner_model | prompt_version | n | avg_node_success_rate | total_conflicts |",
        "|---|---|---|---|---|",
    ]
    for row in health.get("planner_leaderboard", []):
        lines.append(
            f"| {row['planner_model']} | {row['prompt_version']} | {row['n']} | "
            f"{row['avg_node_success_rate']} | {row['total_conflicts']} |"
        )
    lines += [
        "",
        f"- owns_conflict_rate: {health.get('owns_conflict_rate')}",
        f"- rework_edge_rate: {health.get('rework_edge_rate')}",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path
