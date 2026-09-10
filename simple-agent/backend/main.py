from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uuid
from worker import run_task, task_store
from schema import TaskRequest

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def index():
    return {
        "service": "mini-agent-v2",
        "status": "running",
        "endpoints": ["/task/submit", "/task/{id}", "/tasks", "/metrics"]
    }

@app.get("/task/submit")
def submit_task(content: str):
    req = TaskRequest(task_id=str(uuid.uuid4()), content=content)
    # Run in background for long tasks
    import threading
    t = threading.Thread(target=run_task, args=(req,))
    t.start()
    return {"task_id": req.task_id, "status": "running"}

@app.get("/task/{task_id}")
def get_task(task_id: str):
    task = task_store.get(task_id)
    if not task:
        return {"error": "Task not found"}
    return task

@app.get("/tasks")
def list_tasks(limit: int = 20):
    tasks = sorted(task_store.values(), key=lambda x: x.created_at, reverse=True)
    return [t.dict() for t in tasks[:limit]]

@app.get("/metrics")
def get_metrics():
    tasks = list(task_store.values())
    success = len([t for t in tasks if t.status == "success"])
    failed = len([t for t in tasks if t.status == "failed"])
    running = len([t for t in tasks if t.status == "running"])
    
    completed = [t for t in tasks if t.status in ["success", "failed"]]
    avg_duration = sum([t.duration_ms or 0 for t in completed]) / len(completed) if completed else 0
    avg_tokens = sum([t.llm_tokens or 0 for t in completed]) / len(completed) if completed else 0
    total_tool_calls = sum([t.tool_calls_count for t in tasks])
    
    return {
        "total": len(tasks),
        "success": success,
        "failed": failed,
        "running": running,
        "avg_duration_ms": avg_duration,
        "avg_tokens": avg_tokens,
        "total_tool_calls": total_tool_calls
    }

