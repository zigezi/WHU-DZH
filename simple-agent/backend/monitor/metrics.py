from typing import Dict, Any
from .trace_store import trace_store


class MetricsAggregator:
    # ------------------------------------------------------------------ #
    def get_global_metrics(self) -> Dict[str, Any]:
        traces = trace_store.list_traces(limit=1000)
        if not traces:
            return {
                "total": 0, "success": 0, "failed": 0, "running": 0,
                "success_rate": 0, "avg_duration_ms": 0, "avg_tokens": 0,
                "total_tool_calls": 0,
            }

        success = len([t for t in traces if t.status == "success"])
        failed = len([t for t in traces if t.status == "failed"])
        running = len([t for t in traces if t.status == "running"])

        completed = [t for t in traces if t.status in ("success", "failed")]
        avg_duration = (
            sum([(t.end_time - t.start_time) * 1000 for t in completed
                 if t.end_time is not None]) / len(completed)
            if completed else 0
        )
        avg_tokens = (
            sum([t.total_tokens or 0 for t in completed]) / len(completed)
            if completed else 0
        )
        total_tool_calls = sum([t.total_tool_calls or 0 for t in traces])

        return {
            "total": len(traces),
            "success": success,
            "failed": failed,
            "running": running,
            "success_rate": round(success / len(completed), 4) if completed else 0,
            "avg_duration_ms": round(avg_duration, 2),
            "avg_tokens": round(avg_tokens, 2),
            "total_tool_calls": total_tool_calls,
        }

    # ------------------------------------------------------------------ #
    def get_layer_metrics(self) -> Dict[str, Any]:
        """按 ETCLOVG 分层聚合指标"""
        traces = trace_store.list_traces(limit=1000)
        layer_stats: Dict[str, Dict[str, Any]] = {}

        for trace in traces:
            for span in trace.spans:
                layer = span.layer
                if layer not in layer_stats:
                    layer_stats[layer] = {
                        "total": 0, "success": 0, "failed": 0,
                        "total_duration_ms": 0,
                    }
                layer_stats[layer]["total"] += 1
                if span.status == "failed":
                    layer_stats[layer]["failed"] += 1
                else:
                    layer_stats[layer]["success"] += 1
                layer_stats[layer]["total_duration_ms"] += span.duration_ms or 0

        for stats in layer_stats.values():
            total = stats["total"]
            stats["success_rate"] = round(stats["success"] / total, 4) if total else 0
            stats["avg_duration_ms"] = round(stats["total_duration_ms"] / total, 2) if total else 0
        return layer_stats

    # ------------------------------------------------------------------ #
    def get_tool_metrics(self) -> Dict[str, Any]:
        """按工具维度聚合（使用真实工具名，而非固定的 span 名称）"""
        traces = trace_store.list_traces(limit=1000)
        tool_stats: Dict[str, Dict[str, Any]] = {}

        for trace in traces:
            for span in trace.spans:
                if span.type != "tool_call":
                    continue
                tool_name = (span.attributes or {}).get("tool") or span.name
                if tool_name not in tool_stats:
                    tool_stats[tool_name] = {
                        "total": 0, "success": 0, "failed": 0,
                        "total_duration_ms": 0,
                    }
                tool_stats[tool_name]["total"] += 1
                if span.status == "failed":
                    tool_stats[tool_name]["failed"] += 1
                else:
                    tool_stats[tool_name]["success"] += 1
                tool_stats[tool_name]["total_duration_ms"] += span.duration_ms or 0

        for stats in tool_stats.values():
            total = stats["total"]
            stats["success_rate"] = round(stats["success"] / total, 4) if total else 0
            stats["avg_duration_ms"] = round(stats["total_duration_ms"] / total, 2) if total else 0
        return tool_stats


metrics_aggregator = MetricsAggregator()
