"""评判翻译（P5a 5a.3 / P5a.20 便签1）：τ evaluator reward → simple-agent V 层。

- db 终态 hash 比对 → assertion `db_final_state`（blocker）
- outputs/动作序列检查 → assertion `actions_match`（blocker）

P5a.20 便签1：额外把 GT-vs-final **字段级 diff**（data_diff / actions_diff / outputs /
双方 hash）写入 acceptance_check 与 verdict span，使 FAIL 归因不再靠人工推断。

loss = 1 - reward；reward 由 sidecar 的 StubUser 注桩 replay 计算（零 LLM）。
红线：diff 只含 DB 层 GT（动作/字段），不含 hidden instruction。
"""
from monitor.collector import add_event

_DIFF_KEYS = ("r_actions", "r_outputs", "gt_data_hash", "agent_data_hash",
              "data_diff", "actions_diff", "outputs")


def _assertions_from_info(reward, info):
    info = info if isinstance(info, dict) else {}
    checks = []
    if "r_actions" in info:
        checks.append(("db_final_state", bool(info.get("r_actions"))))
    if "r_outputs" in info and info.get("r_outputs") is not None:
        checks.append(("actions_match", bool(info.get("r_outputs"))))
    if not checks:
        checks.append(("db_final_state", float(reward) == 1.0))
    return checks


def _diff_fields(info):
    return {k: info.get(k) for k in _DIFF_KEYS if k in info}


def score_tau_episode(trace_id, reward, info=None, parent_span_id=None):
    reward = float(reward)
    info = info if isinstance(info, dict) else {}
    checks = _assertions_from_info(reward, info)
    extra = _diff_fields(info)
    for name, passed in checks:
        attrs = {"name": name, "passed": bool(passed), "severity": "blocker", "source": "tau"}
        attrs.update(extra)
        add_event(
            trace_id=trace_id, name=name, layer="V",
            span_type="acceptance_check", parent_span_id=parent_span_id,
            attributes=attrs,
        )
    loss = round(1.0 - reward, 4)
    decision = "PASS" if loss == 0 else "FAIL"
    failed = [n for n, p in checks if not p]
    add_event(
        trace_id=trace_id, name="V层判决", layer="V", span_type="verdict",
        parent_span_id=parent_span_id,
        attributes={
            "decision": decision, "loss": loss, "reward": reward,
            "failed": failed, "source": "tau", **extra,
        },
    )
    return {"loss": loss, "decision": decision, "reward": reward, "failed": failed}
