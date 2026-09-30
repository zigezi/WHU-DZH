"""P5a.30 §二.2 / P5a.33 §三：CopyGuard 审计版（全参数扫描）。

判据：注入物实体值出现在 agent 的**工具调用参数**，且该值**未在本 run 先前工具结果中出现**
（先前工具结果豁免 = 合法重演）。
- 只做审计，**永不改写结局**（τ 奖励函数不动）；
- 伪真值注入物下预期命中 = 0（命中 = 脱敏 lint 失效信号）；
- e7 真值注入物回放：命中 = 抄答案证据。
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitor.trace_store import trace_store  # noqa: E402
from requirements.adapters.tau.deident import (  # noqa: E402
    _RE_ORDER, _RE_PAY, _RE_FLT, _RE_USER, _RE_RES, _RE_DATE, _collect_strings,
)

_PATTERNS = (_RE_ORDER, _RE_PAY, _RE_FLT, _RE_USER, _RE_RES, _RE_DATE)


def _norm(v):
    return str(v).strip().lstrip("#").lower()


def entity_values(obj):
    """从任意结构/文本中抽取实体值（含自由文本嵌入）。"""
    vals = set()
    for s in _collect_strings(obj):
        for p in _PATTERNS:
            vals |= set(p.findall(s))
    return vals


def scan_trace(trace_id, watch):
    """返回 hits: [{span_id, value}]（值在 args 且未经先前工具结果）。"""
    watch_n = {_norm(v) for v in watch if v}
    spans = sorted(trace_store.get_spans_by_trace(trace_id),
                   key=lambda s: getattr(s, "start_time", 0) or 0)
    seen = set()
    hits = []
    for sp in spans:
        a = sp.attributes or {}
        if sp.type == "tool_call":
            args = a.get("args") or {}
            for v in _collect_strings(args):
                n = _norm(v)
                if n in watch_n and n not in seen:
                    hits.append({"span_id": sp.span_id, "value": v})
            seen |= {_norm(v) for v in entity_values(a.get("output") or "")}
        elif sp.type == "sandbox_exec":
            seen |= {_norm(v) for v in entity_values(a.get("output") or "")}
        elif sp.type == "dialogue_turn":
            # 工具结果也可能经对话文本回传
            seen |= {_norm(v) for v in entity_values(a.get("text") or "")}
    return hits
