"""评判翻译（P5a 5a.3）：τ evaluator reward → simple-agent V 层。

本版 τ evaluator 只有两类检查：
- db 终态 hash 比对 → assertion `db_final_state`（blocker）
- outputs/动作序列检查 → assertion `actions_match`（blocker）

loss = 1 - reward；reward 由 sidecar 的 StubUser 注桩 replay 计算（零 LLM）。
"""
from monitor.collector import add_event


def _assertions_from_info(reward, info):
    info = info or {}
    checks = []
    if "r_actions" in info:
        checks.append(("db_final_state", info.get("r_actions") == 1.0))
    if "r_outputs" in info:
        checks.append(("actions_match", info.get("r_outputs") == 1.0))
    if not checks:
        checks.append(("db_final_state", float(reward) == 1.0))
    return checks


def score_tau_episode(trace_id, reward, info=None, parent_span_id=None):
    reward = float(reward)
    checks = _assertions_from_info(reward, info)
    for name, passed in checks:
        add_event(
            trace_id=trace_id, name=name, layer="V",
            span_type="acceptance_check", parent_span_id=parent_span_id,
            attributes={
                "name": name, "passed": bool(passed), "severity": "blocker",
                "source": "tau",
            },
        )
    loss = round(1.0 - reward, 4)
    decision = "PASS" if loss == 0 else "FAIL"
    failed = [n for n, p in checks if not p]
    add_event(
        trace_id=trace_id, name="V层判决", layer="V", span_type="verdict",
        parent_span_id=parent_span_id,
        attributes={
            "decision": decision, "loss": loss, "reward": reward,
            "failed": failed, "source": "tau",
        },
    )
    return {"loss": loss, "decision": decision, "reward": reward, "failed": failed}
