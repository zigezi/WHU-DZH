import sqlite3
import json
import os
import threading
from typing import List, Optional
from .schema import Trace, Span

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "logs", "trace.db")


class TraceStore:
    """
    线程安全的 SQLite trace/span 存储。

    说明：worker 通过线程池并发执行任务，monitor 进程还会同时读取同一个
    DB 文件，因此这里必须：
      1. 用同一把可重入锁串行化本进程内的所有写操作；
      2. 打开 WAL 模式，允许跨进程「多读一写」；
      3. 设置 busy timeout，避免瞬时锁冲突直接抛 "database is locked"。
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA busy_timeout=30000")
        self._init_tables()

    # ------------------------------------------------------------------ #
    # 初始化 / 迁移
    # ------------------------------------------------------------------ #
    def _init_tables(self):
        with self._lock:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS traces (
                    trace_id TEXT PRIMARY KEY,
                    task_id TEXT,
                    task_content TEXT,
                    start_time REAL,
                    end_time REAL,
                    status TEXT,
                    total_tokens INTEGER,
                    total_tool_calls INTEGER
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS spans (
                    span_id TEXT PRIMARY KEY,
                    trace_id TEXT,
                    parent_span_id TEXT,
                    name TEXT,
                    type TEXT,
                    layer TEXT,
                    status TEXT,
                    start_time REAL,
                    end_time REAL,
                    duration_ms REAL,
                    attributes TEXT,
                    error TEXT
                )
            """)
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_spans_trace ON spans(trace_id)"
            )
            # 统一任务状态表：替代内存 task_store dict（P0.2）
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    status TEXT,
                    created_at TEXT,
                    created_at_ts REAL,
                    finished_at TEXT,
                    result TEXT,
                    error TEXT,
                    duration_ms REAL,
                    llm_tokens INTEGER,
                    content TEXT,
                    steps TEXT,
                    tool_calls_count INTEGER,
                    req_id TEXT
                )
            """)
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at_ts)"
            )
            # 路由后验表（P3.2）：每个 (任务族, 臂, 环境指纹) 一组 Beta 参数
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS routes (
                    sig_family TEXT,
                    arm TEXT,
                    alpha REAL,
                    beta REAL,
                    total_tokens REAL,
                    n INTEGER,
                    env_fp TEXT,
                    PRIMARY KEY (sig_family, arm, env_fp)
                )
            """)
            # 先例库（P3.3）
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS precedents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sig TEXT,
                    req_id TEXT,
                    plan_json TEXT,
                    assertions_ref TEXT,
                    tokens INTEGER,
                    duration_ms REAL,
                    created_at TEXT,
                    content TEXT
                )
            """)
            # 兼容旧库：补充 result / error / code_version 列
            self._ensure_column("traces", "result", "TEXT")
            self._ensure_column("traces", "error", "TEXT")
            self._ensure_column("traces", "code_version", "TEXT")
            self.conn.commit()

    def _ensure_column(self, table: str, column: str, decl: str):
        cols = [row[1] for row in self.conn.execute(f"PRAGMA table_info({table})")]
        if column not in cols:
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")

    # ------------------------------------------------------------------ #
    # Trace
    # ------------------------------------------------------------------ #
    def add_trace(self, trace: Trace):
        with self._lock:
            self.conn.execute("""
                INSERT OR REPLACE INTO traces
                (trace_id, task_id, task_content, start_time, end_time, status,
                 total_tokens, total_tool_calls, result, error, code_version)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (
                trace.trace_id, trace.task_id, trace.task_content,
                trace.start_time, trace.end_time, trace.status,
                trace.total_tokens, trace.total_tool_calls,
                trace.result, trace.error,
                getattr(trace, "code_version", None)
            ))
            self.conn.commit()

    def update_trace(self, trace: Trace):
        self.add_trace(trace)

    # ------------------------------------------------------------------ #
    # Span
    # ------------------------------------------------------------------ #
    def add_span(self, span: Span):
        with self._lock:
            self.conn.execute("""
                INSERT OR REPLACE INTO spans VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                span.span_id, span.trace_id, span.parent_span_id,
                span.name, span.type, span.layer, span.status,
                span.start_time, span.end_time, span.duration_ms,
                json.dumps(span.attributes, ensure_ascii=False, default=str), span.error
            ))
            self.conn.commit()

    def update_span(self, span: Span):
        self.add_span(span)

    # ------------------------------------------------------------------ #
    # 查询
    # ------------------------------------------------------------------ #
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        with self._lock:
            row = self.conn.execute(
                "SELECT trace_id, task_id, task_content, start_time, end_time, status,"
                " total_tokens, total_tool_calls, result, error, code_version"
                " FROM traces WHERE trace_id=?", (trace_id,)
            ).fetchone()
        if not row:
            return None
        return Trace(
            trace_id=row[0], task_id=row[1], task_content=row[2],
            start_time=row[3], end_time=row[4], status=row[5],
            total_tokens=row[6] or 0, total_tool_calls=row[7] or 0,
            result=row[8], error=row[9], code_version=row[10],
            spans=self.get_spans_by_trace(trace_id)
        )

    @staticmethod
    def _row_to_span(row) -> Span:
        try:
            attributes = json.loads(row[10]) if row[10] else {}
        except (ValueError, TypeError):
            attributes = {}
        return Span(
            span_id=row[0], trace_id=row[1], parent_span_id=row[2],
            name=row[3], type=row[4], layer=row[5], status=row[6],
            start_time=row[7], end_time=row[8], duration_ms=row[9],
            attributes=attributes, error=row[11],
        )

    def get_spans_by_trace(self, trace_id: str) -> List[Span]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT * FROM spans WHERE trace_id=? ORDER BY start_time ASC",
                (trace_id,)
            ).fetchall()
        return [self._row_to_span(row) for row in rows]

    def get_span(self, span_id: str) -> Optional[Span]:
        with self._lock:
            row = self.conn.execute(
                "SELECT * FROM spans WHERE span_id=?", (span_id,)
            ).fetchone()
        return self._row_to_span(row) if row else None

    def get_spans_by_plan_id(self, plan_id: str) -> List[Span]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT * FROM spans WHERE json_extract(attributes,'$.plan_id')=?"
                " ORDER BY start_time ASC", (plan_id,)
            ).fetchall()
        return [self._row_to_span(row) for row in rows]

    def find_spans_by_type(self, span_type: str, limit: int = 1000) -> List[Span]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT * FROM spans WHERE type=? ORDER BY start_time DESC LIMIT ?",
                (span_type, limit),
            ).fetchall()
        return [self._row_to_span(row) for row in rows]

    def list_traces(self, limit: int = 100, status: str = None) -> List[Trace]:
        with self._lock:
            query = "SELECT trace_id FROM traces"
            params = []
            if status:
                query += " WHERE status=?"
                params.append(status)
            query += " ORDER BY start_time DESC LIMIT ?"
            params.append(limit)
            trace_ids = [row[0] for row in self.conn.execute(query, params).fetchall()]
        return [self.get_trace(tid) for tid in trace_ids]


    # ------------------------------------------------------------------ #
    # Task：统一任务状态入库（P0.2，替代内存 task_store）
    # ------------------------------------------------------------------ #
    @staticmethod
    def _to_iso(value):
        if value is None:
            return None
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)

    @staticmethod
    def _row_to_task(row) -> dict:
        try:
            steps = json.loads(row[10]) if row[10] else []
        except (ValueError, TypeError):
            steps = []
        return {
            "task_id": row[0], "status": row[1], "created_at": row[2],
            "created_at_ts": row[3] or 0, "finished_at": row[4],
            "result": row[5], "error": row[6], "duration_ms": row[7],
            "llm_tokens": row[8] or 0, "content": row[9] or "",
            "steps": steps, "tool_calls_count": row[11] or 0, "req_id": row[12],
        }

    def upsert_task(self, task: dict):
        with self._lock:
            self.conn.execute("""
                INSERT OR REPLACE INTO tasks
                (task_id, status, created_at, created_at_ts, finished_at,
                 result, error, duration_ms, llm_tokens, content, steps,
                 tool_calls_count, req_id)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                task.get("task_id"),
                task.get("status"),
                self._to_iso(task.get("created_at")),
                task.get("created_at_ts") or 0,
                self._to_iso(task.get("finished_at")),
                task.get("result"),
                task.get("error"),
                task.get("duration_ms"),
                task.get("llm_tokens") or 0,
                task.get("content", ""),
                json.dumps(task.get("steps", []), ensure_ascii=False, default=str),
                task.get("tool_calls_count") or 0,
                task.get("req_id"),
            ))
            self.conn.commit()

    def get_task(self, task_id: str) -> Optional[dict]:
        with self._lock:
            row = self.conn.execute(
                "SELECT task_id, status, created_at, created_at_ts, finished_at,"
                " result, error, duration_ms, llm_tokens, content, steps,"
                " tool_calls_count, req_id FROM tasks WHERE task_id=?",
                (task_id,),
            ).fetchone()
        return self._row_to_task(row) if row else None

    def list_tasks(self, limit: int = 20) -> List[dict]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT task_id, status, created_at, created_at_ts, finished_at,"
                " result, error, duration_ms, llm_tokens, content, steps,"
                " tool_calls_count, req_id FROM tasks"
                " ORDER BY created_at_ts DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_task(row) for row in rows]

    # ------------------------------------------------------------------ #
    # Routes：路由后验（P3.2）
    # ------------------------------------------------------------------ #
    def get_route_params(self, sig_family: str, arm: str, env_fp: str):
        with self._lock:
            row = self.conn.execute(
                "SELECT alpha, beta FROM routes"
                " WHERE sig_family=? AND arm=? AND env_fp=?",
                (sig_family, arm, env_fp),
            ).fetchone()
        if not row:
            return 1.0, 1.0
        return float(row[0]), float(row[1])

    def update_route(self, sig_family: str, arm: str, env_fp: str,
                     success: bool, tokens: float = 0):
        with self._lock:
            row = self.conn.execute(
                "SELECT alpha, beta, total_tokens, n FROM routes"
                " WHERE sig_family=? AND arm=? AND env_fp=?",
                (sig_family, arm, env_fp),
            ).fetchone()
            if row:
                alpha, beta, total_tokens, n = row
            else:
                alpha, beta, total_tokens, n = 1.0, 1.0, 0.0, 0
            if success:
                alpha += 1.0
            else:
                beta += 1.0
            total_tokens += tokens or 0
            n += 1
            self.conn.execute(
                "INSERT OR REPLACE INTO routes VALUES (?,?,?,?,?,?,?)",
                (sig_family, arm, alpha, beta, total_tokens, n, env_fp),
            )
            self.conn.commit()
        return alpha, beta

    def list_routes(self, limit: int = 200) -> List[dict]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT sig_family, arm, alpha, beta, total_tokens, n, env_fp"
                " FROM routes ORDER BY n DESC LIMIT ?", (limit,),
            ).fetchall()
        return [
            {"sig_family": r[0], "arm": r[1], "alpha": r[2], "beta": r[3],
             "total_tokens": r[4], "n": r[5], "env_fp": r[6]}
            for r in rows
        ]

    # ------------------------------------------------------------------ #
    # Precedents：先例库（P3.3）
    # ------------------------------------------------------------------ #
    def add_precedent(self, precedent: dict):
        with self._lock:
            self.conn.execute(
                "INSERT INTO precedents"
                " (sig, req_id, plan_json, assertions_ref, tokens, duration_ms,"
                "  created_at, content) VALUES (?,?,?,?,?,?,?,?)",
                (
                    precedent.get("sig"),
                    precedent.get("req_id"),
                    json.dumps(precedent.get("plan", []), ensure_ascii=False,
                               default=str),
                    precedent.get("assertions_ref"),
                    precedent.get("tokens") or 0,
                    precedent.get("duration_ms"),
                    self._to_iso(precedent.get("created_at")),
                    precedent.get("content", ""),
                ),
            )
            self.conn.commit()

    def list_precedents(self, limit: int = 500) -> List[dict]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT id, sig, req_id, plan_json, assertions_ref, tokens,"
                " duration_ms, created_at, content FROM precedents"
                " ORDER BY id DESC LIMIT ?", (limit,),
            ).fetchall()
        result = []
        for r in rows:
            try:
                plan = json.loads(r[3]) if r[3] else []
            except (ValueError, TypeError):
                plan = []
            result.append({
                "id": r[0], "sig": r[1], "req_id": r[2], "plan": plan,
                "assertions_ref": r[4], "tokens": r[5] or 0,
                "duration_ms": r[6], "created_at": r[7], "content": r[8] or "",
            })
        return result


# 全局单例
trace_store = TraceStore()
