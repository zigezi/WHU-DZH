#!/usr/bin/env python3
"""janitor: 清理过期容器 / 工作区产物 / 归档旧 trace。

默认干跑（只打印将要清理的内容），加 --apply 才真正执行删除。
"""
import argparse
import gzip
import json
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "backend", "logs", "trace.db")
WORKSPACE = os.path.join(ROOT, "workspace")
EXPORT_DIR = os.path.join(ROOT, ".agent", "exports")

CONTAINER_AGE_S = 3600
WORKSPACE_AGE_S = 7 * 24 * 3600
TRACE_AGE_S = 30 * 24 * 3600


def find_stale_containers():
    """返回 exited 超过 1h 的容器 (id, name, status)。docker 不存在时返回 []。"""
    try:
        out = subprocess.run(
            ["docker", "ps", "-a", "--filter", "status=exited",
             "--format", "{{.ID}}\t{{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=10,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return []
    if out.returncode != 0:
        return []

    stale = []
    now = time.time()
    for line in out.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        cid, name, status = parts[0], parts[1], parts[2]
        age = _parse_exited_age(status)
        if age is not None and age > CONTAINER_AGE_S:
            stale.append((cid, name, status, age))
    return stale


def _parse_exited_age(status: str):
    """从 'Exited (0) 2 hours ago' 解析秒数。"""
    import re
    m = re.search(r"(\d+)\s+(second|minute|hour|day|week|month)s?\s+ago", status)
    if not m:
        return None
    value = int(m.group(1))
    unit = m.group(2)
    factor = {
        "second": 1, "minute": 60, "hour": 3600,
        "day": 86400, "week": 7 * 86400, "month": 30 * 86400,
    }[unit]
    return value * factor


def find_stale_workspace_files():
    """workspace 中 mtime 超过 7 天的文件（跳过 .git / 隐藏目录）。"""
    stale = []
    if not os.path.isdir(WORKSPACE):
        return stale
    cutoff = time.time() - WORKSPACE_AGE_S
    for dirpath, dirnames, filenames in os.walk(WORKSPACE):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules")]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            try:
                mtime = os.path.getmtime(full)
            except OSError:
                continue
            if mtime < cutoff:
                stale.append((full, mtime))
    return stale


def _has_running_trace():
    if not os.path.exists(DB_PATH):
        return False
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM traces WHERE status='running'"
        ).fetchone()
        return bool(row and row[0])
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def find_old_traces():
    """start_time 早于 30 天的 trace_id。"""
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    try:
        cutoff = time.time() - TRACE_AGE_S
        rows = conn.execute(
            "SELECT trace_id FROM traces WHERE start_time < ?", (cutoff,)
        ).fetchall()
        return [r[0] for r in rows]
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def export_and_delete_traces(trace_ids, apply=False):
    if not trace_ids:
        return None
    os.makedirs(EXPORT_DIR, exist_ok=True)
    path = os.path.join(
        EXPORT_DIR, f"traces-{datetime.now().strftime('%Y%m%d-%H%M%S')}.jsonl.gz"
    )
    if apply:
        conn = sqlite3.connect(DB_PATH)
        try:
            with gzip.open(path, "wt", encoding="utf-8") as f:
                for tid in trace_ids:
                    trace = conn.execute(
                        "SELECT * FROM traces WHERE trace_id=?", (tid,)
                    ).fetchone()
                    spans = conn.execute(
                        "SELECT * FROM spans WHERE trace_id=?", (tid,)
                    ).fetchall()
                    f.write(json.dumps(
                        {"trace": trace, "spans": spans},
                        ensure_ascii=False, default=str,
                    ) + "\n")
            conn.executemany(
                "DELETE FROM spans WHERE trace_id=?", [(t,) for t in trace_ids]
            )
            conn.executemany(
                "DELETE FROM traces WHERE trace_id=?", [(t,) for t in trace_ids]
            )
            conn.commit()
        finally:
            conn.close()
    return path


def main():
    parser = argparse.ArgumentParser(description="simple-agent janitor")
    parser.add_argument("--apply", action="store_true",
                        help="真正执行删除（默认干跑）")
    args = parser.parse_args()
    mode = "APPLY" if args.apply else "DRY-RUN"

    print(f"[janitor] mode={mode}")

    containers = find_stale_containers()
    print(f"[janitor] exited>1h containers: {len(containers)}")
    for cid, name, status, age in containers:
        print(f"  - {cid[:12]} {name} ({status})")

    if _has_running_trace():
        print("[janitor] 存在 running trace，跳过 workspace 清理")
        stale_files = []
    else:
        stale_files = find_stale_workspace_files()
    print(f"[janitor] workspace files >7d: {len(stale_files)}")
    for full, mtime in stale_files:
        print(f"  - {os.path.relpath(full, ROOT)} "
              f"({datetime.fromtimestamp(mtime).isoformat(timespec='seconds')})")

    old_traces = find_old_traces()
    print(f"[janitor] traces >30d: {len(old_traces)}")
    for tid in old_traces:
        print(f"  - {tid}")

    if args.apply:
        for cid, _, _, _ in containers:
            try:
                subprocess.run(["docker", "rm", cid], capture_output=True, timeout=30)
            except (FileNotFoundError, subprocess.SubprocessError):
                pass
        for full, _ in stale_files:
            try:
                os.remove(full)
            except OSError:
                pass
        export_path = export_and_delete_traces(old_traces, apply=True)
        if export_path:
            print(f"[janitor] exported + deleted old traces -> {export_path}")

    print("[janitor] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
