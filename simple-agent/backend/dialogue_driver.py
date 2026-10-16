"""DialogueDriver（P5a 5a.1）：把 simple-agent worker 从"单指令循环"升级为"可被对话驱动"。

- UserSimulator：worker 侧自写用户模拟器（openai 兼容 client，DeepSeek），
  包装 hidden instruction，逐轮生成用户话；**不复用 τ 的 load_user（依赖 litellm）**。
- DialogueDriver：管理 sidecar session、工具桥、wiki、turn0，以及 RESPOND 续聊。
"""
import hashlib
import os
from typing import Optional

from requirements.adapters.tau.bridge import SidecarClient, ToolBridge
from tools.registry import ToolRegistry

MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-chat")
WORK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workspace"))

# P5a.10 §三：POLICY v1 定稿（P1 修正版 + P2 + P4 + P5；P3 作废）
POLICY_VERSION = "worker-policy-v1"
POLICY_TEXT = """[WORKER-OWN POLICY v1 — system-owned, not eval asset]
1. Confirm-and-act in one turn: when you call a tool, state the key parameters you are acting on in the SAME assistant message that carries the tool call. Do NOT spend a whole turn on a text-only confirmation — a text-only turn is delivered to the user and wastes a turn.
2. Never fabricate: use only information provided by the user or returned by tools. If something is unknown, ask or say you do not have it.
3. Stop when done: once the goal is achieved, conclude. Do not take extra unrelated actions.
4. Change strategy on repeated failure: if a tool keeps failing, change arguments or approach instead of retrying identically.
[/WORKER-OWN POLICY]"""


def build_user_system_prompt(instruction: str) -> str:
    """镜像 τ-bench LLMUserSimulationEnv.build_system_prompt（对齐官方行为）。"""
    return f"""You are a user interacting with an agent.

Instruction: {instruction}

Rules:
- Just generate one line at a time to simulate the user's message.
- Do not give away all the instruction at once. Only provide the information that is necessary for the current step.
- Do not hallucinate information that is not provided in the instruction. For example, if the agent asks for the order id but it is not mentioned in the instruction, do not make up an order id, just say you do not remember or have it.
- If the instruction goal is satisified, generate '###STOP###' as a standalone message without anything else to end the conversation.
- Do not repeat the exact instruction in the conversation. Instead, use your own words to convey the same information.
- Try to make the conversation as natural as possible, and stick to the personalities in the instruction."""


class UserSimulator:
    def __init__(self, instruction: str, client, model: str = MODEL_NAME):
        self.client = client
        self.model = model
        self.total_tokens = 0
        self.messages = [
            {"role": "system", "content": build_user_system_prompt(instruction)},
            {"role": "user", "content": "Hi! How can I help you today?"},
        ]

    def add_agent_message(self, text: str):
        self.messages.append({"role": "user", "content": text})

    def next_message(self) -> str:
        resp = self.client.chat.completions.create(
            model=self.model, messages=self.messages
        )
        msg = resp.choices[0].message.content or ""
        self.messages.append({"role": "assistant", "content": msg})
        self.total_tokens += getattr(resp.usage, "total_tokens", 0) or 0
        return msg


class DialogueDriver:
    """τ 模式下的对话编排器。"""

    def __init__(self, req, trace_id: str, tau_spec: dict, client,
                 task_span_id: str, add_event):
        self.req = req
        self.trace_id = trace_id
        self.tau_env = tau_spec["tau_env"]
        self.tau_task_id = int(tau_spec["tau_task_id"])
        self.tau_task_split = tau_spec.get("tau_task_split", "test")
        self.client = client
        self.task_span_id = task_span_id
        self.add_event = add_event

        self.sidecar = SidecarClient()
        self.registry = ToolRegistry(WORK_DIR)  # τ 专用：只有 tau__* 工具
        self.bridge = ToolBridge(self.sidecar, self.registry)

        self.session_id: Optional[str] = None
        self.simulator: Optional[UserSimulator] = None
        self.system_prompt: str = ""
        self.turn = 0
        self.stopped = False
        self.last_done = False
        self.last_reward = 0.0
        self.last_observation = ""

    # ------------------------------------------------------------------ #
    def _record_turn(self, role: str, text: str, tokens: int = 0):
        self.turn += 1
        self.add_event(
            trace_id=self.trace_id, name="对话回合", layer="L",
            span_type="dialogue_turn", parent_span_id=self.task_span_id,
            attributes={"turn": self.turn, "role": role, "tokens": tokens,
                        "text": (text or "")[:200]},
        )

    def start(self) -> str:
        """reset sidecar → 注册 tau__* → 取 instruction/wiki → 生成 turn 0 真实用户消息。"""
        self.session_id = self.sidecar.reset(
            self.tau_env, self.tau_task_id, self.tau_task_split
        )
        registered = self.bridge.register(self.session_id)
        instruction = self.sidecar.get_instruction(self.session_id)
        wiki = self.sidecar.get_wiki(self.session_id)
        # P5a.10 §一/§三：POLICY 段追加于 wiki 之后，wiki 逐字节不动
        policy_id = hashlib.md5(POLICY_TEXT.encode()).hexdigest()[:12]
        self.system_prompt = wiki + "\n\n" + POLICY_TEXT
        if not self.system_prompt.startswith(wiki):
            raise RuntimeError("[policy] wiki 段被改动，拒绝注入")
        self.add_event(
            trace_id=self.trace_id, name="策略注入", layer="L",
            span_type="policy_inject", parent_span_id=self.task_span_id,
            attributes={
                "policy_id": policy_id,
                "policy_version": POLICY_VERSION,
                "policy_chars": len(POLICY_TEXT),
                "wiki_sha256_16": hashlib.sha256(wiki.encode()).hexdigest()[:16],
            },
        )
        self.add_event(
            trace_id=self.trace_id, name="工具范围", layer="L",
            span_type="tool_scope", parent_span_id=self.task_span_id,
            attributes={"mode": "tau", "disabled": ["shell", "file_ops"],
                        "tau_tools": registered},
        )
        self.simulator = UserSimulator(instruction, self.client)
        first = self.simulator.next_message()
        self._record_turn("user", first, self.simulator.total_tokens)
        return first

    def on_respond(self, agent_text: str, tokens: int = 0) -> Optional[str]:
        """agent 纯文本回复 = RESPOND；返回下一句用户话，None = ###STOP###。"""
        self._record_turn("assistant", agent_text, tokens)
        # 把 RESPOND 记入 env.actions（sidecar 返回 WAITING_FOR_USER）
        self.sidecar.step(self.session_id, "respond", {"content": agent_text})
        self.simulator.add_agent_message(agent_text)
        nxt = self.simulator.next_message()
        if "###STOP###" in nxt:
            self.stopped = True
            self._record_turn("user", "###STOP###", self.simulator.total_tokens)
            return None
        self.sidecar.provide_user_msg(self.session_id, nxt)
        self._record_turn("user", nxt, self.simulator.total_tokens)
        return nxt

    def note_tool_step(self):
        """worker 每次执行完 tau 工具后调用，记录 env.done/reward。"""
        self.last_done = self.bridge.last_done
        self.last_reward = self.bridge.last_reward
        self.last_observation = self.bridge.last_observation

    def finish(self):
        """episode 结束：注销工具、关闭 session。返回 (reward, info)。"""
        reward, info = None, None
        try:
            r = self.sidecar.reward(self.session_id)
            reward, info = r.get("reward"), r.get("info")
        except Exception:  # noqa: BLE001
            pass
        try:
            self.sidecar.end(self.session_id)
        except Exception:  # noqa: BLE001
            pass
        self.bridge.unregister()
        return reward, info
