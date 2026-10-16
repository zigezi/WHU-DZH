import time
import uuid
import inspect
from functools import wraps
from .schema import Span
from .trace_store import trace_store


class TraceSpan:
    """
    同时支持装饰器模式和上下文管理器模式。

    用法1（装饰器，线程安全，每次调用生成独立 span）:
        @TraceSpan("工具执行", "tool_call", "T", name_arg="tool_name")
        def execute_tool(trace_id, tool_name, args): ...

    用法2（上下文管理器，可在 with 块内补充属性）:
        with TraceSpan("LLM推理", "llm_call", "C", trace_id=tid) as sp:
            sp.set_attribute("model", MODEL_NAME)
    """

    def __init__(self, name: str, span_type: str, layer: str, trace_id: str = None,
                 parent_span_id: str = None, attributes: dict = None, name_arg: str = None):
        self.name = name
        self.span_type = span_type
        self.layer = layer
        self.trace_id = trace_id
        self.parent_span_id = parent_span_id
        self.attributes = dict(attributes or {})
        # 装饰器模式下，从被装饰函数的该参数名中取真实名称（如工具名）
        self.name_arg = name_arg
        self.span = None  # 仅上下文管理器模式使用

    # ------------------------------------------------------------------ #
    # 内部工具
    # ------------------------------------------------------------------ #
    def _new_span(self, trace_id: str, parent_span_id: str = None, name: str = None) -> Span:
        return Span(
            span_id=str(uuid.uuid4()),
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            name=name or self.name,
            type=self.span_type,
            layer=self.layer,
            status="running",
            start_time=time.time(),
            attributes=dict(self.attributes),
        )

    @staticmethod
    def _finish(span: Span, status: str, error: str = None):
        span.status = status
        span.end_time = time.time()
        span.duration_ms = (span.end_time - span.start_time) * 1000
        if error:
            span.error = error
        trace_store.update_span(span)

    def _resolve_name(self, func, args, kwargs) -> str:
        if not self.name_arg:
            return self.name
        if self.name_arg in kwargs:
            return str(kwargs[self.name_arg])
        try:
            bound = inspect.signature(func).bind_partial(*args, **kwargs)
            if self.name_arg in bound.arguments:
                return str(bound.arguments[self.name_arg])
        except (TypeError, ValueError):
            pass
        return self.name

    # ------------------------------------------------------------------ #
    # 装饰器模式
    # ------------------------------------------------------------------ #
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 自动从参数里取 trace_id
            tid = self.trace_id or kwargs.get("trace_id")
            if not tid and args and isinstance(args[0], str) and len(args[0]) > 10:
                tid = args[0]
            if not tid:
                tid = str(uuid.uuid4())

            parent = kwargs.get("parent_span_id", self.parent_span_id)
            span = self._new_span(tid, parent, self._resolve_name(func, args, kwargs))
            trace_store.add_span(span)
            try:
                result = func(*args, **kwargs)
                self._finish(span, "success")
                return result
            except Exception as e:
                self._finish(span, "failed", str(e))
                raise
        return wrapper

    # ------------------------------------------------------------------ #
    # 上下文管理器模式
    # ------------------------------------------------------------------ #
    def __enter__(self):
        if not self.trace_id:
            self.trace_id = str(uuid.uuid4())
        self.span = self._new_span(self.trace_id, self.parent_span_id)
        trace_store.add_span(self.span)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self._finish(self.span, "failed", str(exc_val))
        elif self.span.status == "failed":
            self._finish(self.span, "failed", self.span.error)
        else:
            self._finish(self.span, "success")
        return False

    def set_attribute(self, key: str, value):
        if self.span is not None:
            self.span.attributes[key] = value
        return self

    def set_attributes(self, values: dict):
        if self.span is not None and values:
            self.span.attributes.update(values)
        return self

    def fail(self, error: str = ""):
        """在 with 块内手动标记失败，__exit__ 会保留该状态。"""
        if self.span is not None:
            self.span.status = "failed"
            if error:
                self.span.error = error
        return self


# 兼容旧的调用方式
def trace_span(name: str, span_type: str, layer: str, **kwargs):
    return TraceSpan(name, span_type, layer, **kwargs)


def add_event(trace_id: str, name: str, layer: str, attributes: dict = None,
              parent_span_id: str = None, span_type: str = "event") -> Span:
    now = time.time()
    span = Span(
        span_id=str(uuid.uuid4()),
        trace_id=trace_id,
        parent_span_id=parent_span_id,
        name=name,
        type=span_type,
        layer=layer,
        status="success",
        start_time=now,
        end_time=now,
        duration_ms=0,
        attributes=attributes or {},
    )
    trace_store.add_span(span)
    return span
