#!/usr/bin/env python3
"""P4.4 双门 merge + 早停。

判据：train loss 降 ≥5% 且 dev 集无 PASS→FAIL 退化 → MERGE，否则 REJECT。
连续 3 epoch 不改善 → 生成《收敛报告》。

用法：
  python scripts/epoch_gate.py prev.json curr.json
  python scripts/epoch_gate.py --history e1.json e2.json e3.json
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_DIR = os.path.join(ROOT, ".agent", "reports")


def load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _dev_map(report: dict) -> dict:
    return {e["req_id"]: e for e in report.get("entries", [])
            if e.get("split") == "dev"}


def dev_regressions(prev: dict, curr: dict):
    """返回从 PASS 退化为 FAIL 的 dev req_id 列表。"""
    prev_map, curr_map = _dev_map(prev), _dev_map(curr)
    regressions = []
    for req_id, p in prev_map.items():
        c = curr_map.get(req_id)
        if not c:
            continue
        prev_pass = (p.get("assertion_loss") or 0) == 0
        curr_fail = (c.get("assertion_loss") or 0) > 0
        if prev_pass and curr_fail:
            regressions.append(req_id)
    return regressions


def evaluate_gate(prev: dict, curr: dict) -> dict:
    prev_loss = prev.get("train_loss") or 0
    curr_loss = curr.get("train_loss") or 0
    improvement = (prev_loss - curr_loss) / prev_loss if prev_loss else 0.0
    train_ok = improvement >= 0.05
    regressions = dev_regressions(prev, curr)
    dev_ok = not regressions
    return {
        "decision": "MERGE" if (train_ok and dev_ok) else "REJECT",
        "improvement": round(improvement, 4),
        "train_ok": train_ok,
        "dev_ok": dev_ok,
        "dev_regressions": regressions,
        "prev_train_loss": prev_loss,
        "curr_train_loss": curr_loss,
    }


def check_convergence(history):
    """连续 3 个 epoch 的 train_loss 不再下降 → 收敛。"""
    if len(history) < 3:
        return None
    last3 = history[-3:]
    improved = any(
        (last3[i].get("train_loss") or 0) < (last3[i - 1].get("train_loss") or 0)
        for i in range(1, 3)
    )
    if improved:
        return None
    return {
        "message": "连续 3 epoch 未改善，进入收敛",
        "loss_curve": [r.get("train_loss") for r in history],
    }


def write_convergence(convergence: dict, history) -> str:
    os.makedirs(REPORT_DIR, exist_ok=True)
    path = os.path.join(REPORT_DIR, "convergence.md")
    lines = ["# 收敛报告", "", convergence["message"], "", "## loss 曲线", ""]
    for report in history:
        lines.append(f"- epoch {report.get('epoch')}: {report.get('train_loss')}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


def main():
    parser = argparse.ArgumentParser(description="epoch double gate")
    parser.add_argument("reports", nargs="+", help="两个（或更多）epoch json")
    parser.add_argument("--history", action="store_true",
                        help="把全部输入视为历史序列并检查早停")
    args = parser.parse_args()

    reports = [load(p) for p in args.reports]

    if args.history:
        convergence = check_convergence(reports)
        if convergence:
            path = write_convergence(convergence, reports)
            print(f"CONVERGED -> {path}")
        else:
            print("NOT_CONVERGED")
        return 0

    if len(reports) < 2:
        print("need at least two reports", file=sys.stderr)
        return 2

    result = evaluate_gate(reports[0], reports[1])
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
