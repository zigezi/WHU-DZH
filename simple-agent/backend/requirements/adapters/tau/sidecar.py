#!/usr/bin/env python3
"""τ-bench sidecar (P5a v1.4).

Runs inside the isolated tau venv (`.agent/venv/tau/`), binds 127.0.0.1:8010.
JSON-RPC over HTTP. **Zero LLM calls**: the env's user simulator is replaced by
`QueueUser` (raises `WaitingForUser`) or `StubUser` (replay).

Methods: reset / step / provide_user_msg / reward / list_tools /
         get_instruction / get_wiki / end / health
"""
import json
import os
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# allow running as a bare script from the repo root
_ADAPTER_DIR = os.path.dirname(os.path.abspath(__file__))
if _ADAPTER_DIR not in sys.path:
    sys.path.insert(0, _ADAPTER_DIR)

from tau_bench.envs.user import UserStrategy  # noqa: E402
from tau_bench.types import Action  # noqa: E402

HOST = os.environ.get("TAU_SIDECAR_HOST", "127.0.0.1")
PORT = int(os.environ.get("TAU_SIDECAR_PORT", "8010"))


class WaitingForUser(Exception):
    """Non-blocking sentinel: RESPOND action needs a user message from the driver."""


class QueueUser:
    """Non-LLM user: raises on step so sidecar returns WAITING_FOR_USER."""

    def __init__(self):
        self.instruction = None
        self.pending = None

    def reset(self, instruction=None):
        self.instruction = instruction
        self.pending = None
        return ""

    def step(self, content):
        raise WaitingForUser()

    def get_total_cost(self):
        return 0.0


class StubUser:
    """Replay stub: fixed ###STOP###, zero LLM."""

    def reset(self, instruction=None):
        return "###STOP###"

    def step(self, content):
        return "###STOP###"

    def get_total_cost(self):
        return 0.0


_SESSIONS = {}
_LOCK = threading.RLock()


def _make_env(env_name, task_split, task_index):
    if env_name == "airline":
        from tau_bench.envs.airline.env import MockAirlineDomainEnv as EnvCls
    elif env_name == "retail":
        from tau_bench.envs.retail.env import MockRetailDomainEnv as EnvCls
    else:
        raise ValueError(f"unknown env: {env_name}")
    # HUMAN strategy avoids any LLM construction; we overwrite user right after.
    env = EnvCls(
        user_strategy=UserStrategy.HUMAN,
        user_model="n/a",
        user_provider=None,
        task_split=task_split,
        task_index=task_index,
    )
    env.user = QueueUser()
    return env


# --------------------------------------------------------------------------- #
# RPC methods
# --------------------------------------------------------------------------- #
def rpc_reset(params):
    env_name = params["env_name"]
    task_id = int(params.get("task_id", 0))
    task_split = params.get("task_split", "test")
    env = _make_env(env_name, task_split, task_id)
    env.reset(task_index=task_id)
    sid = str(uuid.uuid4())
    with _LOCK:
        _SESSIONS[sid] = env
    return {"session_id": sid, "env_name": env_name, "task_id": task_id}


def rpc_step(params):
    sid = params["session_id"]
    action = params["action"]
    with _LOCK:
        env = _SESSIONS.get(sid)
    if env is None:
        raise KeyError(f"unknown session: {sid}")
    act = Action(name=action["name"], kwargs=action.get("kwargs", {}))
    try:
        resp = env.step(act)
    except WaitingForUser:
        # RESPOND already appended to env.actions; driver supplies the user message
        return {"status": "WAITING_FOR_USER"}
    return {
        "observation": resp.observation,
        "done": bool(resp.done),
        "reward": float(resp.reward),
    }


def rpc_provide_user_msg(params):
    sid = params["session_id"]
    text = params.get("text", "")
    with _LOCK:
        env = _SESSIONS.get(sid)
    if env is None:
        raise KeyError(f"unknown session: {sid}")
    user = env.user
    if hasattr(user, "pending"):
        user.pending = text
    return {"ok": True}


def rpc_reward(params):
    sid = params["session_id"]
    with _LOCK:
        env = _SESSIONS.get(sid)
    if env is None:
        raise KeyError(f"unknown session: {sid}")
    orig_user = env.user
    env.user = StubUser()  # zero-LLM replay
    try:
        res = env.calculate_reward()
    finally:
        env.user = orig_user
    info = res.info.model_dump() if hasattr(res.info, "model_dump") else str(res.info)
    return {"reward": float(res.reward), "info": info}


def rpc_list_tools(params):
    sid = params["session_id"]
    with _LOCK:
        env = _SESSIONS.get(sid)
    if env is None:
        raise KeyError(f"unknown session: {sid}")
    return {"tools": env.tools_info}


def rpc_get_instruction(params):
    sid = params["session_id"]
    with _LOCK:
        env = _SESSIONS.get(sid)
    if env is None:
        raise KeyError(f"unknown session: {sid}")
    return {"instruction": env.task.instruction}


def rpc_get_wiki(params):
    sid = params["session_id"]
    with _LOCK:
        env = _SESSIONS.get(sid)
    if env is None:
        raise KeyError(f"unknown session: {sid}")
    return {"wiki": env.wiki}


def rpc_get_gt_actions(params):
    """调试/验收用：返回该 task 的 ground-truth actions（用于 GT replay 完美 episode）。"""
    sid = params["session_id"]
    with _LOCK:
        env = _SESSIONS.get(sid)
    if env is None:
        raise KeyError(f"unknown session: {sid}")
    actions = [{"name": a.name, "kwargs": a.kwargs} for a in env.task.actions]
    return {"actions": actions}


def rpc_end(params):
    sid = params.get("session_id")
    with _LOCK:
        _SESSIONS.pop(sid, None)
    return {"ok": True}


def rpc_health(params):
    return {"status": "ok", "sessions": len(_SESSIONS)}


def rpc_list_tasks(params):
    """枚举某 env 某 split 的全部任务元数据（供 ingest 用）。不返回完整 hidden instruction。"""
    env_name = params["env_name"]
    task_split = params.get("task_split", "test")
    env = _make_env(env_name, task_split, 0)
    tasks = []
    for i, t in enumerate(env.tasks):
        tasks.append({
            "id": i,
            "instruction": t.instruction,
            "actions": [a.name for a in t.actions],
            "num_actions": len(t.actions),
            "num_outputs": len(t.outputs),
        })
    return {"env_name": env_name, "task_split": task_split,
            "count": len(tasks), "tasks": tasks}


def rpc_task_bucket(params):
    """判定任务的 GT 是否改变 db 终态：state-changing / read-only（P5a.6 补丁3）。"""
    env_name = params["env_name"]
    task_split = params.get("task_split", "test")
    task_id = int(params["task_id"])
    env = _make_env(env_name, task_split, task_id)
    env.reset(task_index=task_id)
    before = env.get_data_hash()
    orig_user = env.user
    env.user = StubUser()
    try:
        for a in env.task.actions:
            if a.name in env.terminate_tools:
                continue
            try:
                env.step(a)
            except Exception:  # noqa: BLE001
                pass
    finally:
        env.user = orig_user
    after = env.get_data_hash()
    return {"bucket": "state-changing" if before != after else "read-only"}


METHODS = {
    "reset": rpc_reset,
    "step": rpc_step,
    "provide_user_msg": rpc_provide_user_msg,
    "reward": rpc_reward,
    "list_tools": rpc_list_tools,
    "get_instruction": rpc_get_instruction,
    "get_wiki": rpc_get_wiki,
    "get_gt_actions": rpc_get_gt_actions,
    "end": rpc_end,
    "health": rpc_health,
    "list_tasks": rpc_list_tasks,
    "task_bucket": rpc_task_bucket,
}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/health") or self.path == "/":
            self._send(200, rpc_health({}))
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            req = json.loads(raw or b"{}")
            method = req.get("method")
            params = req.get("params", {})
            fn = METHODS.get(method)
            if fn is None:
                raise ValueError(f"unknown method: {method}")
            self._send(200, {"result": fn(params)})
        except Exception as e:  # noqa: BLE001
            self._send(200, {"error": f"{type(e).__name__}: {e}"})

    def log_message(self, *args):
        pass


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[tau-sidecar] listening on http://{HOST}:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
