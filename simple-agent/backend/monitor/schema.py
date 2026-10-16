from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class Span(BaseModel):
    span_id: str
    trace_id: str
    parent_span_id: Optional[str] = None
    name: str
    type: str  # task / step / llm_call / tool_call / sandbox_exec / observability / validation / event
    layer: str  # E / T / C / L / O / V / G
    status: str  # running / success / failed
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    attributes: Dict[str, Any] = {}
    error: Optional[str] = None


class Trace(BaseModel):
    trace_id: str
    task_id: str
    task_content: str
    start_time: float
    end_time: Optional[float] = None
    status: str  # running / success / failed
    spans: List[Span] = []
    total_tokens: int = 0
    total_tool_calls: int = 0
    result: Optional[str] = None
    error: Optional[str] = None
    code_version: Optional[str] = None
