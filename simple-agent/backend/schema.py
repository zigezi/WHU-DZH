from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class TaskRequest(BaseModel):
    task_id: str
    content: str
    req_id: Optional[str] = None
    context: Optional[dict] = {}

class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending / running / success / failed / g_halted / abstained
    created_at: datetime
    created_at_ts: float = 0
    finished_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    llm_tokens: Optional[int] = 0
    content: str = ""
    steps: List[Dict[str, Any]] = []
    tool_calls_count: int = 0
    req_id: Optional[str] = None

class TaskSubmitIn(BaseModel):
    content: str
    req_id: Optional[str] = None

class MonitorMetrics(BaseModel):
    total: int
    success: int
    failed: int
    running: int
    avg_duration_ms: float
    avg_tokens: float
    total_tool_calls: int

