#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

STATE_DIR="$REPO_ROOT/.rhea/ndi"
PID_FILE="$STATE_DIR/ndi.pid"
STDOUT_LOG="$STATE_DIR/ndi.stdout.log"
TRACE_FILE="$REPO_ROOT/opera/metrics/ndi_trace.jsonl"

mkdir -p "$STATE_DIR" "$(dirname "$TRACE_FILE")"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/rhea/ndi.sh start [--interval N]
  bash scripts/rhea/ndi.sh stop
  bash scripts/rhea/ndi.sh status
  bash scripts/rhea/ndi.sh once
  bash scripts/rhea/ndi.sh tail [N]
  bash scripts/rhea/ndi.sh logs [N]
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
      echo "ndi watchdog already running (PID $(cat "$PID_FILE"))"
      exit 0
    fi
    interval=6
    if [[ "${1:-}" == "--interval" && -n "${2:-}" ]]; then
      interval="$2"
      shift 2
    fi
    python3 "$REPO_ROOT/scripts/ndi_watchdog.py" prime >/dev/null
    nohup python3 "$REPO_ROOT/scripts/ndi_watchdog.py" run --interval "$interval" --notify --echo >>"$STDOUT_LOG" 2>&1 &
    pid=$!
    echo "$pid" > "$PID_FILE"
    sleep 0.2
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "failed to start ndi watchdog"
      rm -f "$PID_FILE"
      tail -n 40 "$STDOUT_LOG" 2>/dev/null || true
      exit 1
    fi
    echo "ndi watchdog started"
    echo "  PID: $pid"
    echo "  Trace: $TRACE_FILE"
    echo "  Log: $STDOUT_LOG"
    ;;

  stop)
    cleanup_stale_pid
    if ! [[ -f "$PID_FILE" ]]; then
      echo "ndi watchdog not running"
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
    echo "ndi watchdog stopped (PID $pid)"
    ;;

  status)
    cleanup_stale_pid
    if is_running; then
      echo "ndi watchdog: running (PID $(cat "$PID_FILE"))"
    else
      echo "ndi watchdog: not running"
    fi
    python3 "$REPO_ROOT/scripts/ndi_watchdog.py" status
    ;;

  once)
    python3 "$REPO_ROOT/scripts/ndi_watchdog.py" once --notify --echo
    ;;

  tail)
    n="${1:-40}"
    python3 "$REPO_ROOT/scripts/ndi_watchdog.py" tail -n "$n"
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
