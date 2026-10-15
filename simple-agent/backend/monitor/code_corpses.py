"""P5a.62 §四 / P5a.63 §四：代码域尸体采集（零 token）。

把操作者（opencode 自身）的代码操作日志 → 死亡事件 → ring_mine 输入。
不做谓词、不做裁决；只采集尸体（域转移：器官机器整体复用，谓词须从代码域尸体重新出生）。
"""
from typing import List, Optional

from .trace_store import trace_store


def classify(op: str, exit_code: int, error: str) -> Optional[str]:
    """代码域死亡分类（种子，待尸体确认）。返回 None = 非死亡。"""
    e = (error or "").lower()
    if exit_code == 0 and not e:
        return None
    if "syntaxerror" in e or "indentationerror" in e:
        return "syntax_death"
    if "modulenotfound" in e or "importerror" in e:
        return "env_missing"
    if "timeout" in e:
        return "timeout_loop"
    if "assert" in e or "test" in (op or "").lower() or exit_code != 0:
        return "test_or_build_fail"
    return "op_fail"


def add(ts: str, op: str, command: str, exit_code: int, error: str,
        source: str = "real", capture: str = "live") -> Optional[int]:
    dc = classify(op, exit_code, error)
    if dc is None:
        return None
    trace_store.conn.execute(
        "INSERT INTO code_corpses (ts, op, command, exit_code, error, death_class, source, capture)"
        " VALUES (?,?,?,?,?,?,?,?)", (ts, op, command, exit_code, error, dc, source, capture))
    trace_store.conn.commit()
    return dc


def list_all(limit: int = 1000, source: str = None) -> List[dict]:
    q = ("SELECT id, ts, op, command, exit_code, error, death_class, source, capture"
         " FROM code_corpses")
    params: tuple = ()
    if source:
        q += " WHERE source = ?"
        params = (source,)
    q += " ORDER BY id DESC LIMIT ?"
    params = params + (limit,)
    rows = trace_store.conn.execute(q, params).fetchall()
    return [{"id": r[0], "ts": r[1], "op": r[2], "command": r[3], "exit_code": r[4],
             "error": r[5], "death_class": r[6], "source": r[7], "capture": r[8]} for r in rows]


def real_count() -> int:
    return len(list_all(limit=100000, source="real"))


def real_classes() -> List[str]:
    return sorted({c["death_class"] for c in list_all(limit=100000, source="real")})


def set_source(corpse_id: int, source: str, capture: str = None) -> None:
    """洁池：标注/隔离来源（P5a.79 §二.1）。"""
    if capture is None:
        trace_store.conn.execute("UPDATE code_corpses SET source=? WHERE id=?", (source, corpse_id))
    else:
        trace_store.conn.execute("UPDATE code_corpses SET source=?, capture=? WHERE id=?",
                                 (source, capture, corpse_id))
    trace_store.conn.commit()


def mine_input() -> List[dict]:
    """产出 ring_mine 可消化的模式（只计 source=real）；按 death_class 聚合。"""
    rows = trace_store.conn.execute(
        "SELECT death_class, count(*) FROM code_corpses WHERE source='real'"
        " GROUP BY death_class").fetchall()
    return [{"kind": "code_" + r[0], "pattern_id": "CODE::" + r[0], "occurrences": r[1]} for r in rows]
