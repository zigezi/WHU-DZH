"""P5a.66 §二.1 / B-1（MR-8 旧债）：真实环境指纹。

原 `env_fingerprint()` = 请求别名 `deepseek-chat`（非真实响应模型）→ 后验为**错误身份学习**。
改为**响应模型 + system_fingerprint** 复合键（观测自真实响应；未观测时回退别名）。
"""

_state = {"model": None, "system_fingerprint": None}


def observe(resp) -> None:
    """从 LLM 响应中记录真实模型 + system_fingerprint。"""
    try:
        m = getattr(resp, "model", None)
        sf = getattr(resp, "system_fingerprint", None)
        if m:
            _state["model"] = m
        if sf:
            _state["system_fingerprint"] = sf
    except Exception:  # noqa: BLE001
        pass


def fingerprint(fallback: str = "unknown") -> str:
    m, sf = _state["model"], _state["system_fingerprint"]
    if m and sf:
        return f"{m}|{sf}"
    return m or fallback


def snapshot() -> dict:
    return dict(_state)
