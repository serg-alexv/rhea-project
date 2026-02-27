#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

STATE_DIR="$REPO_ROOT/.rhea/autonudge"
PID_FILE="$STATE_DIR/autonudge.pid"
META_FILE="$STATE_DIR/autonudge.meta.json"
STDOUT_LOG="$STATE_DIR/autonudge.stdout.log"
AUDIT_LOG="$REPO_ROOT/.entire/logs/autonudge.jsonl"

mkdir -p "$STATE_DIR" "$(dirname "$AUDIT_LOG")"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/rhea/autonudge.sh start --target-pane <pane> [autonudge_tmux args...]
  bash scripts/rhea/autonudge.sh stop
  bash scripts/rhea/autonudge.sh status
  bash scripts/rhea/autonudge.sh verify [--strict]
  bash scripts/rhea/autonudge.sh logs [N]
  bash scripts/rhea/autonudge.sh audit [N]

Examples:
  bash scripts/rhea/autonudge.sh start --target-pane %12 --mode nudge --idle-sec 60 --max-total-nudges 5
  bash scripts/rhea/autonudge.sh status
  bash scripts/rhea/autonudge.sh verify
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

extract_target_pane() {
  local prev=""
  for arg in "$@"; do
    if [[ "$prev" == "--target-pane" ]]; then
      printf '%s\n' "$arg"
      return 0
    fi
    case "$arg" in
      --target-pane=*)
        printf '%s\n' "${arg#--target-pane=}"
        return 0
        ;;
    esac
    prev="$arg"
  done
  return 1
}

write_meta() {
  local pid="$1"
  local target="$2"
  shift 2
  python3 - "$META_FILE" "$pid" "$target" "$@" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

meta_path = Path(sys.argv[1])
pid = int(sys.argv[2])
target = sys.argv[3]
argv = sys.argv[4:]
meta = {
    "pid": pid,
    "target_pane": target,
    "started_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "argv": argv,
}
meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
}

cmd="${1:-help}"
shift || true

case "$cmd" in
  start)
    cleanup_stale_pid
    if is_running; then
      echo "autonudge already running (PID $(cat "$PID_FILE"))"
      exit 0
    fi

    target="$(extract_target_pane "$@" || true)"
    if [[ -z "${target:-}" ]]; then
      echo "missing --target-pane"
      usage
      exit 2
    fi

    if ! tmux display-message -p -t "$target" "#{pane_id}" >/dev/null 2>&1; then
      echo "target pane not found: $target"
      exit 3
    fi

    daemon_cmd=(
      python3 "$REPO_ROOT/scripts/rhea/autonudge_tmux.py"
      --log-path "$AUDIT_LOG"
      "$@"
    )
    nohup "${daemon_cmd[@]}" >>"$STDOUT_LOG" 2>&1 &
    pid=$!
    echo "$pid" >"$PID_FILE"
    write_meta "$pid" "$target" "${daemon_cmd[@]}"
    sleep 0.2

    if ! kill -0 "$pid" 2>/dev/null; then
      echo "failed to start autonudge daemon"
      rm -f "$PID_FILE"
      tail -n 40 "$STDOUT_LOG" 2>/dev/null || true
      exit 4
    fi

    echo "autonudge started"
    echo "  PID: $pid"
    echo "  Target: $target"
    echo "  Audit log: $AUDIT_LOG"
    echo "  Stdout log: $STDOUT_LOG"
    ;;

  stop)
    cleanup_stale_pid
    if ! [[ -f "$PID_FILE" ]]; then
      echo "autonudge not running"
      exit 0
    fi

    pid="$(cat "$PID_FILE")"
    kill "$pid" 2>/dev/null || true
    for _ in 1 2 3 4 5 6; do
      if ! kill -0 "$pid" 2>/dev/null; then
        break
      fi
      sleep 0.2
    done
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi

    rm -f "$PID_FILE"
    echo "autonudge stopped (PID $pid)"
    ;;

  status)
    cleanup_stale_pid
    if is_running; then
      echo "autonudge: running (PID $(cat "$PID_FILE"))"
    else
      echo "autonudge: not running"
    fi

    if [[ -f "$META_FILE" ]]; then
      echo "--- meta ---"
      cat "$META_FILE"
    fi

    if [[ -f "$AUDIT_LOG" ]]; then
      echo "--- audit tail ---"
      tail -n 3 "$AUDIT_LOG"
    else
      echo "audit log missing: $AUDIT_LOG"
    fi
    ;;

  verify)
    python3 "$REPO_ROOT/scripts/rhea/verify_jsonl_chain.py" --path "$AUDIT_LOG" "$@"
    ;;

  logs)
    n="${1:-40}"
    tail -n "$n" "$STDOUT_LOG"
    ;;

  audit)
    n="${1:-40}"
    tail -n "$n" "$AUDIT_LOG"
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
