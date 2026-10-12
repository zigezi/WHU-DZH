"""L1.5 负先例仪器（P5a.47 §三.4 / P5a.54）：失败轨迹 → **警告通道**（域无关，独立于注入层）。

- 与 L1（正向先例）/注入层**隔离**：负先例不注入运行，只累积为"规避已知死法"的教具与谓词素材；
- 每条 = {req_id, death_cause, verdict, epoch, plan(工具序列), tokens}；
- 死因可由 failure-mine 模式（ERR::*/REPEAT::*/LOCK_ORDER::*）或 verdict 归类。
"""
import json
from typing import List, Optional

from .trace_store import trace_store


def add(req_id: str, death_cause: str, verdict: str, epoch: Optional[int],
        plan: list, tokens: int = 0, created_at: str = None) -> None:
    trace_store.conn.execute(
        "INSERT INTO negative_precedents"
        " (req_id, death_cause, verdict, epoch, plan_json, tokens, created_at)"
        " VALUES (?,?,?,?,?,?,?)",
        (req_id, death_cause, verdict, epoch,
         json.dumps(plan or [], ensure_ascii=False), tokens,
         trace_store._to_iso(created_at) if created_at else None),
    )
    trace_store.conn.commit()


def list_all(limit: int = 1000) -> List[dict]:
    rows = trace_store.conn.execute(
        "SELECT id, req_id, death_cause, verdict, epoch, plan_json, tokens, created_at"
        " FROM negative_precedents ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    out = []
    for r in rows:
        try:
            plan = json.loads(r[5]) if r[5] else []
        except Exception:  # noqa: BLE001
            plan = []
        out.append({"id": r[0], "req_id": r[1], "death_cause": r[2], "verdict": r[3],
                    "epoch": r[4], "plan": plan, "tokens": r[6], "created_at": r[7]})
    return out


def count_by_cause() -> dict:
    rows = trace_store.conn.execute(
        "SELECT death_cause, count(*) FROM negative_precedents GROUP BY death_cause").fetchall()
    return {r[0]: r[1] for r in rows}
