"""G 层：熔断状态机 + 无进展检测（P2.2）。

状态机 CLOSED / OPEN / HALF_OPEN：
- CLOSED：正常；预算三阈值（step/token/timeout）或连续重复触发 HALT；
- OPEN：冷却 60s，期间 before_step 一律 HALT；
- HALF_OPEN：冷却结束放行一次试探，成功即回 CLOSED。

无进展检测：对 sha1(tool + json(args) + error) 连续重复 >= repeat_threshold
判定为原地打转。重复到阈值-1 时注入纠偏消息（PARTIAL），到阈值时熔断（HALT）。
"""
import hashlib
import json
import time
from dataclasses import dataclass
from typing import Dict, Optional

from .collector import add_event
from .judges import JudgeVerdict

COOLDOWN_S = 60
_FEEDBACK_MSG = "检测到对 {tool} 的重复调用，请改变策略，不要再用相同参数重试。"


@dataclass
class _TraceState:
    state: str = "CLOSED"
    opened_at: float = 0.0
    started_at: float = 0.0
    last_sig: Optional[str] = None
    repeat: int = 0
    pending_feedback: Optional[dict] = None
    guard_span_id: Optional[str] = None


class Guard:
    def __init__(self, max_steps: int = 10, max_tokens: int = 30000,
                 timeout_s: int = 600, repeat_threshold: int = 3,
                 cooldown_s: int = COOLDOWN_S):
        self.max_steps = max_steps
        self.max_tokens = max_tokens
        self.timeout_s = timeout_s
        self.repeat_threshold = repeat_threshold
        self.cooldown_s = cooldown_s
        self._states: Dict[str, _TraceState] = {}

    # ------------------------------------------------------------------ #
    def _state(self, trace_id: str) -> _TraceState:
        st = self._states.get(trace_id)
        if st is None:
            st = _TraceState(started_at=time.time())
            self._states[trace_id] = st
        return st

    @staticmethod
    def _sig_text(text: str) -> str:
        return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]

    def _sig(self, tool_name: str, args: dict, error: str) -> str:
        clean = {k: v for k, v in (args or {}).items()
                 if k not in ("work_dir", "trace_id", "parent_span_id")}
        return self._sig_text(
            tool_name + json.dumps(clean, sort_keys=True, default=str) + (error or "")
        )

    def _write(self, trace_id: str, span_type: str, attrs: dict,
               parent_span_id: Optional[str] = None, name: Optional[str] = None):
        return add_event(
            trace_id=trace_id, name=name or span_type, layer="G",
            span_type=span_type, parent_span_id=parent_span_id, attributes=attrs,
        )

    def _halt(self, trace_id: str, reason: str, evidence: str,
              parent_span_id: Optional[str] = None) -> JudgeVerdict:
        span = self._write(
            trace_id, "circuit_break",
            {"reason": reason, "evidence": evidence},
            parent_span_id, name="熔断",
        )
        return JudgeVerdict(
            decision="HALT", confidence=1.0, domain_check=True,
            evidence_refs=[span.span_id], form="rule",
        )

    @staticmethod
    def _pass() -> JudgeVerdict:
        return JudgeVerdict(decision="PASS", confidence=1.0, domain_check=True,
                            evidence_refs=[], form="rule")

    # ------------------------------------------------------------------ #
    def before_step(self, trace_id: str, step: int, tokens_used: int,
                    parent_span_id: Optional[str] = None) -> JudgeVerdict:
        st = self._state(trace_id)
        if st.state == "OPEN":
            if time.time() - st.opened_at >= self.cooldown_s:
                st.state = "HALF_OPEN"
            else:
                return self._halt(
                    trace_id, "circuit_open",
                    f"熔断冷却中，剩余 {self.cooldown_s - (time.time() - st.opened_at):.0f}s",
                    parent_span_id,
                )
        if step >= self.max_steps:
            return self._halt(trace_id, "max_steps",
                              f"step={step} >= {self.max_steps}", parent_span_id)
        if tokens_used >= self.max_tokens:
            return self._halt(trace_id, "max_tokens",
                              f"tokens={tokens_used} >= {self.max_tokens}", parent_span_id)
        if time.time() - st.started_at >= self.timeout_s:
            return self._halt(trace_id, "timeout",
                              f"elapsed >= {self.timeout_s}s", parent_span_id)
        return self._pass()

    def after_tool(self, trace_id: str, tool_name: str, args: dict,
                   error: str = "",
                   parent_span_id: Optional[str] = None) -> JudgeVerdict:
        st = self._state(trace_id)
        sig = self._sig(tool_name, args, error)

        # 1) 结算上一轮纠偏反馈：下一次调用签名是否改变
        if st.pending_feedback is not None:
            corrected = sig != st.pending_feedback["sig"]
            self._write(
                trace_id, "feedback_response",
                {"corrected": corrected, "tool": tool_name},
                st.pending_feedback["span_id"], name="反馈响应",
            )
            st.pending_feedback = None

        # 2) 重复签名计数
        if sig == st.last_sig:
            st.repeat += 1
        else:
            st.repeat = 1
            st.last_sig = sig

        # 3) HALF_OPEN 试探结束 → 回到 CLOSED
        if st.state == "HALF_OPEN":
            st.state = "CLOSED"
            st.repeat = 0
            return self._pass()

        # 4) 达到阈值 → 熔断
        if st.repeat >= self.repeat_threshold:
            st.state = "OPEN"
            st.opened_at = time.time()
            verdict = self._halt(
                trace_id, "repeat",
                f"{tool_name} 连续重复 {st.repeat} 次 (sig={sig})", parent_span_id,
            )
            st.guard_span_id = verdict.evidence_refs[0] if verdict.evidence_refs else None
            self._write(
                trace_id, "feedback_injected",
                {"guard_span_id": st.guard_span_id, "tool": tool_name,
                 "msg_hash": self._sig_text(_FEEDBACK_MSG.format(tool=tool_name))},
                parent_span_id, name="纠偏注入",
            )
            st.pending_feedback = {"span_id": st.guard_span_id, "sig": sig,
                                   "msg": _FEEDBACK_MSG.format(tool=tool_name)}
            return verdict

        # 5) 阈值前一步 → 注入纠偏消息但不熔断
        if st.repeat == self.repeat_threshold - 1:
            msg = _FEEDBACK_MSG.format(tool=tool_name)
            fb = self._write(
                trace_id, "feedback_injected",
                {"guard_span_id": None, "tool": tool_name, "msg": msg,
                 "msg_hash": self._sig_text(msg)},
                parent_span_id, name="纠偏注入",
            )
            st.pending_feedback = {"span_id": fb.span_id, "sig": sig, "msg": msg}
            return JudgeVerdict(
                decision="PARTIAL", confidence=1.0, domain_check=True,
                evidence_refs=[fb.span_id], form="rule",
            )

        return self._pass()

    def pop_feedback(self, trace_id: str) -> Optional[dict]:
        st = self._states.get(trace_id)
        if st and st.pending_feedback:
            return dict(st.pending_feedback)
        return None

    def reset(self, trace_id: str):
        self._states.pop(trace_id, None)
