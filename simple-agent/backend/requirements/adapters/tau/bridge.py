"""τ-bench sidecar 客户端 + 工具桥（P5a 5a.2）。

- SidecarClient：对 127.0.0.1:8010 的 JSON-RPC 客户端；
- ToolBridge：把 sidecar 的 τ 工具动态注册为 simple-agent 工具（`tau__<name>`），
  per-session 生命周期，episode 结束注销。

sidecar 不可达 → 工具调用立即返回结构化错误，绝不 hang 住 worker 循环。
"""
import json
import urllib.request


class SidecarError(RuntimeError):
    pass


class SidecarClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 8010, timeout: float = 30):
        self.url = f"http://{host}:{port}/"
        self.timeout = timeout

    def call(self, method: str, params: dict = None):
        data = json.dumps({"method": method, "params": params or {}}).encode("utf-8")
        req = urllib.request.Request(
            self.url, data=data, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                obj = json.loads(resp.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            raise SidecarError(f"sidecar unreachable: {type(e).__name__}: {e}")
        if "error" in obj:
            raise SidecarError(obj["error"])
        return obj["result"]

    def health(self):
        return self.call("health")

    def reset(self, env_name: str, task_id: int, task_split: str = "test") -> str:
        return self.call("reset", {
            "env_name": env_name, "task_id": task_id, "task_split": task_split,
        })["session_id"]

    def step(self, session_id: str, name: str, kwargs: dict):
        return self.call("step", {
            "session_id": session_id,
            "action": {"name": name, "kwargs": kwargs or {}},
        })

    def provide_user_msg(self, session_id: str, text: str):
        return self.call("provide_user_msg", {"session_id": session_id, "text": text})

    def reward(self, session_id: str):
        return self.call("reward", {"session_id": session_id})

    def list_tools(self, session_id: str):
        return self.call("list_tools", {"session_id": session_id})["tools"]

    def get_instruction(self, session_id: str) -> str:
        return self.call("get_instruction", {"session_id": session_id})["instruction"]

    def get_wiki(self, session_id: str) -> str:
        return self.call("get_wiki", {"session_id": session_id})["wiki"]

    def list_tasks(self, env_name: str, task_split: str = "test"):
        return self.call("list_tasks", {
            "env_name": env_name, "task_split": task_split,
        })

    def task_bucket(self, env_name: str, task_id: int, task_split: str = "test") -> str:
        return self.call("task_bucket", {
            "env_name": env_name, "task_id": task_id, "task_split": task_split,
        })["bucket"]

    def end(self, session_id: str):
        return self.call("end", {"session_id": session_id})


class ToolBridge:
    """per-session τ 工具注册/注销 + 调用转发。"""

    def __init__(self, client: SidecarClient, registry):
        self.client = client
        self.registry = registry
        self.session_id = None
        self.registered = []
        # last step result from a tool call (for env.done / reward)
        self.last_done = False
        self.last_reward = 0.0
        self.last_observation = ""
        self.last_error = ""

    def register(self, session_id: str):
        self.session_id = session_id
        tools = self.client.list_tools(session_id)
        for tool in tools:
            fname = tool["function"]["name"]
            name = f"tau__{fname}"
            schema = json.loads(json.dumps(tool))
            schema["function"]["name"] = name
            self.registry.register(
                name=name, schema=schema, func=self._forwarder(fname)
            )
            self.registered.append(name)
        return list(self.registered)

    def _forwarder(self, fname: str):
        def forward(**kwargs):
            args = {k: v for k, v in kwargs.items()
                    if k not in ("work_dir", "trace_id", "parent_span_id")}
            try:
                res = self.client.step(self.session_id, fname, args)
            except SidecarError as e:
                self.last_error = str(e)
                self.last_done = False
                raise RuntimeError(f"[tau] sidecar error on {fname}: {e}")
            if res.get("status") == "WAITING_FOR_USER":
                # real tools never wait; treat defensively
                self.last_observation = ""
                return ""
            self.last_done = bool(res.get("done"))
            self.last_reward = float(res.get("reward") or 0.0)
            self.last_observation = res.get("observation", "")
            return self.last_observation
        return forward

    def unregister(self):
        for name in self.registered:
            self.registry._tools.pop(name, None)
            self.registry._schemas.pop(name, None)
        self.registered = []

    def tool_names(self):
        return list(self.registered)
