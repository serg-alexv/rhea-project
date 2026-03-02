#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

STATE_DIR="$REPO_ROOT/.rhea/gemini_guard"
PID_FILE="$STATE_DIR/gemini_guard.pid"
STDOUT_LOG="$STATE_DIR/gemini_guard.stdout.log"

mkdir -p "$STATE_DIR"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/rhea/gemini.sh start [--interval N]
  bash scripts/rhea/gemini.sh stop
  bash scripts/rhea/gemini.sh status
  bash scripts/rhea/gemini.sh once
  bash scripts/rhea/gemini.sh tail [N]
  bash scripts/rhea/gemini.sh logs [N]
EOF
}

is_running() {
  [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

is_launchd_running() {
  local domain
  domain="gui/$(id -u)"
  launchctl print "$domain/com.rhea.gemini" >/dev/null 2>&1
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
      echo "gemini_guard already running (PID $(cat "$PID_FILE"))"
      exit 0
    elif is_launchd_running; then
      echo "gemini_guard already running (launchd com.rhea.gemini)"
      exit 0
    fi
    interval=45
    if [[ "${1:-}" == "--interval" && -n "${2:-}" ]]; then
      interval="$2"
      shift 2
    fi
    nohup python3 "$REPO_ROOT/scripts/gemini_guard.py" run \
      --interval "$interval" \
      --notify \
      --echo \
      >>"$STDOUT_LOG" 2>&1 &
    pid=$!
    echo "$pid" > "$PID_FILE"
    sleep 0.2
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "failed to start gemini_guard daemon"
      rm -f "$PID_FILE"
      tail -n 40 "$STDOUT_LOG" 2>/dev/null || true
      exit 1
    fi
    echo "gemini_guard started"
    echo "  PID: $pid"
    echo "  Log: $STDOUT_LOG"
    ;;

  stop)
    cleanup_stale_pid
    if ! [[ -f "$PID_FILE" ]]; then
      if is_launchd_running; then
        echo "gemini_guard is managed by launchd (com.rhea.gemini)"
        echo "use: bash scripts/rhea.sh maintainers stop"
        exit 0
      fi
      echo "gemini_guard not running"
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
    echo "gemini_guard stopped (PID $pid)"
    ;;

  status)
    cleanup_stale_pid
    if is_running; then
      echo "gemini_guard: running (PID $(cat "$PID_FILE"))"
    elif is_launchd_running; then
      echo "gemini_guard: running (launchd com.rhea.gemini)"
    else
      echo "gemini_guard: not running"
    fi
    python3 "$REPO_ROOT/scripts/gemini_guard.py" status
    ;;

  once)
    python3 "$REPO_ROOT/scripts/gemini_guard.py" once --notify --echo
    ;;

  tail)
    n="${1:-20}"
    python3 "$REPO_ROOT/scripts/gemini_guard.py" tail -n "$n"
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
