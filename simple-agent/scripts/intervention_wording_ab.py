#!/usr/bin/env python3
"""P5a.70 §三：干预语义文案变体校准（A/B，≤0.1M 硬顶，temp=0，金丝雀化）。
测"否决消息措辞是否让模型一次听懂并改对"（点火≠救场的显性变量）。
  /root/miniconda3/envs/mini-agent/bin/python scripts/intervention_wording_ab.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
R = os.path.join(ROOT, ".agent", "reports")
CANARY = "CANARY_IW_2c81"

_env = {}
with open(os.path.join(BACKEND, ".env"), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1); _env[k.strip()] = v.strip()
from openai import OpenAI  # noqa: E402
CLI = OpenAI(api_key=_env["DEEPSEEK_API_KEY"],
             base_url=_env.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"))
MODEL = os.getenv("MODEL_NAME", "deepseek-chat")

VARIANTS = {
    "V1_current": "INTERCEPTED：若本订单还需改地址，先地址后物品；若无需改地址，重新发起本调用即可通过。",
    "V2_imperative": "STOP：请先调用 modify_pending_order_address，然后重新发起本调用。",
    "V3_structured": "INTERCEPTED{action_required=modify_pending_order_address; then_retry=modify_pending_order_items}",
}

SCHEMA = [
    {"type": "function", "function": {"name": "modify_pending_order_items",
     "description": "Change items of a pending order.",
     "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "modify_pending_order_address",
     "description": "Change the shipping address of a pending order.",
     "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}}}}},
]


def run_variant(msg):
    calls = []

    def items(order_id=None):
        return msg                     # 拦截消息（合成否决）
    def address(order_id=None):
        return "OK: address updated"

    impl = {"modify_pending_order_items": items, "modify_pending_order_address": address}
    messages = [
        {"role": "system", "content": "You are an order agent. Follow interception guidance exactly. "
                                      f"[marker:{CANARY}]"},
        {"role": "user", "content": "Change the item on order #W1 to red, and update its shipping "
                                    "address to 921 Park Ave, Chicago."},
    ]
    for _ in range(6):
        r = CLI.chat.completions.create(model=MODEL, temperature=0, messages=messages,
                                        tools=SCHEMA, tool_choice="auto")
        m = r.choices[0].message
        if not m.tool_calls:
            break
        messages.append({"role": "assistant", "content": m.content or "", "tool_calls": m.tool_calls})
        for tc in m.tool_calls:
            nm = tc.function.name
            calls.append(nm)
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": impl[nm](**(json.loads(tc.function.arguments or "{}")))})
    # comprehension：拦截(items)之后，下一个工具须是 address
    comp = False
    for i, nm in enumerate(calls):
        if nm == "modify_pending_order_items":
            comp = (i + 1 < len(calls) and calls[i + 1] == "modify_pending_order_address")
            break
    leak = CANARY in json.dumps(calls)
    return {"calls": calls, "comprehension": comp, "canary_leak": leak}


def main():
    rows = {v: run_variant(m) for v, m in VARIANTS.items()}
    comp = {v: rows[v]["comprehension"] for v in VARIANTS}
    leak = any(rows[v]["canary_leak"] for v in VARIANTS)
    out = {"detector_id": "intervention_wording_ab", "version": "iw-20261014",
           "note": "P5a.70 ③ 干预语义文案变体校准（金丝雀化，temp=0）",
           "results": rows, "comprehension": comp,
           "best": [v for v in VARIANTS if comp[v]] or None,
           "canary_leak": leak}
    json.dump(out, open(os.path.join(R, "intervention-wording-ab.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
