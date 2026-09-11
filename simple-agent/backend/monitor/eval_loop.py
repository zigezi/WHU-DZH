#!/usr/bin/env python3
"""P4.1 epoch 评测器。

对 split=train 的全部需求依次 POST /task/submit 执行，全部完成后跑
vlayer.verdict，计算 epoch loss（Σ 加权失败 + 0.05×token/预算）；
同时对 dev 需求执行一遍用于回归门禁。输出
.agent/reports/epoch-{N}.json 与同名 markdown 摘要。

用法：cd backend && python monitor/eval_loop.py --epoch 1
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import requests  # noqa: E402

from requirements import loader  # noqa: E402
from monitor import vlayer  # noqa: E402

ROOT = os.path.dirname(BACKEND_DIR)
REPORT_DIR = os.path.join(ROOT, ".agent", "reports")
TERMINAL = {"success", "failed", "g_halted", "abstained"}
DEFAULT_BASE_URL = "http://localhost:8000"


def submit(base_url: str, content: str, req_id: str) -> str:
    resp = requests.post(
        f"{base_url}/task/submit",
        json={"content": content, "req_id": req_id},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["task_id"]


def wait_task(base_url: str, task_id: str, timeout_s: int) -> dict:
    deadline = time.time() + timeout_s
    last = {}
    while time.time() < deadline:
        try:
            last = requests.get(f"{base_url}/task/{task_id}", timeout=30).json()
        except Exception:
            time.sleep(2)
            continue
        if last.get("status") in TERMINAL:
            return last
        time.sleep(2)
    last.setdefault("status", "timeout")
    return last


def run_requirement(base_url: str, req: dict) -> dict:
    content = req["task"]  # v2.3：只允许用 task 字段喂模型，禁止 ears_text
    budget = req.get("budget") or {}
    entry = {
        "req_id": req["req_id"],
        "split": req.get("split"),
        "title": req.get("title"),
        "task": content,
        "status": None,
        "task_id": None,
        "assertion_loss": None,
        "loss": None,
        "tokens": 0,
        "failed": [],
    }
    try:
        task_id = submit(base_url, content, req["req_id"])
        entry["task_id"] = task_id
        task = wait_task(base_url, task_id, budget.get("timeout_s", 600) + 60)
        entry["status"] = task.get("status")
        entry["tokens"] = task.get("llm_tokens") or 0
        evaluated = vlayer.evaluate(req["req_id"], trace_id=task_id)
        assertion_loss = evaluated["loss"]
        entry["assertion_loss"] = assertion_loss
        entry["failed"] = [r.name for r in evaluated["results"] if not r.passed]
        token_ratio = entry["tokens"] / max(budget.get("max_tokens", 30000), 1)
        entry["loss"] = round(assertion_loss + 0.05 * token_ratio, 4)
    except Exception as e:  # noqa: BLE001
        entry["status"] = "error"
        entry["error"] = str(e)
        entry["loss"] = None
    return entry


def compute_epoch_loss(entries) -> float:
    return round(sum(e.get("loss") or 0 for e in entries if e["split"] == "train"), 4)


def build_report(epoch: int, base_url: str, entries) -> dict:
    return {
        "epoch": epoch,
        "generated_at": datetime.now().isoformat(),
        "base_url": base_url,
        "train_loss": compute_epoch_loss(entries),
        "entries": entries,
    }


def write_report(report: dict) -> str:
    os.makedirs(REPORT_DIR, exist_ok=True)
    json_path = os.path.join(REPORT_DIR, f"epoch-{report['epoch']}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    lines = [
        f"# Epoch {report['epoch']} 评测报告",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- train loss：{report['train_loss']}",
        "",
        "| req_id | split | status | assertion_loss | loss | tokens | failed |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in report["entries"]:
        lines.append(
            f"| {e['req_id']} | {e['split']} | {e['status']} | "
            f"{e['assertion_loss']} | {e['loss']} | {e['tokens']} | "
            f"{', '.join(e['failed']) or '-'} |"
        )
    md_path = os.path.join(REPORT_DIR, f"epoch-{report['epoch']}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return json_path


def run_epoch(epoch: int, base_url: str, limit: int = None) -> dict:
    reqs = loader.load_by_split("train") + loader.load_by_split("dev")
    if limit:
        reqs = reqs[:limit]
    entries = [run_requirement(base_url, req) for req in reqs]
    report = build_report(epoch, base_url, entries)
    path = write_report(report)
    print(f"[eval_loop] epoch={epoch} train_loss={report['train_loss']}")
    print(f"[eval_loop] report -> {path}")
    return report


def main():
    parser = argparse.ArgumentParser(description="epoch evaluator")
    parser.add_argument("--epoch", type=int, required=True)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--limit", type=int, default=None,
                        help="只跑前 N 条需求（调试用）")
    args = parser.parse_args()
    run_epoch(args.epoch, args.base_url, args.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
