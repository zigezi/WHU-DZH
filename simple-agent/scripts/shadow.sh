#!/usr/bin/env bash
# 影子实例启停（P4.2，v2.3 修复两处已知缺陷）。
# 只操作 pidmap 里自己登记的 PID，绝不碰 8000。
# 用法：scripts/shadow.sh start <branch> | scripts/shadow.sh stop
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SHADOW_DIR="$ROOT/.agent/worktrees/shadow"
PIDMAP="$ROOT/.agent/pidmap.json"
LOG_DIR="$ROOT/.agent/logs"
PORT=8002
CMD="${1:-}"
BRANCH="${2:-}"

usage() { echo "usage: $0 {start <branch>|stop}" >&2; exit 2; }

# 反查真实监听 PID（修复 1：不信任 $!，uvicorn 会 re-exec/起子进程）
listener_pid() {
  ss -tlnp 2>/dev/null | grep ":${PORT} " | grep -oP 'pid=\K[0-9]+' | head -1
}

start() {
  [ -z "$BRANCH" ] && usage
  mkdir -p "$ROOT/.agent/worktrees" "$LOG_DIR"

  if [ -n "$(listener_pid)" ]; then
    echo "[shadow] port $PORT already in use by pid $(listener_pid)" >&2
    exit 1
  fi

  if [ ! -d "$SHADOW_DIR" ]; then
    if git -C "$ROOT" show-ref --verify --quiet "refs/heads/$BRANCH"; then
      git -C "$ROOT" worktree add "$SHADOW_DIR" "$BRANCH"
    else
      git -C "$ROOT" worktree add -b "$BRANCH" "$SHADOW_DIR" HEAD
    fi
  fi

  (
    cd "$SHADOW_DIR/backend"
    set -a
    [ -f "$ROOT/backend/.env" ] && . "$ROOT/backend/.env"
    set +a
    setsid python3 -m uvicorn main:app --host 0.0.0.0 --port "$PORT" \
      </dev/null > "$LOG_DIR/shadow-$PORT.log" 2>&1 &
  )

  # 修复 2：等待循环健康检查（每 1s，最多 30 次），成功后再写 pidmap
  ok=0
  for _ in $(seq 1 30); do
    if curl -sf "http://localhost:$PORT/" >/dev/null 2>&1; then ok=1; break; fi
    sleep 1
  done
  if [ "$ok" != "1" ]; then
    echo "[shadow] health check failed after 30s; see $LOG_DIR/shadow-$PORT.log" >&2
    exit 1
  fi

  PID="$(listener_pid)"
  if [ -z "$PID" ]; then
    echo "[shadow] cannot resolve listener pid for :$PORT" >&2
    exit 1
  fi
  printf '{"port":%s,"pid":%s,"branch":"%s","dir":"%s","started_at":"%s"}\n' \
    "$PORT" "$PID" "$BRANCH" "$SHADOW_DIR" "$(date -Is)" > "$PIDMAP"
  echo "[shadow] started pid=$PID port=$PORT branch=$BRANCH"
}

stop() {
  if [ ! -f "$PIDMAP" ]; then
    echo "[shadow] no pidmap, nothing to stop" >&2
    exit 1
  fi
  PID="$(python3 -c "import json;print(json.load(open('$PIDMAP'))['pid'])")"
  PORT="$(python3 -c "import json;print(json.load(open('$PIDMAP'))['port'])")"

  # 三重校验：PID 存在、命令行含 uvicorn、确实是 :8002 的监听者
  if ! ps -p "$PID" >/dev/null 2>&1; then
    echo "[shadow] pid $PID not running; removing stale pidmap"
    rm -f "$PIDMAP"
    return 0
  fi
  if ! tr '\0' ' ' < "/proc/$PID/cmdline" 2>/dev/null | grep -q "uvicorn"; then
    echo "[shadow] pid $PID is not a uvicorn process, refusing to kill" >&2
    exit 1
  fi
  if [ "$(listener_pid)" != "$PID" ]; then
    echo "[shadow] pid $PID is not the :$PORT listener, refusing to kill" >&2
    exit 1
  fi

  kill "$PID"
  for _ in $(seq 1 15); do
    [ -z "$(listener_pid)" ] && break
    sleep 1
  done
  rm -f "$PIDMAP"
  echo "[shadow] stopped pid=$PID port=$PORT"
}

case "$CMD" in
  start) start ;;
  stop) stop ;;
  *) usage ;;
esac
