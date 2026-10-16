#!/usr/bin/env python3
"""P5a.11 机制存在性验证：guard 单元测试 + 金丝雀任务。

- guard 单元测试：确定性，验证"连续重复 >=3 触发 HALT"的状态机存在且工作。
- 金丝雀任务：构造一个永远返回错误的假工具，让 DeepSeek 真跑一个任务，
  观察 (a) 模型是否在连续失败时换策略；(b) 不换时 guard 是否熔断。

定位：仅验证"机制存在且工作"，**不得**被引用为"P5 提升通过率"的证据。
"""
import json
import os
import sys
import time
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from monitor.guard import Guard  # noqa: E402
from monitor.trace_store import trace_store  # noqa: E402
from monitor.schema import Trace  # noqa: E402
from openai import OpenAI  # noqa: E402

# load key
_env = {}
with open(os.path.join(BACKEND, ".env"), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            _env[k.strip()] = v.strip()
CLIENT = OpenAI(api_key=_env["DEEPSEEK_API_KEY"],
                base_url=_env.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"))


def _new_trace(prefix):
    tid = f"{prefix}-{uuid.uuid4().hex[:8]}"
    trace_store.add_trace(Trace(trace_id=tid, task_id=tid, task_content=prefix,
                                start_time=time.time(), status="running"))
    return tid


def guard_unit_test():
    print("=== guard 单元测试（确定性，无 LLM）===")
    g = Guard(repeat_threshold=3)
    tid = _new_trace("canary-unit")
    d = []
    for i in range(3):
        v = g.after_tool(tid, "fake_tool", {"key": "alpha"}, "boom")
        d.append(v.decision)
    print(f"same tool+args+error x3 -> decisions={d} (期望 PASS/PARTIAL/HALT)")
    # 换签名应重置
    g2 = Guard(repeat_threshold=3)
    tid2 = _new_trace("canary-unit2")
    a = g2.after_tool(tid2, "fake_tool", {"key": "alpha"}, "boom").decision
    b = g2.after_tool(tid2, "fake_tool", {"key": "beta"}, "boom").decision
    print(f"different args -> {[a, b]} (期望 PASS/PASS，不误熔断)")
    return d == ["PASS", "PARTIAL", "HALT"]


def canary_llm():
    print("\n=== 金丝雀任务（真实 LLM，假工具永远报错）===")
    tid = _new_trace("canary-llm")
    g = Guard(repeat_threshold=3)
    tools = [{"type": "function", "function": {
        "name": "canary_fetch",
        "description": "Fetch a stored value by key. (This tool is currently broken and always errors.)",
        "parameters": {"type": "object",
                       "properties": {"key": {"type": "string"}},
                       "required": ["key"]}}}]
    messages = [
        {"role": "system", "content": "You are an agent. Use tools to accomplish the task. If a tool fails, adapt your approach."},
        {"role": "user", "content": "Use canary_fetch to get the value for key 'alpha', then report it."},
    ]
    sigs, halted, changed = [], False, False
    tokens = 0
    for step in range(8):
        gv = g.before_step(tid, step, tokens)
        if gv.decision == "HALT":
            halted = True
            print(f"  step{step}: guard before_step HALT")
            break
        resp = CLIENT.chat.completions.create(model="deepseek-chat", messages=messages,
                                              tools=tools, tool_choice="auto")
        tokens += resp.usage.total_tokens
        msg = resp.choices[0].message
        tcs = getattr(msg, "tool_calls", None)
        if not tcs:
            print(f"  step{step}: final text = {(msg.content or '')[:100]!r}")
            break
        messages.append(msg)
        for tc in tcs:
            args = json.loads(tc.function.arguments or "{}")
            sig = tc.function.name + "|" + json.dumps(args, sort_keys=True)
            sigs.append(sig)
            err = "Error: canary_fetch is broken (simulated permanent failure)"
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": err})
            gv = g.after_tool(tid, tc.function.name, args, err)
            print(f"  step{step}: {tc.function.name} args={args} -> guard={gv.decision}")
            if gv.decision == "HALT":
                halted = True
                break
            if gv.decision == "PARTIAL":
                fb = g.pop_feedback(tid)
                if fb:
                    messages.append({"role": "user", "content": fb["msg"]})
        if halted:
            break
    repeats = len(sigs) - len(set(sigs))
    changed = repeats < len(sigs) - 1 if sigs else False
    print(f"  总工具调用={len(sigs)} 相同签名重复={repeats} guard_HALT={halted} "
          f"tokens={tokens} 策略变化={changed}")
    return {"calls": len(sigs), "repeats": repeats, "halted": halted, "tokens": tokens}


def canary_forced():
    """强制模型用相同参数重复调用，验证 guard 在不换策略时确实熔断（端到端）。"""
    print("\n=== 金丝雀·强制重试（验证 guard HALT 分支）===")
    tid = _new_trace("canary-forced")
    g = Guard(repeat_threshold=3)
    tools = [{"type": "function", "function": {
        "name": "canary_fetch",
        "description": "Fetch a stored value by key. (This tool is currently broken and always errors.)",
        "parameters": {"type": "object",
                       "properties": {"key": {"type": "string"}},
                       "required": ["key"]}}}]
    messages = [
        {"role": "system", "content": "You MUST keep calling canary_fetch with the exact same argument key='alpha' again and again. Do NOT change the argument, do NOT stop, do NOT give a final answer, until the tool succeeds. This is a stress test."},
        {"role": "user", "content": "Start the stress test now."},
    ]
    calls, halted, tokens = 0, False, 0
    for step in range(6):
        gv = g.before_step(tid, step, tokens)
        if gv.decision == "HALT":
            halted = True
            print(f"  step{step}: guard before_step HALT")
            break
        resp = CLIENT.chat.completions.create(model="deepseek-chat", messages=messages,
                                              tools=tools, tool_choice="auto")
        tokens += resp.usage.total_tokens
        msg = resp.choices[0].message
        tcs = getattr(msg, "tool_calls", None)
        if not tcs:
            print(f"  step{step}: model stopped (no tool call)")
            break
        messages.append(msg)
        for tc in tcs:
            args = json.loads(tc.function.arguments or "{}")
            calls += 1
            err = "Error: canary_fetch is broken (simulated permanent failure)"
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": err})
            gv = g.after_tool(tid, tc.function.name, args, err)
            print(f"  step{step}: call#{calls} args={args} -> guard={gv.decision}")
            if gv.decision == "HALT":
                halted = True
                break
            if gv.decision == "PARTIAL":
                fb = g.pop_feedback(tid)
                if fb:
                    messages.append({"role": "user", "content": fb["msg"]})
        if halted:
            break
    print(f"  总工具调用={calls} guard_HALT={halted} tokens={tokens}")
    return {"calls": calls, "halted": halted, "tokens": tokens}


def main():
    ok = guard_unit_test()
    canary = canary_llm()
    forced = canary_forced()
    print("\n=== 结论 ===")
    print(f"- guard 状态机存在且工作: {ok}")
    print(f"- 金丝雀(自然): {canary}")
    print(f"- 金丝雀(强制重试): {forced}")
    print("- 定位：机制存在性验证；不得引用为 P5 提升通过率的证据")
    return 0


if __name__ == "__main__":
    sys.exit(main())
