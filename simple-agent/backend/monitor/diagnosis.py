from typing import Dict, Any, List
from .schema import Trace
from .anomaly import anomaly_detector


class ShapleyDiagnosis:
    """
    基于边际贡献的简化 Shapley 根因定位。

    思想：对每个层级，计算「移除该层 span 后故障严重程度的下降幅度」，
    下降越多说明该层对本次故障的贡献越大；再叠加异常规则的直接命中，
    归一化后得到各层贡献百分比。

    与旧实现的区别：不再要求 trace.status == "failed"，因此 agent 虽然
    最终返回 success、但过程中工具失败/超时的情况同样能被诊断。
    """

    def __init__(self):
        self.layers = ["E", "T", "C", "L", "O", "V", "G"]
        self.layer_names = {
            "E": "执行沙箱层",
            "T": "工具协议层",
            "C": "上下文记忆层",
            "L": "生命周期编排层",
            "O": "可观测性层",
            "V": "验证评估层",
            "G": "治理安全层",
        }

    # ------------------------------------------------------------------ #
    def calculate_shapley(self, trace: Trace) -> Dict[str, float]:
        anomalies = anomaly_detector.detect(trace)
        failed_spans = [s for s in trace.spans if s.status == "failed"]

        # 既无异常也无失败 span → 视为健康，不分配根因
        if not anomalies and not failed_spans:
            return {layer: 0.0 for layer in self.layers}

        scores = {layer: 0.0 for layer in self.layers}

        # 1) 异常规则直接命中对应层级
        for anomaly in anomalies:
            scores[anomaly["layer"]] += 2.0 if anomaly["severity"] == "high" else 1.0

        # 2) 边际贡献：移除某层后严重程度下降越多，贡献越大
        base_severity = self._severity(trace.spans, trace)
        for layer in self.layers:
            filtered = [s for s in trace.spans if s.layer != layer]
            marginal = base_severity - self._severity(filtered, trace, include_status=False)
            scores[layer] += max(0.0, marginal)

        total = sum(scores.values())
        if total <= 0:
            return {layer: 0.0 for layer in self.layers}

        shapley_values = {layer: round(v / total * 100, 2) for layer, v in scores.items()}
        return dict(sorted(shapley_values.items(), key=lambda x: x[1], reverse=True))

    # ------------------------------------------------------------------ #
    def _severity(self, spans: List, trace: Trace, include_status: bool = True) -> float:
        severity = 0.0
        severity += len([s for s in spans if s.status == "failed"]) * 1.0
        severity += len([s for s in spans if s.error]) * 0.5
        if include_status and trace.status == "failed":
            severity += 2.0
        duration = (trace.end_time or trace.start_time) - trace.start_time
        if duration > 30:
            severity += 1.0
        if trace.total_tokens and trace.total_tokens > 8000:
            severity += 0.5
        return severity

    # ------------------------------------------------------------------ #
    def get_root_cause(self, trace: Trace) -> Dict[str, Any]:
        shapley = self.calculate_shapley(trace)
        anomalies = anomaly_detector.detect(trace)
        failed_spans = [s for s in trace.spans if s.status == "failed"]

        if not anomalies and not failed_spans:
            return {
                "root_cause_layer": None,
                "root_cause_name": "无异常",
                "confidence": 0.0,
                "shapley_values": shapley,
                "anomalies": [],
                "evidence": [],
            }

        top_layer = next(iter(shapley))
        evidence = []
        for s in failed_spans:
            evidence.append({
                "layer": s.layer,
                "span": s.name,
                "type": s.type,
                "error": (s.error or "")[:300],
                "duration_ms": round(s.duration_ms or 0, 1),
            })

        return {
            "root_cause_layer": top_layer,
            "root_cause_name": self.layer_names.get(top_layer, top_layer),
            "confidence": shapley.get(top_layer, 0.0),
            "shapley_values": shapley,
            "anomalies": anomalies,
            "evidence": evidence,
        }


shapley_diagnosis = ShapleyDiagnosis()
