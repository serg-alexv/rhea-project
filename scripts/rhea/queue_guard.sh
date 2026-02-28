#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

STATE_DIR="$REPO_ROOT/.rhea/queue_guard"
PID_FILE="$STATE_DIR/queue_guard.pid"
STDOUT_LOG="$STATE_DIR/queue_guard.stdout.log"

mkdir -p "$STATE_DIR"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/rhea/queue_guard.sh start [--interval N]
  bash scripts/rhea/queue_guard.sh stop
  bash scripts/rhea/queue_guard.sh status
  bash scripts/rhea/queue_guard.sh once
  bash scripts/rhea/queue_guard.sh compact
  bash scripts/rhea/queue_guard.sh tail
  bash scripts/rhea/queue_guard.sh logs [N]
EOF
}

is_running() {
  [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

cleanup_stale_pid() {
  if [[ -f "$PID_FILE" ]] && ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    rm -f "$PID_FILE"
  fi
}

cmd="${1:-help}"
shift || true

case "$cmd" in
  start)
    cleanup_stale_pid
    if is_running; then
      echo "queue_guard already running (PID $(cat "$PID_FILE"))"
      exit 0
    fi
    interval=30
    if [[ "${1:-}" == "--interval" && -n "${2:-}" ]]; then
      interval="$2"
      shift 2
    fi
    nohup python3 "$REPO_ROOT/scripts/rhea_queue_guard.py" run --interval "$interval" --echo --notify >>"$STDOUT_LOG" 2>&1 &
    pid=$!
    echo "$pid" > "$PID_FILE"
    sleep 0.2
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "failed to start queue_guard daemon"
      rm -f "$PID_FILE"
      tail -n 40 "$STDOUT_LOG" 2>/dev/null || true
      exit 1
    fi
    echo "queue_guard started"
    echo "  PID: $pid"
    echo "  Log: $STDOUT_LOG"
    ;;

  stop)
    cleanup_stale_pid
    if ! [[ -f "$PID_FILE" ]]; then
      echo "queue_guard not running"
      exit 0
    fi
    pid="$(cat "$PID_FILE")"
    kill "$pid" 2>/dev/null || true
    for _ in 1 2 3 4 5; do
      if ! kill -0 "$pid" 2>/dev/null; then
        break
      fi
      sleep 0.2
    done
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
    echo "queue_guard stopped (PID $pid)"
    ;;

  status)
    cleanup_stale_pid
    if is_running; then
      echo "queue_guard: running (PID $(cat "$PID_FILE"))"
    else
      echo "queue_guard: not running"
    fi
    python3 "$REPO_ROOT/scripts/rhea_queue_guard.py" status
    ;;

  once)
    python3 "$REPO_ROOT/scripts/rhea_queue_guard.py" once --notify
    ;;

  compact)
    python3 "$REPO_ROOT/scripts/rhea_queue_guard.py" compact
    ;;

  tail)
    python3 "$REPO_ROOT/scripts/rhea_queue_guard.py" tail
    ;;

  logs)
    n="${1:-40}"
    tail -n "$n" "$STDOUT_LOG"
    ;;

  help|--help|-h)
    usage
    ;;

  *)
    echo "unknown command: $cmd"
    usage
    exit 1
    ;;
esac
