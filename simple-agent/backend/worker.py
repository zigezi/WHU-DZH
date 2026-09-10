import time
import uuid
import os
import json
from openai import OpenAI
from schema import TaskRequest, TaskStatus
from datetime import datetime
from tools.registry import ToolCall, ToolResult
from tools.init import init_tool_registry

# ========== Monitor 埋点导入 ==========
from monitor.collector import TraceSpan, add_event
from monitor.trace_store import trace_store
from monitor.schema import Trace

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

MODEL_NAME = "deepseek-chat"
MAX_STEPS = 10
WORK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workspace"))

os.makedirs(WORK_DIR, exist_ok=True)
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
tool_registry = init_tool_registry(WORK_DIR)
task_store = {}

SYSTEM_PROMPT = """You are a coding agent. You can read/write files and execute commands in the workspace.
Follow these rules:
1. Your working directory root is the workspace folder. Use relative paths directly, DO NOT add "workspace/" prefix.
2. First understand the task, then use tools to accomplish it
3. After tool calls, analyze the result and continue if needed
4. When the task is complete, give a final summary
5. Always use tools for file operations, never pretend you did it
6. For frontend tasks, create proper HTML/CSS/JS files
"""


def _safe_args(args: dict, limit: int = 500) -> dict:
    safe = {}
    for key, value in args.items():
        if key == "work_dir":
            continue
        if isinstance(value, str) and len(value) > limit:
            safe[key] = value[:limit] + f"...(+{len(value) - limit})"
        else:
            safe[key] = value
    return safe


def execute_tool(trace_id: str, parent_span_id: str, tool_name: str, args: dict) -> ToolResult:
    """统一工具执行入口：E 层埋点由 ToolRegistry 负责。"""
    return tool_registry.execute(ToolCall(
        tool_name=tool_name,
        args=args,
        trace_id=trace_id,
        parent_span_id=parent_span_id,
    ))


def run_task(req: TaskRequest) -> TaskStatus:
    # 1. 创建主Trace（L层）
    trace = Trace(
        trace_id=req.task_id,
        task_id=req.task_id,
        task_content=req.content,
        start_time=time.time(),
        status="running",
    )
    trace_store.add_trace(trace)

    status = TaskStatus(
        task_id=req.task_id,
        status="running",
        created_at=datetime.now(),
        content=req.content,
    )
    task_store[req.task_id] = status
    start = time.time()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": req.content},
    ]

    steps = []
    total_tokens = 0
    tool_calls_count = 0
    failed_tool_calls = 0

    # L 层：任务生命周期编排 span
    task_span = TraceSpan(
        name="任务编排", span_type="task", layer="L",
        trace_id=req.task_id, attributes={"task": req.content[:200]},
    )
    task_span.__enter__()

    try:
        for step in range(MAX_STEPS):
            step_span = TraceSpan(
                name=f"步骤{step + 1}", span_type="step", layer="L",
                trace_id=req.task_id, parent_span_id=task_span.span.span_id,
                attributes={"step": step + 1},
            )
            with step_span:
                # 2. LLM推理埋点（C层）
                with TraceSpan(
                    name="LLM推理", span_type="llm_call", layer="C",
                    trace_id=req.task_id, parent_span_id=step_span.span.span_id,
                ) as llm_span:
                    resp = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=messages,
                        tools=tool_registry.get_schemas(),
                        tool_choice="auto",
                    )
                    usage = resp.usage
                    llm_span.set_attributes({
                        "model": MODEL_NAME,
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens,
                    })

                message = resp.choices[0].message
                total_tokens += resp.usage.total_tokens

                tool_calls = getattr(message, "tool_calls", None)

                # 无工具调用 = 任务完成
                if not tool_calls:
                    status.result = message.content
                    status.status = "success"
                    step_span.set_attribute("finished", True)
                    break

                messages.append(message)
                for tool_call in tool_calls:
                    tool_calls_count += 1
                    args = json.loads(tool_call.function.arguments)

                    step_start = time.time()
                    # 3. 工具协议埋点（T层），内部再由 registry 产生 E 层执行埋点
                    with TraceSpan(
                        name=tool_call.function.name, span_type="tool_call", layer="T",
                        trace_id=req.task_id, parent_span_id=step_span.span.span_id,
                        attributes={"tool": tool_call.function.name,
                                    "args": _safe_args(args)},
                    ) as tool_span:
                        try:
                            result = execute_tool(
                                trace_id=req.task_id,
                                parent_span_id=tool_span.span.span_id,
                                tool_name=tool_call.function.name,
                                args=args,
                            )
                            step_success = result.success
                            step_error = result.error
                            output = result.output
                        except Exception as e:
                            step_success = False
                            step_error = str(e)
                            output = ""

                        tool_span.set_attributes({
                            "success": step_success,
                            "output": (output or "")[:500],
                        })
                        if not step_success:
                            tool_span.fail(step_error)
                            failed_tool_calls += 1

                    steps.append({
                        "type": "tool_call",
                        "tool_name": tool_call.function.name,
                        "args": args,
                        "success": step_success,
                        "output": output[:500],
                        "error": step_error,
                        "duration_ms": (time.time() - step_start) * 1000,
                    })

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": output if step_success else f"Error: {step_error}",
                    })

        if status.status != "success":
            status.status = "success"
            if not status.result:
                status.result = "Task completed after maximum steps"

    except Exception as e:
        status.status = "failed"
        status.error = str(e)

    # 4. O 层：埋点自检（记录哪些层级缺失）
    spans = trace_store.get_spans_by_trace(req.task_id)
    present = {s.layer for s in spans}
    required = {"L", "C"}
    if tool_calls_count:
        required |= {"T", "E"}
    missing = sorted(required - present)
    add_event(
        trace_id=req.task_id,
        name="埋点自检",
        layer="O",
        parent_span_id=task_span.span.span_id,
        span_type="observability",
        attributes={
            "present_layers": sorted(present),
            "missing_layers": missing,
            "span_count": len(spans),
            "failed_tool_calls": failed_tool_calls,
        },
    )

    task_span.set_attributes({"status": status.status, "total_tool_calls": tool_calls_count})
    if status.status == "failed":
        task_span.fail(status.error or "task failed")
    task_span.__exit__(None, None, None)

    # 5. 更新主Trace状态
    trace.status = status.status
    trace.end_time = time.time()
    trace.total_tokens = total_tokens
    trace.total_tool_calls = tool_calls_count
    trace.result = status.result
    trace.error = status.error
    trace_store.update_trace(trace)

    status.finished_at = datetime.now()
    status.duration_ms = (time.time() - start) * 1000
    status.llm_tokens = total_tokens
    status.steps = steps
    status.tool_calls_count = tool_calls_count
    status.created_at_ts = status.created_at.timestamp()

    task_store[req.task_id] = status
    return status
