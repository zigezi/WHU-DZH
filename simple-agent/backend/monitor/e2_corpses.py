"""P5a.81 §五 / P5a.86 §三.4：E2 新域尸体池（domain_pack="bid"）。

与 code_corpses 同构（同采集口径 filter_oplog_v1 / 同语境锚定字段），独立成池。
E2 epoch-1 以资产=0 开局；尸体→候选→电池→C-1→指纹→影子，一要件不免（a81 §三）。
"""
from typing import List, Optional

from .trace_store import trace_store
from .code_corpses import classify, _git_head, _env_fingerprint, SCHEMA_V

TABLE = "e2_corpses"
DOMAIN_PACK = "bid"
COLS = ("id, ts, op, command, exit_code, error, death_class, source, capture,"
        " git_head, env_fingerprint, schema_v, tier, domain_pack")


def add(ts, op, command, exit_code, error, source="real", capture="e2",
        git_head=None, env_fingerprint=None, schema_v=None,
        death_class=None, tier="live", domain_pack=DOMAIN_PACK) -> Optional[int]:
    dc = death_class or classify(op, exit_code, error)
    if dc is None:
        return None
    trace_store.conn.execute(
        f"INSERT INTO {TABLE} (ts, op, command, exit_code, error, death_class, source,"
        " capture, git_head, env_fingerprint, schema_v, tier, domain_pack)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (ts, op, command, exit_code, error, dc, source, capture,
         git_head or _git_head(), env_fingerprint or _env_fingerprint(),
         schema_v or SCHEMA_V, tier, domain_pack))
    trace_store.conn.commit()
    return dc


def ingest_event(ev: dict, source: str = "real", capture: str = "e2_hook") -> Optional[int]:
    from .oplog_filter import filter_event
    v = filter_event(ev)
    if v["action"] == "drop":
        return None
    return add(ev.get("ts"), ev.get("op"), ev.get("command"), int(ev.get("exit_code", 0)),
               ev.get("error", ""), source=source, capture=capture,
               death_class=v.get("death_class"), tier=v.get("tier", "gray"))


def list_all(limit: int = 1000, source: str = None) -> List[dict]:
    q = f"SELECT {COLS} FROM {TABLE}"
    params: tuple = ()
    if source:
        q += " WHERE source = ?"
        params = (source,)
    q += " ORDER BY id DESC LIMIT ?"
    params = params + (limit,)
    rows = trace_store.conn.execute(q, params).fetchall()
    keys = ("id", "ts", "op", "command", "exit_code", "error", "death_class", "source",
            "capture", "git_head", "env_fingerprint", "schema_v", "tier", "domain_pack")
    out = []
    for r in rows:
        d = dict(zip(keys, r))
        for k in ("git_head", "env_fingerprint", "schema_v"):
            d[k] = d[k] or "unknown"
        d["tier"] = d["tier"] or "live"
        out.append(d)
    return out


def real_count() -> int:
    return len([c for c in list_all(limit=100000, source="real") if c["tier"] != "gray"])


def real_classes() -> List[str]:
    return sorted({c["death_class"] for c in list_all(limit=100000, source="real") if c["tier"] != "gray"})


def mine_input() -> List[dict]:
    rows = trace_store.conn.execute(
        f"SELECT death_class, count(*) FROM {TABLE}"
        " WHERE source='real' AND (tier IS NULL OR tier!='gray') GROUP BY death_class").fetchall()
    return [{"kind": "e2_" + r[0], "pattern_id": "E2::" + r[0], "occurrences": r[1]} for r in rows]
