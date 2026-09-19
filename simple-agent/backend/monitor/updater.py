#!/usr/bin/env python3
"""P4.3 更新器（数据更新包，不动代码）。

读 epoch 报告中 loss>0 的需求 → 调现有 diagnosis.shapley_diagnosis 归因 →
产出 .agent/proposals/epoch-{N}-proposal.json。

v1 铁律：本文件只生成提案，由人工审阅后手动应用。
"""
import argparse
import json
import os
import sys
from datetime import datetime

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from monitor.trace_store import trace_store  # noqa: E402
from monitor.diagnosis import shapley_diagnosis  # noqa: E402

ROOT = os.path.dirname(BACKEND_DIR)
PROPOSAL_DIR = os.path.join(ROOT, ".agent", "proposals")

TYPE_BY_LAYER = {
    "G": "threshold_patch",
    "T": "threshold_patch",
    "E": "threshold_patch",
    "V": "precedent_update",
    "C": "prompt_hint",
    "L": "prompt_hint",
    "O": "prompt_hint",
}


def _target(layer, req_id):
    if layer == "G":
        return "monitor/guard.py:repeat_threshold"
    if layer == "V":
        return f"requirements#{req_id}"
    if layer == "C":
        return "SYSTEM_PROMPT"
    if layer:
        return f"monitor/{layer.lower()}layer"
    return "unknown"


def build_proposals(report: dict):
    proposals = []
    for entry in report.get("entries", []):
        if not entry.get("loss"):
            continue
        trace = None
        if entry.get("task_id"):
            trace = trace_store.get_trace(entry["task_id"])
        if trace is None:
            continue
        diagnosis = shapley_diagnosis.get_root_cause(trace)
        layer = diagnosis.get("root_cause_layer")
        span_ids = [e.get("span_id") for e in diagnosis.get("evidence", [])
                    if e.get("span_id")]
        span_ids += [s for s in diagnosis.get("root_cause_span_ids", []) if s]
        span_ids = list(dict.fromkeys(span_ids))
        proposals.append({
            "type": TYPE_BY_LAYER.get(layer, "prompt_hint"),
            "target": _target(layer, entry["req_id"]),
            "root_cause_layer": layer,
            "evidence": [entry["task_id"]] + span_ids + [
                a["rule_id"] for a in diagnosis.get("anomalies", [])
            ],
            "span_ids": span_ids,
            "suggested_value": None,
            "confidence": round((diagnosis.get("confidence") or 0) / 100, 4),
            "req_id": entry["req_id"],
            "loss": entry["loss"],
        })
    return proposals


def generate(report_path: str) -> str:
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    proposals = build_proposals(report)
    epoch = report.get("epoch")
    cost = {
        "updater_llm_tokens": 0,
        "note": "updater 使用确定性 Shapley 归因（anomaly 规则 + 边际贡献），无 LLM 调用，token 消耗为 0",
        "budget_cny": 10.0,
        "spent_cny": 0.0,
    }
    package = {
        "epoch": epoch,
        "generated_at": datetime.now().isoformat(),
        "note": "v1：仅生成提案，需人工审阅后手动应用并单独 commit",
        "source_report": os.path.basename(report_path),
        "cost": cost,
        "proposals": proposals,
    }
    os.makedirs(PROPOSAL_DIR, exist_ok=True)
    out = os.path.join(PROPOSAL_DIR, f"epoch-{epoch}-proposal.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(package, f, ensure_ascii=False, indent=2)

    # 记入 spans：updater 自身运行记录（tokens=0）
    try:
        import time as _time
        from monitor.schema import Trace
        from monitor.collector import add_event
        utid = f"updater-epoch-{epoch}"
        trace_store.add_trace(Trace(
            trace_id=utid, task_id=utid,
            task_content=f"updater run epoch {epoch}",
            start_time=_time.time(), status="success",
        ))
        add_event(
            trace_id=utid, name="updater运行", layer="O",
            span_type="updater_run",
            attributes={"updater_llm_tokens": 0, "proposals": len(proposals),
                        "budget_cny": 10.0, "spent_cny": 0.0},
        )
    except Exception:  # noqa: BLE001
        pass

    print(f"[updater] {len(proposals)} proposals -> {out} (tokens=0, spent=¥0.00/¥10)")
    return out


def main():
    parser = argparse.ArgumentParser(description="epoch proposal updater")
    parser.add_argument("report", help="path to epoch-{N}.json")
    args = parser.parse_args()
    generate(args.report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
