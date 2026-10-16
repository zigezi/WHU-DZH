#!/usr/bin/env bash
# τ-bench sidecar 启停（P5a 5a.0/5a.2）。
# 独立 venv `.agent/venv/tau/`，监听 127.0.0.1:8010（仅 loopback）。
# 注意：使用独立的 tau_pidmap.json，避免与 shadow.sh 的 pidmap.json 互相覆盖。
# 用法：scripts/tau_sidecar.sh {start|stop|status}
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.agent/venv/tau/bin/python"
SCRIPT="$ROOT/backend/requirements/adapters/tau/sidecar.py"
PIDMAP="$ROOT/.agent/tau_pidmap.json"
LOG_DIR="$ROOT/.agent/logs"
HOST=127.0.0.1
PORT="${TAU_SIDECAR_PORT:-8010}"
CMD="${1:-}"

usage() { echo "usage: $0 {start|stop|status}" >&2; exit 2; }

listener_pid() {
  ss -tlnp 2>/dev/null | grep ":${PORT} " | grep -oP 'pid=\K[0-9]+' | head -1
}

start() {
  mkdir -p "$LOG_DIR"
  if [ ! -x "$PY" ]; then echo "[tau] venv python missing: $PY" >&2; exit 1; fi
  if [ -n "$(listener_pid)" ]; then
    echo "[tau] port $PORT already in use by pid $(listener_pid)" >&2; exit 1
  fi
  ( setsid "$PY" "$SCRIPT" </dev/null > "$LOG_DIR/tau_sidecar.log" 2>&1 & )

  ok=0
  for _ in $(seq 1 30); do
    if curl -sf "http://$HOST:$PORT/health" >/dev/null 2>&1; then ok=1; break; fi
    sleep 1
  done
  if [ "$ok" != "1" ]; then
    echo "[tau] health check failed; see $LOG_DIR/tau_sidecar.log" >&2; exit 1
  fi
  PID="$(listener_pid)"
  [ -z "$PID" ] && { echo "[tau] cannot resolve listener pid" >&2; exit 1; }
  printf '{"service":"tau-sidecar","host":"%s","port":%s,"pid":%s,"started_at":"%s"}\n' \
    "$HOST" "$PORT" "$PID" "$(date -Is)" > "$PIDMAP"
  echo "[tau] started pid=$PID host=$HOST port=$PORT"
}

stop() {
  if [ ! -f "$PIDMAP" ]; then echo "[tau] no pidmap, nothing to stop" >&2; exit 1; fi
  PID="$(python3 -c "import json;print(json.load(open('$PIDMAP'))['pid'])")"
  if ! ps -p "$PID" >/dev/null 2>&1; then
    echo "[tau] pid $PID not running; removing stale pidmap"; rm -f "$PIDMAP"; return 0
  fi
  if ! tr '\0' ' ' < "/proc/$PID/cmdline" 2>/dev/null | grep -q "sidecar.py"; then
    echo "[tau] pid $PID is not the tau sidecar, refusing to kill" >&2; exit 1
  fi
  kill "$PID"
  for _ in $(seq 1 15); do [ -z "$(listener_pid)" ] && break; sleep 1; done
  rm -f "$PIDMAP"
  echo "[tau] stopped pid=$PID"
}

status() {
  if [ -n "$(listener_pid)" ]; then echo "[tau] running pid=$(listener_pid) port=$PORT"; else echo "[tau] not running"; fi
}

case "$CMD" in
  start) start ;;
  stop) stop ;;
  status) status ;;
  *) usage ;;
esac
