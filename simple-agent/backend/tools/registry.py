import hashlib
import os
import time
import uuid
from typing import Callable, Dict, Any, Optional
from pydantic import BaseModel

from monitor.schema import Span
from monitor.trace_store import trace_store

_SKIP_ARGS = ("work_dir", "trace_id", "parent_span_id")


class ToolCall(BaseModel):
    tool_name: str
    args: Dict[str, Any]
    # 可选：携带 trace 上下文，registry 会据此产生 E 层（执行沙箱）span
    trace_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    # 可选：所属 plan 节点，B/C 段靠它把执行面数据映射回规划面
    plan_node_id: Optional[str] = None


class ToolResult(BaseModel):
    success: bool
    output: str
    error: str = ""
    duration_ms: float = 0


def _safe_args(args: Dict[str, Any], limit: int = 800) -> Dict[str, Any]:
    """裁剪过长的参数，避免把大文件内容写进 span 属性。"""
    safe = {}
    for key, value in args.items():
        if key in _SKIP_ARGS:
            continue
        if isinstance(value, str) and len(value) > limit:
            safe[key] = value[:limit] + f"...(+{len(value) - limit})"
        else:
            safe[key] = value
    return safe


def _manifest(work_dir: str) -> Dict[str, str]:
    """{相对路径: md5前8位}，跳过 .git / node_modules 与 >10MB 文件。"""
    manifest: Dict[str, str] = {}
    if not os.path.isdir(work_dir):
        return manifest
    for dirpath, dirnames, filenames in os.walk(work_dir):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules")]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(full) > 10 * 1024 * 1024:
                    continue
                rel = os.path.relpath(full, work_dir)
                with open(full, "rb") as f:
                    manifest[rel] = hashlib.md5(f.read()).hexdigest()[:8]
            except OSError:
                continue
    return manifest


def _effect_diff(before: Dict[str, str], after: Dict[str, str]) -> Dict[str, list]:
    return {
        "created": sorted(set(after) - set(before))[:50],
        "modified": sorted(p for p in after if p in before and after[p] != before[p])[:50],
        "deleted": sorted(set(before) - set(after))[:50],
    }


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
            if call.plan_node_id:
                exec_span.attributes["plan_node_id"] = call.plan_node_id
            trace_store.add_span(exec_span)

        before = _manifest(self.work_dir)
        func = self._tools[call.tool_name]
        try:
            # Inject execution context for all tools
            call.args["work_dir"] = self.work_dir
            call.args.setdefault("trace_id", call.trace_id)
            call.args.setdefault("parent_span_id", call.parent_span_id)
            output = func(**call.args)
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
        after = _manifest(self.work_dir)

        if exec_span is not None:
            exec_span.status = "success" if result.success else "failed"
            exec_span.end_time = time.time()
            exec_span.duration_ms = result.duration_ms
            exec_span.error = result.error or None
            exec_span.attributes["success"] = result.success
            exec_span.attributes["output"] = (result.output or "")[:1000]
            exec_span.attributes["effect_diff"] = _effect_diff(before, after)
            hook = getattr(func, "_last_exec_meta", None)
            if hook is not None:
                try:
                    exec_span.attributes.update(hook() or {})
                except Exception:
                    pass
            trace_store.update_span(exec_span)

        return result
