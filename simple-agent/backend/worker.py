import time
import uuid
import os
import json
from openai import OpenAI
from schema import TaskRequest, TaskStatus
from datetime import datetime
from tools.registry import ToolCall, ToolResult
from tools.init import init_tool_registry
from version import get_code_version

# ========== Monitor 埋点导入 ==========
from monitor.collector import TraceSpan, add_event
from monitor.trace_store import trace_store
from monitor.schema import Trace
from monitor import vlayer
from monitor import plan_observer
from monitor.guard import Guard
from monitor.routing import router
from requirements import loader
import signature
import planner

def _load_dotenv(path: str):
    """极简 .env 解析（P-1，不引入新依赖）：KEY=VALUE 逐行，跳过注释/空行。"""
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)


_load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

MODEL_NAME = "deepseek-chat"
# P5a 约束 6：τ 批跑需更高天花板，常规任务默认 10
MAX_STEPS = int(os.getenv("SA_MAX_STEPS", "10"))
WORK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workspace"))

os.makedirs(WORK_DIR, exist_ok=True)
# P-1：缺 key 大声报错退出，禁止 api_key="missing" 静默兜底
if not DEEPSEEK_API_KEY:
    raise SystemExit(
        "[worker] FATAL: DEEPSEEK_API_KEY 未设置。请在 backend/.env 写入 "
        "DEEPSEEK_API_KEY=sk-... 后重启服务（禁止把 key 提交入库）。"
    )
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
tool_registry = init_tool_registry(WORK_DIR)

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


def _record_progress(req_id: str, trace_id: str, step: int,
                     tokens_so_far: int, parent_span_id: str):
    """P1.3：每步跑 cheap 断言子集，写进度曲线 span。"""
    try:
        results = vlayer.run_assertions(
            req_id, trace_id=trace_id, cheap_only=True,
            parent_span_id=parent_span_id,
        )
        passed = sum(1 for r in results if r.passed)
        add_event(
            trace_id=trace_id, name="进度", layer="V", span_type="progress",
            parent_span_id=parent_span_id,
            attributes={
                "step": step, "passed": passed, "total": len(results),
                "tokens_so_far": tokens_so_far,
            },
        )
    except Exception:
        pass


def _load_budget(req_id: str) -> dict:
    """带 req_id 时取需求预算，否则用默认值。"""
    budget = {"max_steps": MAX_STEPS, "max_tokens": 30000, "timeout_s": 600}
    if not req_id:
        return budget
    try:
        spec = loader.get(req_id).get("budget") or {}
        for key in budget:
            if key in spec:
                budget[key] = spec[key]
    except Exception:
        pass
    return budget


def _abstain_check(content: str, trace_id: str, parent_span_id: str) -> bool:
    """P3.4：查相似先例，最高相似度 < 0.2 判为冷路径（仅记录，不改变行为）。"""
    try:
        best = 0.0
        for precedent in trace_store.list_precedents():
            best = max(best, signature.similarity(content, precedent.get("content") or ""))
        matched = best >= 0.2
        add_event(
            trace_id=trace_id, name="弃权检查", layer="L",
            span_type="abstain_check", parent_span_id=parent_span_id,
            attributes={"matched": matched, "best_similarity": round(best, 4)},
        )
        return matched
    except Exception:
        return False


def _store_precedent(req: TaskRequest, steps: list, tokens: int,
                     duration_ms: float, sig_family: str):
    plan = [
        {"tool": s.get("tool_name"), "args": s.get("args")}
        for s in steps if s.get("type") == "tool_call"
    ]
    trace_store.add_precedent({
        "sig": sig_family,
        "req_id": req.req_id,
        "plan": plan,
        "assertions_ref": req.req_id,
        "tokens": tokens,
        "duration_ms": duration_ms,
        "created_at": datetime.now(),
        "content": req.content,
    })


def _inject_precedent(req: TaskRequest, trace_id: str, sig_family: str,
                      messages: list, parent_span_id: str):
    """P5a.6 补丁2：precedent-assisted 臂——按新签名取相似先例，注入 plan 摘要（≤500 token）。"""
    best, sim = None, 0.0
    for p in trace_store.list_precedents():
        s = 1.0 if p.get("sig") == sig_family else \
            signature.similarity(req.content, p.get("content") or "")
        if s > sim:
            sim, best = s, p
    if best is None or sim < 0.2:
        return
    plan = best.get("plan") or []
    summary = json.dumps(plan, ensure_ascii=False)[:2000]  # ≈500 token 上限
    tokens_injected = len(summary) // 4
    add_event(
        trace_id=trace_id, name="先例注入", layer="L",
        span_type="precedent_injected", parent_span_id=parent_span_id,
        attributes={"precedent_sig": best.get("sig"),
                    "similarity": round(sim, 4),
                    "tokens_injected": tokens_injected},
    )
    # 插到 wiki system 之后、首轮 user 之前
    messages.insert(1, {
        "role": "system",
        "content": f"[precedent] 相似历史任务的工具调用序列摘要：{summary}",
    })


def execute_tool(trace_id: str, parent_span_id: str, tool_name: str, args: dict,
                 plan_node_id: str = None, registry=None) -> ToolResult:
    """统一工具执行入口：E 层埋点由 ToolRegistry 负责。"""
    reg = registry or tool_registry
    return reg.execute(ToolCall(
        tool_name=tool_name,
        args=args,
        trace_id=trace_id,
        parent_span_id=parent_span_id,
        plan_node_id=plan_node_id,
    ))


def run_task(req: TaskRequest, plan_node_id: str = None) -> TaskStatus:
    # 1. 创建主Trace（L层）
    start = time.time()
    trace = Trace(
        trace_id=req.task_id,
        task_id=req.task_id,
        task_content=req.content,
        start_time=start,
        status="running",
        code_version=get_code_version(),
    )
    trace_store.add_trace(trace)

    status = TaskStatus(
        task_id=req.task_id,
        status="running",
        created_at=datetime.now(),
        created_at_ts=start,
        content=req.content,
        req_id=req.req_id,
    )
    trace_store.upsert_task(status.model_dump())

    budget = _load_budget(req.req_id)
    guard = Guard(
        max_steps=budget["max_steps"],
        max_tokens=budget["max_tokens"],
        timeout_s=budget["timeout_s"],
        repeat_threshold=3,
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": req.content},
    ]

    steps = []
    total_tokens = 0
    tool_calls_count = 0
    failed_tool_calls = 0
    halted_reason = None

    # L 层：任务生命周期编排 span
    task_span = TraceSpan(
        name="任务编排", span_type="task", layer="L",
        trace_id=req.task_id, attributes={"task": req.content[:200]},
    )
    task_span.__enter__()

    # P3 §5.0.0：确定性线性规划器，真实调用 record_plan 并下传 plan_node_id
    plan = planner.make_plan(req)
    plan_id, _plan_attrs = plan_observer.record_plan(
        trace_id=req.task_id, req_id=req.req_id, plan_json=plan.to_json(),
        planner_model=plan.planner_model, prompt_version=plan.prompt_version,
        parent_span_id=task_span.span.span_id,
    )
    task_span.set_attribute("plan_id", plan_id)

    # P3.4 弃权检查（仅带 req_id 的任务）
    if req.req_id:
        _abstain_check(req.content, req.task_id, task_span.span.span_id)

    # P5a 5a.1：τ 模式检测 + DialogueDriver（多轮回路）
    tau_spec = None
    driver = None
    active_registry = tool_registry
    if req.req_id:
        try:
            spec = loader.get(req.req_id)
            if spec.get("tau_env"):
                tau_spec = spec
        except Exception:
            tau_spec = None
    if tau_spec is not None:
        try:
            from dialogue_driver import DialogueDriver
            driver = DialogueDriver(
                req, req.task_id, tau_spec, client,
                task_span.span.span_id, add_event,
            )
            first_user = driver.start()
            active_registry = driver.registry
            # τ 模式：wiki 作 system prompt；turn 0 真实用户消息（非占位开场白）
            messages = [
                {"role": "system", "content": driver.system_prompt},
                {"role": "user", "content": first_user},
            ]
        except Exception as e:  # noqa: BLE001
            status.status = "failed"
            status.error = f"[tau] driver init failed: {e}"
            driver = None

    # P5a.6 补丁1：τ 用 hidden instruction 的签名（REQ.sig），常规任务用 task 文本
    sig_family = (tau_spec.get("sig") if tau_spec else None) or signature.sign(req.content)

    # P5a.6 补丁2：臂选择（仅 τ；dev 固定 direct，避免尺子被处理污染）
    arm = "direct"
    if tau_spec is not None and driver is not None:
        if tau_spec.get("split") == "dev":
            arm, explored = "direct", False
        else:
            arm, explored = router.choose_meta(
                sig_family, ["direct", "precedent-assisted"])
        add_event(
            trace_id=req.task_id, name="臂选择", layer="L",
            span_type="arm_choice", parent_span_id=task_span.span.span_id,
            attributes={"sig_family": sig_family, "arm": arm,
                        "exploration": explored},
        )
        if arm == "precedent-assisted":
            _inject_precedent(req, req.task_id, sig_family, messages,
                              task_span.span.span_id)

    try:
        # 预算一致性（v2.1）：循环上界 = min(需求 max_steps, 系统天花板 MAX_STEPS)
        step_ceiling = min(budget["max_steps"], MAX_STEPS)
        if budget["max_steps"] > MAX_STEPS:
            add_event(
                trace_id=req.task_id, name="预算上限", layer="L",
                span_type="budget_cap",
                attributes={"req_max_steps": budget["max_steps"],
                            "applied": step_ceiling},
            )
        for step in range(step_ceiling):
            node_id = plan.node_for_step(step)
            plan_attr = {"plan_node_id": node_id}
            step_span = TraceSpan(
                name=f"步骤{step + 1}", span_type="step", layer="L",
                trace_id=req.task_id, parent_span_id=task_span.span.span_id,
                attributes={"plan_node_id": node_id, "step": step + 1},
            )
            with step_span:
                # G 层：预算三阈值 + 熔断状态机（HALT 后不再调 LLM）
                gv = guard.before_step(
                    req.task_id, step, total_tokens,
                    parent_span_id=step_span.span.span_id,
                )
                if gv.decision == "HALT":
                    halted_reason = f"guard before_step: {gv.evidence_refs}"
                    step_span.set_attribute("g_halted", True)
                    break

                # 2. LLM推理埋点（C层）
                with TraceSpan(
                    name="LLM推理", span_type="llm_call", layer="C",
                    trace_id=req.task_id, parent_span_id=step_span.span.span_id,
                    attributes=plan_attr,
                ) as llm_span:
                    resp = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=messages,
                        tools=active_registry.get_schemas(),
                        tool_choice="auto",
                    )
                    usage = resp.usage
                    llm_span.set_attributes({
                        "model": MODEL_NAME,
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens,
                        # P5a.9 §三.2：DeepSeek prompt cache instrumentation
                        "prompt_cache_hit_tokens": getattr(
                            usage, "prompt_cache_hit_tokens", None),
                        "prompt_cache_miss_tokens": getattr(
                            usage, "prompt_cache_miss_tokens", None),
                    })

                message = resp.choices[0].message
                total_tokens += resp.usage.total_tokens

                tool_calls = getattr(message, "tool_calls", None)

                # 无工具调用：τ 模式 = RESPOND（继续对话）；否则 = 任务完成
                if not tool_calls:
                    if driver is not None:
                        nxt = driver.on_respond(
                            message.content or "", resp.usage.total_tokens)
                        if nxt is None:
                            # driver 判定 ###STOP###，对话自然结束
                            status.result = message.content
                            status.status = "success"
                            step_span.set_attribute("tau_stop", True)
                            break
                        messages.append(message)
                        messages.append({"role": "user", "content": nxt})
                        continue
                    status.result = message.content
                    status.status = "success"
                    step_span.set_attribute("finished", True)
                    break

                messages.append(message)
                for tool_call in tool_calls:
                    tool_calls_count += 1
                    try:
                        args = json.loads(tool_call.function.arguments)
                    except (json.JSONDecodeError, TypeError) as e:
                        # LLM 偶发产出非法 JSON 参数：回灌错误，不让整个任务崩掉
                        failed_tool_calls += 1
                        messages.append({
                            "role": "tool", "tool_call_id": tool_call.id,
                            "content": f"Error: invalid JSON arguments: {e}",
                        })
                        continue

                    step_start = time.time()
                    # 3. 工具协议埋点（T层），内部再由 registry 产生 E 层执行埋点
                    with TraceSpan(
                        name=tool_call.function.name, span_type="tool_call", layer="T",
                        trace_id=req.task_id, parent_span_id=step_span.span.span_id,
                        attributes={**plan_attr, "tool": tool_call.function.name,
                                    "args": _safe_args(args)},
                    ) as tool_span:
                        try:
                            result = execute_tool(
                                trace_id=req.task_id,
                                parent_span_id=tool_span.span.span_id,
                                tool_name=tool_call.function.name,
                                args=args,
                                plan_node_id=node_id,
                                registry=active_registry if driver is not None else None,
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

                    # G 层：无进展检测 + 纠偏反馈
                    gv = guard.after_tool(
                        req.task_id, tool_call.function.name, args,
                        error="" if step_success else (step_error or ""),
                        parent_span_id=step_span.span.span_id,
                    )
                    if gv.decision == "HALT":
                        halted_reason = f"guard after_tool: {gv.evidence_refs}"
                        break
                    if gv.decision == "PARTIAL":
                        fb = guard.pop_feedback(req.task_id)
                        # τ 模式下不注入纠偏消息，避免污染多轮对话
                        if fb and fb.get("msg") and driver is None:
                            messages.append({"role": "user", "content": fb["msg"]})

                if driver is not None:
                    driver.note_tool_step()
                    if driver.last_done:
                        # 第 4 条终止路径：agent 调 terminate 工具 → env.done
                        status.status = "success"
                        status.result = status.result or "env.done (terminate tool)"
                        step_span.set_attribute("tau_done", True)
                        break

                if halted_reason:
                    step_span.set_attribute("g_halted", True)
                    break

                # P1.3 每步进度曲线（仅带 req_id 的任务）
                if req.req_id:
                    _record_progress(
                        req.req_id, req.task_id, step + 1,
                        total_tokens, step_span.span.span_id,
                    )

        if status.status == "running":
            status.status = "success"
            if not status.result:
                status.result = "Task completed after maximum steps"

        if halted_reason:
            status.status = "g_halted"
            status.result = "任务被治理层熔断终止"
            status.error = halted_reason

    except Exception as e:
        status.status = "failed"
        status.error = str(e)

    # P5a 5a.3：τ episode 结束 → evaluator reward → V 层（loss = 1 - reward）
    if driver is not None:
        try:
            tau_reward, tau_info = driver.finish()
            if tau_reward is not None:
                from requirements.adapters.tau.scoring import score_tau_episode
                score_tau_episode(
                    req.task_id, tau_reward, tau_info, task_span.span.span_id
                )
                status.result = f"{status.result or ''} | tau_reward={tau_reward}"
            user_tokens = driver.simulator.total_tokens if driver.simulator else 0
            add_event(
                trace_id=req.task_id, name="τ成本", layer="O",
                span_type="tau_cost", parent_span_id=task_span.span.span_id,
                attributes={"agent_tokens": total_tokens,
                            "user_tokens": user_tokens,
                            "total_tokens": total_tokens + user_tokens},
            )
        except Exception as e:  # noqa: BLE001
            status.error = (status.error or "") + f" [tau scoring: {e}]"

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

    # P3.2 / P3.3 / P5a.6：路由后验更新（按实际臂）+ 成功先例入库
    try:
        router.update(sig_family, arm, status.status == "success", total_tokens)
        if status.status == "success":
            _store_precedent(req, steps, total_tokens, status.duration_ms, sig_family)
    except Exception:
        pass

    # P3 §5.0.2：写切分质量报告（C 段产物）
    try:
        plan_observer.write_decomposition_report(req.task_id)
    except Exception:
        pass

    trace_store.upsert_task(status.model_dump())
    return status
