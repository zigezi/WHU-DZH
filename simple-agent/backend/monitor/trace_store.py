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
            # 兼容旧库：补充 result / error 列
            self._ensure_column("traces", "result", "TEXT")
            self._ensure_column("traces", "error", "TEXT")
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
                 total_tokens, total_tool_calls, result, error)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (
                trace.trace_id, trace.task_id, trace.task_content,
                trace.start_time, trace.end_time, trace.status,
                trace.total_tokens, trace.total_tool_calls,
                trace.result, trace.error
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
                " total_tokens, total_tool_calls, result, error"
                " FROM traces WHERE trace_id=?", (trace_id,)
            ).fetchone()
        if not row:
            return None
        return Trace(
            trace_id=row[0], task_id=row[1], task_content=row[2],
            start_time=row[3], end_time=row[4], status=row[5],
            total_tokens=row[6] or 0, total_tool_calls=row[7] or 0,
            result=row[8], error=row[9],
            spans=self.get_spans_by_trace(trace_id)
        )

    def get_spans_by_trace(self, trace_id: str) -> List[Span]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT * FROM spans WHERE trace_id=? ORDER BY start_time ASC",
                (trace_id,)
            ).fetchall()
        spans = []
        for row in rows:
            try:
                attributes = json.loads(row[10]) if row[10] else {}
            except (ValueError, TypeError):
                attributes = {}
            spans.append(Span(
                span_id=row[0], trace_id=row[1], parent_span_id=row[2],
                name=row[3], type=row[4], layer=row[5], status=row[6],
                start_time=row[7], end_time=row[8], duration_ms=row[9],
                attributes=attributes, error=row[11]
            ))
        return spans

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


# 全局单例
trace_store = TraceStore()
