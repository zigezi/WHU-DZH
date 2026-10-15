"""P5a.62 §四 / P5a.63 §四：代码域尸体采集（零 token）。

把操作者（opencode 自身）的代码操作日志 → 死亡事件 → ring_mine 输入。
不做谓词、不做裁决；只采集尸体（域转移：器官机器整体复用，谓词须从代码域尸体重新出生）。
"""
from typing import List, Optional

from .trace_store import trace_store

# P5a.80 §三：尸体 schema 版本（语境锚定；分析工具对缺字段旧条目按 unknown 处理）
SCHEMA_V = "cc-v2"
_GIT_HEAD = {"v": None}


def _git_head() -> str:
    if _GIT_HEAD["v"] is None:
        import os
        import subprocess
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        try:
            _GIT_HEAD["v"] = subprocess.run(
                ["git", "-C", root, "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=5).stdout.strip() or "unknown"
        except Exception:  # noqa: BLE001
            _GIT_HEAD["v"] = "unknown"
    return _GIT_HEAD["v"]


def _env_fingerprint() -> str:
    try:
        from .env_state import fingerprint
        return fingerprint()
    except Exception:  # noqa: BLE001
        return "unknown"



def classify(op: str, exit_code: int, error: str) -> Optional[str]:
    """代码域死亡分类（P5a.82 §三.6：废止"凡 rc!=0 即 test_or_build_fail"的一刀切）。
    信号死亡单独立类 signal_death；非特定错误 → op_fail（由采集口径决定入池/灰区）。"""
    e = (error or "").lower()
    if exit_code == 0 and not e:
        return None
    if exit_code == 124 or "timeout" in e:
        return "timeout_loop"
    if exit_code >= 128:
        return "signal_death"
    if "syntaxerror" in e or "indentationerror" in e:
        return "syntax_death"
    if "modulenotfound" in e or "importerror" in e:
        return "env_missing"
    if "assert" in e or "test" in (op or "").lower():
        return "test_or_build_fail"
    return "op_fail"


def add(ts: str, op: str, command: str, exit_code: int, error: str,
        source: str = "real", capture: str = "live",
        git_head: str = None, env_fingerprint: str = None, schema_v: str = None,
        death_class: str = None, tier: str = "live") -> Optional[int]:
    dc = death_class or classify(op, exit_code, error)
    if dc is None:
        return None
    trace_store.conn.execute(
        "INSERT INTO code_corpses"
        " (ts, op, command, exit_code, error, death_class, source, capture,"
        "  git_head, env_fingerprint, schema_v, tier)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (ts, op, command, exit_code, error, dc, source, capture,
         git_head or _git_head(), env_fingerprint or _env_fingerprint(), schema_v or SCHEMA_V, tier))
    trace_store.conn.commit()
    return dc


def ingest_event(ev: dict, source: str = "real", capture: str = "hook") -> Optional[int]:
    """P5a.82 §三：按 filter_oplog_v1 判级后入库。drop 丢弃；gray 入库但不计触发线。"""
    from .oplog_filter import filter_event
    verdict = filter_event(ev)
    if verdict["action"] == "drop":
        return None
    return add(ev.get("ts"), ev.get("op"), ev.get("command"), int(ev.get("exit_code", 0)),
               ev.get("error", ""), source=source, capture=capture,
               death_class=verdict.get("death_class"), tier=verdict.get("tier", "gray"))


def list_all(limit: int = 1000, source: str = None) -> List[dict]:
    q = ("SELECT id, ts, op, command, exit_code, error, death_class, source, capture,"
         " git_head, env_fingerprint, schema_v, tier FROM code_corpses")
    params: tuple = ()
    if source:
        q += " WHERE source = ?"
        params = (source,)
    q += " ORDER BY id DESC LIMIT ?"
    params = params + (limit,)
    rows = trace_store.conn.execute(q, params).fetchall()
    return [{"id": r[0], "ts": r[1], "op": r[2], "command": r[3], "exit_code": r[4],
             "error": r[5], "death_class": r[6], "source": r[7], "capture": r[8],
             "git_head": r[9] or "unknown", "env_fingerprint": r[10] or "unknown",
             "schema_v": r[11] or "unknown", "tier": r[12] or "live"} for r in rows]


def real_count() -> int:
    """触发线口径：source=real 且非灰区（tier!=gray）。"""
    return len([c for c in list_all(limit=100000, source="real") if c["tier"] != "gray"])


def real_classes() -> List[str]:
    return sorted({c["death_class"] for c in list_all(limit=100000, source="real")
                   if c["tier"] != "gray"})


def set_source(corpse_id: int, source: str, capture: str = None) -> None:
    """洁池：标注/隔离来源（P5a.79 §二.1）。"""
    if capture is None:
        trace_store.conn.execute("UPDATE code_corpses SET source=? WHERE id=?", (source, corpse_id))
    else:
        trace_store.conn.execute("UPDATE code_corpses SET source=?, capture=? WHERE id=?",
                                 (source, capture, corpse_id))
    trace_store.conn.commit()


def mine_input() -> List[dict]:
    """产出 ring_mine 可消化的模式（只计 source=real 且非灰区）；按 death_class 聚合。"""
    rows = trace_store.conn.execute(
        "SELECT death_class, count(*) FROM code_corpses"
        " WHERE source='real' AND (tier IS NULL OR tier!='gray')"
        " GROUP BY death_class").fetchall()
    return [{"kind": "code_" + r[0], "pattern_id": "CODE::" + r[0], "occurrences": r[1]} for r in rows]
