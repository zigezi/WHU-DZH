from typing import List, Dict, Any
from .schema import Trace


class AnomalyDetector:
    """
    基于 span 的规则式异常检测。

    每条规则返回 (命中与否, 证据描述)。规则覆盖 ETCLOVG 各层，
    不再只针对 status == "failed" 的 trace —— 因为 agent 即使最终
    返回 success，也可能在过程中出现工具失败、超时、死循环等问题。
    """

    def __init__(self):
        self.rules = [
            {"id": "T001", "name": "工具连续失败", "layer": "T", "severity": "high",
             "condition": self._tool_consecutive_fail},
            {"id": "T002", "name": "工具参数错误", "layer": "T", "severity": "medium",
             "condition": self._tool_param_error},
            {"id": "T003", "name": "未知工具调用", "layer": "T", "severity": "medium",
             "condition": self._unknown_tool},
            {"id": "L001", "name": "规划死循环", "layer": "L", "severity": "high",
             "condition": self._planning_loop},
            {"id": "L002", "name": "冗余步骤过多", "layer": "L", "severity": "medium",
             "condition": self._redundant_steps},
            {"id": "C001", "name": "目标漂移", "layer": "C", "severity": "high",
             "condition": self._goal_drift},
            {"id": "C002", "name": "上下文膨胀", "layer": "C", "severity": "medium",
             "condition": self._context_bloat},
            {"id": "E001", "name": "执行权限错误", "layer": "E", "severity": "high",
             "condition": self._permission_error},
            {"id": "E002", "name": "执行超时", "layer": "E", "severity": "medium",
             "condition": self._exec_timeout},
            {"id": "O001", "name": "埋点缺失", "layer": "O", "severity": "medium",
             "condition": self._missing_instrument},
        ]

    # ------------------------------------------------------------------ #
    def detect(self, trace: Trace) -> List[Dict[str, Any]]:
        anomalies = []
        for rule in self.rules:
            hit, evidence = rule["condition"](trace)
            if hit:
                anomalies.append({
                    "rule_id": rule["id"],
                    "name": rule["name"],
                    "layer": rule["layer"],
                    "severity": rule["severity"],
                    "evidence": evidence,
                })
        return anomalies

    # ------------------------------------------------------------------ #
    # 辅助
    # ------------------------------------------------------------------ #
    @staticmethod
    def _by_type(trace: Trace, span_type: str):
        return [s for s in trace.spans if s.type == span_type]

    @staticmethod
    def _by_layer(trace: Trace, layer: str):
        return [s for s in trace.spans if s.layer == layer]

    # ------------------------------------------------------------------ #
    # T 层：工具协议
    # ------------------------------------------------------------------ #
    def _tool_consecutive_fail(self, trace: Trace):
        tool_spans = self._by_type(trace, "tool_call")
        if len(tool_spans) < 2:
            return False, ""
        tail = tool_spans[-2:]
        if all(s.status == "failed" for s in tail):
            names = ", ".join(s.name for s in tail)
            return True, f"连续 2 次工具调用失败: {names}"
        return False, ""

    def _tool_param_error(self, trace: Trace):
        keywords = ("parameter", "argument", "required", "invalid", "validation",
                    "missing", "参数", "字段", "类型")
        for s in self._by_type(trace, "tool_call"):
            err = (s.error or "").lower()
            if err and any(k in err for k in keywords):
                return True, f"工具 {s.name} 参数错误: {s.error[:120]}"
        return False, ""

    def _unknown_tool(self, trace: Trace):
        for s in self._by_type(trace, "tool_call"):
            err = (s.error or "").lower()
            if "tool not found" in err or "未知工具" in err:
                return True, f"调用了未注册工具: {s.name}"
        return False, ""

    # ------------------------------------------------------------------ #
    # L 层：生命周期编排
    # ------------------------------------------------------------------ #
    def _planning_loop(self, trace: Trace):
        names = [s.name for s in self._by_type(trace, "tool_call")]
        if len(names) < 6:
            return False, ""
        # 最近 4 次工具调用完全重复 → 极可能在原地打转
        if len(set(names[-4:])) == 1:
            return True, f"最近 4 次重复调用同一工具: {names[-1]}"
        return False, ""

    def _redundant_steps(self, trace: Trace):
        tool_calls = len(self._by_type(trace, "tool_call"))
        if tool_calls > 8:
            return True, f"工具调用次数过多: {tool_calls}"
        return False, ""

    # ------------------------------------------------------------------ #
    # C 层：上下文记忆
    # ------------------------------------------------------------------ #
    def _goal_drift(self, trace: Trace):
        # 声称成功，但所有工具调用都失败了 → 很可能并未真正完成任务
        tools = self._by_type(trace, "tool_call")
        if not tools:
            return False, ""
        failed = [s for s in tools if s.status == "failed"]
        succeeded = [s for s in tools if s.status == "success"]
        if trace.status == "success" and failed and not succeeded:
            return True, f"任务标记成功但 {len(failed)} 次工具调用全部失败"
        if trace.result and "maximum steps" in trace.result.lower():
            return True, "达到最大步数后强行结束，未得到最终答案"
        return False, ""

    def _context_bloat(self, trace: Trace):
        if trace.total_tokens and trace.total_tokens > 8000:
            return True, f"累计 token 消耗过高: {trace.total_tokens}"
        return False, ""

    # ------------------------------------------------------------------ #
    # E 层：执行沙箱
    # ------------------------------------------------------------------ #
    def _permission_error(self, trace: Trace):
        keywords = ("permission", "denied", "access", "not allowed", "forbidden",
                    "权限", "拒绝", "禁止")
        for s in trace.spans:
            err = (s.error or "").lower()
            if err and any(k in err for k in keywords):
                return True, f"[{s.layer}/{s.name}] {s.error[:120]}"
        return False, ""

    def _exec_timeout(self, trace: Trace):
        for s in trace.spans:
            err = (s.error or "").lower()
            if "timeout" in err or "timed out" in err or "超时" in err:
                return True, f"[{s.layer}/{s.name}] {s.error[:120]}"
            if s.duration_ms and s.duration_ms > 30000:
                return True, f"[{s.layer}/{s.name}] 执行耗时 {s.duration_ms:.0f}ms 超过 30s"
        return False, ""

    # ------------------------------------------------------------------ #
    # O 层：可观测性自检
    # ------------------------------------------------------------------ #
    def _missing_instrument(self, trace: Trace):
        if trace.status == "running":
            return False, ""
        # 优先读取 worker 写入的埋点自检结果
        for s in self._by_layer(trace, "O"):
            missing = (s.attributes or {}).get("missing_layers")
            if missing:
                return True, f"缺少层级埋点: {', '.join(missing)}"
        # 兜底：直接检查关键层是否存在
        present = {s.layer for s in trace.spans}
        required = {"L", "C"}
        if trace.total_tool_calls:
            required |= {"T", "E"}
        missing = sorted(required - present)
        if missing:
            return True, f"缺少层级埋点: {', '.join(missing)}"
        return False, ""


anomaly_detector = AnomalyDetector()
