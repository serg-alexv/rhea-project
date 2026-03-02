#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

STATE_DIR="$REPO_ROOT/.rhea/flow_up"
PID_FILE="$STATE_DIR/flow_up.pid"
STDOUT_LOG="$STATE_DIR/flow_up.stdout.log"

mkdir -p "$STATE_DIR"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/rhea/flow_up.sh start [--interval N]
  bash scripts/rhea/flow_up.sh stop
  bash scripts/rhea/flow_up.sh status
  bash scripts/rhea/flow_up.sh once
  bash scripts/rhea/flow_up.sh tail [N]
  bash scripts/rhea/flow_up.sh logs [N]
EOF
}

is_running() {
  [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

is_launchd_running() {
  local domain
  domain="gui/$(id -u)"
  launchctl print "$domain/com.rhea.flowup" >/dev/null 2>&1
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
      echo "flow_up guard already running (PID $(cat "$PID_FILE"))"
      exit 0
    fi
    interval=20
    if [[ "${1:-}" == "--interval" && -n "${2:-}" ]]; then
      interval="$2"
      shift 2
    fi
    nohup python3 "$REPO_ROOT/scripts/flow_up_guard.py" run --interval "$interval" --notify --echo >>"$STDOUT_LOG" 2>&1 &
    pid=$!
    echo "$pid" > "$PID_FILE"
    sleep 0.2
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "failed to start flow_up guard"
      rm -f "$PID_FILE"
      tail -n 40 "$STDOUT_LOG" 2>/dev/null || true
      exit 1
    fi
    echo "flow_up guard started"
    echo "  PID: $pid"
    echo "  Log: $STDOUT_LOG"
    ;;

  stop)
    cleanup_stale_pid
    if ! [[ -f "$PID_FILE" ]]; then
      echo "flow_up guard not running"
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
    echo "flow_up guard stopped (PID $pid)"
    ;;

  status)
    cleanup_stale_pid
    if is_running; then
      echo "flow_up guard: running (PID $(cat "$PID_FILE"))"
    elif is_launchd_running; then
      echo "flow_up guard: running (launchd com.rhea.flowup)"
    else
      echo "flow_up guard: not running"
    fi
    python3 "$REPO_ROOT/scripts/flow_up_guard.py" status
    ;;

  once)
    python3 "$REPO_ROOT/scripts/flow_up_guard.py" once --notify --echo
    ;;

  tail)
    n="${1:-40}"
    python3 "$REPO_ROOT/scripts/flow_up_guard.py" tail -n "$n"
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
