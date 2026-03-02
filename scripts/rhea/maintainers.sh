#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
UID_NUM="$(id -u)"
DOMAIN="gui/$UID_NUM"

STATE_DIR="$REPO_ROOT/.rhea/maintainers"
mkdir -p "$STATE_DIR"

R_LABEL="com.rhea.radio"
N_LABEL="com.rhea.ndi"
Q_LABEL="com.rhea.queueguard"
F_LABEL="com.rhea.flowup"
G_LABEL="com.rhea.gemini"

R_PLIST="$STATE_DIR/$R_LABEL.plist"
N_PLIST="$STATE_DIR/$N_LABEL.plist"
Q_PLIST="$STATE_DIR/$Q_LABEL.plist"
F_PLIST="$STATE_DIR/$F_LABEL.plist"
G_PLIST="$STATE_DIR/$G_LABEL.plist"

R_LOG="$REPO_ROOT/.rhea/radio/radio.stdout.log"
N_LOG="$REPO_ROOT/.rhea/ndi/ndi.stdout.log"
Q_LOG="$REPO_ROOT/.rhea/queue_guard/queue_guard.stdout.log"
F_LOG="$REPO_ROOT/.rhea/flow_up/flow_up.stdout.log"
G_LOG="$REPO_ROOT/.rhea/gemini_guard/gemini_guard.stdout.log"

mkdir -p "$(dirname "$R_LOG")" "$(dirname "$N_LOG")" "$(dirname "$Q_LOG")" "$(dirname "$F_LOG")" "$(dirname "$G_LOG")"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/rhea/maintainers.sh start
  bash scripts/rhea/maintainers.sh stop
  bash scripts/rhea/maintainers.sh restart
  bash scripts/rhea/maintainers.sh status
  bash scripts/rhea/maintainers.sh logs [N]
EOF
}

write_plist() {
  local label="$1"
  local plist="$2"
  local stdout_log="$3"
  local stderr_log="$4"
  shift 4
  local args=("$@")

  {
    echo '<?xml version="1.0" encoding="UTF-8"?>'
    echo '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
    echo '<plist version="1.0"><dict>'
    echo "  <key>Label</key><string>$label</string>"
    echo "  <key>WorkingDirectory</key><string>$REPO_ROOT</string>"
    echo '  <key>ProgramArguments</key><array>'
    for a in "${args[@]}"; do
      local esc="${a//&/&amp;}"
      esc="${esc//</&lt;}"
      esc="${esc//>/&gt;}"
      echo "    <string>$esc</string>"
    done
    echo '  </array>'
    echo '  <key>RunAtLoad</key><true/>'
    echo '  <key>KeepAlive</key><true/>'
    echo "  <key>StandardOutPath</key><string>$stdout_log</string>"
    echo "  <key>StandardErrorPath</key><string>$stderr_log</string>"
    echo '</dict></plist>'
  } >"$plist"
}

svc_ref() {
  local label="$1"
  echo "$DOMAIN/$label"
}

svc_bootout() {
  local label="$1"
  launchctl bootout "$DOMAIN/$(basename "$label")" 2>/dev/null || true
}

svc_loaded() {
  local label="$1"
  launchctl print "$(svc_ref "$label")" >/dev/null 2>&1
}

install_all() {
  python3 "$REPO_ROOT/scripts/rhea_radio.py" prime >/dev/null || true
  python3 "$REPO_ROOT/scripts/ndi_watchdog.py" prime >/dev/null || true

  write_plist "$R_LABEL" "$R_PLIST" "$R_LOG" "$R_LOG" \
    "python3" "$REPO_ROOT/scripts/rhea_radio.py" "run" "--interval" "2" "--notify" "--pulse-notify" "--echo"
  write_plist "$N_LABEL" "$N_PLIST" "$N_LOG" "$N_LOG" \
    "python3" "$REPO_ROOT/scripts/ndi_watchdog.py" "run" "--interval" "8" "--notify" "--echo" "--red-pixel"
  write_plist "$Q_LABEL" "$Q_PLIST" "$Q_LOG" "$Q_LOG" \
    "python3" "$REPO_ROOT/scripts/rhea_queue_guard.py" "run" "--interval" "30" "--notify" "--echo"
  write_plist "$F_LABEL" "$F_PLIST" "$F_LOG" "$F_LOG" \
    "python3" "$REPO_ROOT/scripts/flow_up_guard.py" "run" "--interval" "20" "--notify" "--echo" "--alarm-mode" "adaptive"
  write_plist "$G_LABEL" "$G_PLIST" "$G_LOG" "$G_LOG" \
    "python3" "$REPO_ROOT/scripts/gemini_guard.py" "run" "--interval" "45" "--notify" "--echo"
}

start_one() {
  local label="$1"
  local plist="$2"
  launchctl bootout "$(svc_ref "$label")" 2>/dev/null || true
  launchctl bootstrap "$DOMAIN" "$plist"
  launchctl kickstart -k "$(svc_ref "$label")"
}

start_all() {
  install_all
  start_one "$R_LABEL" "$R_PLIST"
  start_one "$N_LABEL" "$N_PLIST"
  start_one "$Q_LABEL" "$Q_PLIST"
  start_one "$F_LABEL" "$F_PLIST"
  start_one "$G_LABEL" "$G_PLIST"
  echo "maintainers started via launchd"
}

stop_all() {
  launchctl bootout "$(svc_ref "$R_LABEL")" 2>/dev/null || true
  launchctl bootout "$(svc_ref "$N_LABEL")" 2>/dev/null || true
  launchctl bootout "$(svc_ref "$Q_LABEL")" 2>/dev/null || true
  launchctl bootout "$(svc_ref "$F_LABEL")" 2>/dev/null || true
  launchctl bootout "$(svc_ref "$G_LABEL")" 2>/dev/null || true
  echo "maintainers stopped"
}

status_one() {
  local label="$1"
  if svc_loaded "$label"; then
    local line
    line="$(launchctl print "$(svc_ref "$label")" | rg -m1 'state = |pid = ' || true)"
    echo "$label: running ${line:+($line)}"
  else
    echo "$label: not running"
  fi
}

status_all() {
  status_one "$R_LABEL"
  status_one "$N_LABEL"
  status_one "$Q_LABEL"
  status_one "$F_LABEL"
  status_one "$G_LABEL"
}

cmd="${1:-help}"
shift || true

case "$cmd" in
  start) start_all ;;
  stop) stop_all ;;
  restart) stop_all; start_all ;;
  status) status_all ;;
  logs)
    n="${1:-80}"
    echo "--- radio"
    tail -n "$n" "$R_LOG" 2>/dev/null || true
    echo "--- ndi"
    tail -n "$n" "$N_LOG" 2>/dev/null || true
    echo "--- queue_guard"
    tail -n "$n" "$Q_LOG" 2>/dev/null || true
    echo "--- flow_up"
    tail -n "$n" "$F_LOG" 2>/dev/null || true
    echo "--- gemini_guard"
    tail -n "$n" "$G_LOG" 2>/dev/null || true
    ;;
  help|--help|-h) usage ;;
  *)
    echo "unknown command: $cmd"
    usage
    exit 1
    ;;
esac
