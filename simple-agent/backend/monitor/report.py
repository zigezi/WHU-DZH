from datetime import datetime
from typing import Dict, Any, List
from .metrics import metrics_aggregator
from .trace_store import trace_store
from .diagnosis import shapley_diagnosis
from .anomaly import anomaly_detector


class ReportGenerator:
    def generate_full_report(self) -> Dict[str, Any]:
        """生成完整监控诊断报告"""
        global_metrics = metrics_aggregator.get_global_metrics()
        layer_metrics = metrics_aggregator.get_layer_metrics()
        tool_metrics = metrics_aggregator.get_tool_metrics()

        # 诊断「所有存在问题」的任务：失败、有失败 span、或命中异常规则
        problem_traces = self._collect_problem_traces()
        problem_diagnosis = []
        for trace in problem_traces:
            diagnosis = shapley_diagnosis.get_root_cause(trace)
            problem_diagnosis.append({
                "trace_id": trace.trace_id,
                "status": trace.status,
                "task_content": (trace.task_content or "")[:80],
                "diagnosis": diagnosis,
            })

        # 整体瓶颈：成功率最低的层级
        bottleneck = None
        if layer_metrics:
            layer, stats = min(
                layer_metrics.items(),
                key=lambda x: x[1].get("success_rate", 1),
            )
            bottleneck = {
                "layer": layer,
                "success_rate": stats.get("success_rate", 0),
            }

        return {
            "report_time": datetime.now().isoformat(),
            "global_metrics": global_metrics,
            "layer_metrics": layer_metrics,
            "tool_metrics": tool_metrics,
            "system_bottleneck": bottleneck,
            "problem_tasks_diagnosis": problem_diagnosis,
            "failed_tasks_diagnosis": problem_diagnosis,  # 向后兼容旧字段名
            "anomaly_summary": self._anomaly_summary(problem_diagnosis),
            "shapley_summary": self._shapley_summary(problem_diagnosis),
        }

    # ------------------------------------------------------------------ #
    def _collect_problem_traces(self, limit: int = 50) -> List:
        result = []
        for trace in trace_store.list_traces(limit=limit):
            if trace.status == "running":
                continue
            has_failed_span = any(s.status == "failed" for s in trace.spans)
            if trace.status == "failed" or has_failed_span or anomaly_detector.detect(trace):
                result.append(trace)
        return result

    def _anomaly_summary(self, problem_diagnosis: list) -> Dict[str, int]:
        """统计各类异常出现的次数"""
        summary: Dict[str, int] = {}
        for item in problem_diagnosis:
            for anomaly in item["diagnosis"]["anomalies"]:
                key = f'{anomaly["rule_id"]} {anomaly["name"]}'
                summary[key] = summary.get(key, 0) + 1
        return dict(sorted(summary.items(), key=lambda x: x[1], reverse=True))

    def _shapley_summary(self, problem_diagnosis: list) -> Dict[str, float]:
        """统计所有问题任务的平均 Shapley 贡献分布"""
        if not problem_diagnosis:
            return {}
        layer_sum: Dict[str, float] = {}
        for item in problem_diagnosis:
            for layer, value in item["diagnosis"]["shapley_values"].items():
                layer_sum[layer] = layer_sum.get(layer, 0) + value
        count = len(problem_diagnosis)
        return {layer: round(value / count, 2) for layer, value in layer_sum.items()}


report_generator = ReportGenerator()
