from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uuid
import threading
from worker import run_task
from schema import TaskRequest, TaskSubmitIn
from monitor.trace_store import trace_store
import signature

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def index():
    return {
        "service": "mini-agent-v2",
        "status": "running",
        "endpoints": ["/task/submit", "/task/{id}", "/tasks", "/metrics"]
    }


def _submit(content: str, req_id: str = None):
    req = TaskRequest(task_id=str(uuid.uuid4()), content=content, req_id=req_id)
    # Run in background for long tasks
    t = threading.Thread(target=run_task, args=(req,))
    t.start()
    return {"task_id": req.task_id, "status": "running"}


@app.post("/task/submit")
def submit_task(body: TaskSubmitIn):
    return _submit(body.content, body.req_id)


@app.get("/task/submit")
def submit_task_legacy(content: str, req_id: str = None):
    """Deprecated: kept for backward compatibility, prefer POST JSON."""
    result = _submit(content, req_id)
    result["deprecated"] = True
    result["message"] = "GET /task/submit is deprecated; use POST with JSON body {'content': ...}"
    return result


@app.get("/task/{task_id}")
def get_task(task_id: str):
    task = trace_store.get_task(task_id)
    if not task:
        return {"error": "Task not found"}
    return task


@app.get("/tasks")
def list_tasks(limit: int = 20):
    return trace_store.list_tasks(limit=limit)


@app.get("/precedents/similar")
def similar_precedents(content: str, top: int = 3):
    """P3.3：返回与 content 最相似的 Top-N 先例。"""
    scored = []
    for precedent in trace_store.list_precedents():
        score = signature.similarity(content, precedent.get("content") or "")
        if score > 0:
            scored.append({**precedent, "similarity": round(score, 4)})
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:top]


@app.get("/metrics")
def get_metrics():
    tasks = trace_store.list_tasks(limit=100000)
    success = len([t for t in tasks if t["status"] == "success"])
    failed = len([t for t in tasks if t["status"] == "failed"])
    running = len([t for t in tasks if t["status"] == "running"])

    completed = [t for t in tasks if t["status"] in ["success", "failed"]]
    avg_duration = sum([t["duration_ms"] or 0 for t in completed]) / len(completed) if completed else 0
    avg_tokens = sum([t["llm_tokens"] or 0 for t in completed]) / len(completed) if completed else 0
    total_tool_calls = sum([t["tool_calls_count"] or 0 for t in tasks])

    return {
        "total": len(tasks),
        "success": success,
        "failed": failed,
        "running": running,
        "avg_duration_ms": avg_duration,
        "avg_tokens": avg_tokens,
        "total_tool_calls": total_tool_calls
    }
