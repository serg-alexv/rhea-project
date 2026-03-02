#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

STATE_DIR="$REPO_ROOT/.rhea/radio"
PID_FILE="$STATE_DIR/radio.pid"
STDOUT_LOG="$STATE_DIR/radio.stdout.log"
FEED_LOG="$REPO_ROOT/opera/metrics/radio_feed.jsonl"

mkdir -p "$STATE_DIR" "$(dirname "$FEED_LOG")"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/rhea/radio.sh start [--interval N]
  bash scripts/rhea/radio.sh stop
  bash scripts/rhea/radio.sh status
  bash scripts/rhea/radio.sh once
  bash scripts/rhea/radio.sh logs [N]
  bash scripts/rhea/radio.sh tail [N]
  bash scripts/rhea/radio.sh listen

Notes:
  - start: background daemon, default interval=2s, notifications ON
  - listen: follow unified radio feed (tail -f)
EOF
}

is_running() {
  [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

is_launchd_running() {
  local domain
  domain="gui/$(id -u)"
  launchctl print "$domain/com.rhea.radio" >/dev/null 2>&1
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
      echo "radio already running (PID $(cat "$PID_FILE"))"
      exit 0
    elif is_launchd_running; then
      echo "radio already running (launchd com.rhea.radio)"
      exit 0
    fi
    interval=2
    if [[ "${1:-}" == "--interval" && -n "${2:-}" ]]; then
      interval="$2"
      shift 2
    fi
    # Start from live edge; skip historical backlog on each daemon restart.
    python3 "$REPO_ROOT/scripts/rhea_radio.py" prime >/dev/null
    nohup python3 "$REPO_ROOT/scripts/rhea_radio.py" run \
      --interval "$interval" \
      --notify \
      --pulse-notify \
      --echo \
      >>"$STDOUT_LOG" 2>&1 &
    pid=$!
    echo "$pid" > "$PID_FILE"
    sleep 0.2
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "failed to start radio daemon"
      rm -f "$PID_FILE"
      tail -n 40 "$STDOUT_LOG" 2>/dev/null || true
      exit 1
    fi
    echo "radio started"
    echo "  PID: $pid"
    echo "  Feed: $FEED_LOG"
    echo "  Log: $STDOUT_LOG"
    ;;

  stop)
    cleanup_stale_pid
    if ! [[ -f "$PID_FILE" ]]; then
      if is_launchd_running; then
        echo "radio is managed by launchd (com.rhea.radio)"
        echo "use: bash scripts/rhea.sh maintainers stop"
        exit 0
      fi
      echo "radio not running"
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
    echo "radio stopped (PID $pid)"
    ;;

  status)
    cleanup_stale_pid
    if is_running; then
      echo "radio: running (PID $(cat "$PID_FILE"))"
    elif is_launchd_running; then
      echo "radio: running (launchd com.rhea.radio)"
    else
      echo "radio: not running"
    fi
    python3 "$REPO_ROOT/scripts/rhea_radio.py" status
    ;;

  once)
    python3 "$REPO_ROOT/scripts/rhea_radio.py" once --notify --echo
    ;;

  logs)
    n="${1:-40}"
    tail -n "$n" "$STDOUT_LOG"
    ;;

  tail)
    n="${1:-40}"
    python3 "$REPO_ROOT/scripts/rhea_radio.py" tail -n "$n"
    ;;

  listen)
    touch "$FEED_LOG"
    tail -f "$FEED_LOG"
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
