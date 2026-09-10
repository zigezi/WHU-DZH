import time
import uuid
from typing import Callable, Dict, Any, Optional
from pydantic import BaseModel

from monitor.schema import Span
from monitor.trace_store import trace_store


class ToolCall(BaseModel):
    tool_name: str
    args: Dict[str, Any]
    # 可选：携带 trace 上下文，registry 会据此产生 E 层（执行沙箱）span
    trace_id: Optional[str] = None
    parent_span_id: Optional[str] = None


class ToolResult(BaseModel):
    success: bool
    output: str
    error: str = ""
    duration_ms: float = 0


def _safe_args(args: Dict[str, Any], limit: int = 800) -> Dict[str, Any]:
    """裁剪过长的参数，避免把大文件内容写进 span 属性。"""
    safe = {}
    for key, value in args.items():
        if key == "work_dir":
            continue
        if isinstance(value, str) and len(value) > limit:
            safe[key] = value[:limit] + f"...(+{len(value) - limit})"
        else:
            safe[key] = value
    return safe


class ToolRegistry:
    def __init__(self, work_dir: str):
        self.work_dir = work_dir
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, dict] = {}

    def register(self, name: str, schema: dict, func: Callable):
        self._tools[name] = func
        self._schemas[name] = schema

    def get_schemas(self):
        return list(self._schemas.values())

    def execute(self, call: ToolCall) -> ToolResult:
        start = time.time()

        if call.tool_name not in self._tools:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool not found: {call.tool_name}",
                duration_ms=(time.time() - start) * 1000,
            )

        # E 层埋点：真正的执行沙箱调用
        exec_span: Optional[Span] = None
        if call.trace_id:
            exec_span = Span(
                span_id=str(uuid.uuid4()),
                trace_id=call.trace_id,
                parent_span_id=call.parent_span_id,
                name=call.tool_name,
                type="sandbox_exec",
                layer="E",
                status="running",
                start_time=start,
                attributes={"tool": call.tool_name, "args": _safe_args(call.args)},
            )
            trace_store.add_span(exec_span)

        try:
            # Inject work_dir into args for all tools
            call.args["work_dir"] = self.work_dir
            output = self._tools[call.tool_name](**call.args)
            result = ToolResult(
                success=True,
                output=output,
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            result = ToolResult(
                success=False,
                output="",
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

        if exec_span is not None:
            exec_span.status = "success" if result.success else "failed"
            exec_span.end_time = time.time()
            exec_span.duration_ms = result.duration_ms
            exec_span.error = result.error or None
            exec_span.attributes["success"] = result.success
            exec_span.attributes["output"] = (result.output or "")[:1000]
            trace_store.update_span(exec_span)

        return result
