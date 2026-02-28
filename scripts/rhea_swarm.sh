#!/usr/bin/env bash
# rhea_swarm.sh — Agent process manager + multiplexer
# The OpenClaw-equivalent for Rhea: daemon, mux, task loop, relay.
#
# Usage:
#   bash scripts/rhea_swarm.sh start          # start all agents in tmux
#   bash scripts/rhea_swarm.sh stop           # graceful shutdown
#   bash scripts/rhea_swarm.sh status         # show who's alive
#   bash scripts/rhea_swarm.sh attach         # attach to tmux session
#   bash scripts/rhea_swarm.sh relay          # run one relay cycle (outbox→inbox)
#   bash scripts/rhea_swarm.sh loop           # run continuous task loop
#   bash scripts/rhea_swarm.sh logs [agent]   # tail agent logs
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

SESSION="rhea-swarm"
LOG_DIR="$PROJECT_ROOT/opera/logs/swarm"
PID_DIR="$PROJECT_ROOT/opera/logs/swarm/pids"
RELAY_DIR="$PROJECT_ROOT/opera/ops/virtual-office"

mkdir -p "$LOG_DIR" "$PID_DIR"

# ─── Agent definitions ───
# name:command:model
AGENTS=(
  "rex:claude:opus"
  "orion:codex:gpt-5.3-codex"
  "gemini:python3 src/rhea_bridge.py serve:gemini-2.5-flash"
)

red()    { printf '\033[0;31m%s\033[0m\n' "$*"; }
green()  { printf '\033[0;32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[0;33m%s\033[0m\n' "$*"; }
dim()    { printf '\033[0;90m%s\033[0m\n' "$*"; }

# ─── STATUS ───
cmd_status() {
  echo "╔══════════════════════════════════════╗"
  echo "║       RHEA SWARM STATUS              ║"
  echo "╠══════════════════════════════════════╣"

  # Check tmux session
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    green "║ tmux session: $SESSION (alive)"
  else
    red   "║ tmux session: $SESSION (dead)"
  fi

  # Check each agent
  for agent_def in "${AGENTS[@]}"; do
    IFS=: read -r name cmd model <<< "$agent_def"
    pid_file="$PID_DIR/${name}.pid"
    if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
      local pid=$(cat "$pid_file")
      local uptime=$(ps -p "$pid" -o etime= 2>/dev/null | xargs)
      green "║ $name: alive (pid=$pid, up=$uptime, model=$model)"
    else
      red   "║ $name: dead"
    fi
  done

  # Task queue summary
  if [ -f "$PROJECT_ROOT/opera/tasks/state.json" ]; then
    local open=$(python3 -c "
import json
d=json.load(open('opera/tasks/state.json'))
s=d.get('tasks',d) if isinstance(d,dict) else {}
counts={'open':0,'claimed':0,'done':0,'blocked':0}
for t in s.values():
    st=t.get('status','open') if isinstance(t,dict) else 'open'
    if st in counts: counts[st]+=1
print(f'open={counts[\"open\"]} claimed={counts[\"claimed\"]} done={counts[\"done\"]} blocked={counts[\"blocked\"]}')
" 2>/dev/null || echo "parse error")
    echo "║ tasks: $open"
  fi

  # Relay status
  local inbox_count=$(find "$RELAY_DIR/inbox" -name "*.md" 2>/dev/null | wc -l | xargs)
  local outbox_count=$(find "$RELAY_DIR/outbox" -name "*.md" 2>/dev/null | wc -l | xargs)
  echo "║ relay: inbox=$inbox_count outbox=$outbox_count"

  echo "╚══════════════════════════════════════╝"
}

# ─── START ───
cmd_start() {
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    yellow "Session $SESSION already exists. Use 'attach' to view."
    return 0
  fi

  green "Starting Rhea Swarm..."

  # Create tmux session with first pane = status dashboard
  tmux new-session -d -s "$SESSION" -n "dashboard" \
    "watch -n 10 bash $SCRIPT_DIR/rhea_swarm.sh status"

  # Create a pane for each agent
  for agent_def in "${AGENTS[@]}"; do
    IFS=: read -r name cmd model <<< "$agent_def"
    local log_file="$LOG_DIR/${name}.log"

    tmux new-window -t "$SESSION" -n "$name"

    case "$cmd" in
      claude)
        # Rex — Claude Code in continuous mode
        tmux send-keys -t "$SESSION:$name" \
          "cd $PROJECT_ROOT && claude --resume 2>&1 | tee -a $log_file" Enter
        ;;
      codex)
        # Orion — Codex CLI
        tmux send-keys -t "$SESSION:$name" \
          "cd $PROJECT_ROOT && codex 2>&1 | tee -a $log_file" Enter
        ;;
      python3*)
        # Gemini bridge serve mode
        tmux send-keys -t "$SESSION:$name" \
          "cd $PROJECT_ROOT && $cmd 2>&1 | tee -a $log_file" Enter
        ;;
    esac

    green "  Started $name ($model)"
  done

  # Create relay window (auto-delivers outbox→inbox every 60s)
  tmux new-window -t "$SESSION" -n "relay" \
    "cd $PROJECT_ROOT && while true; do bash $SCRIPT_DIR/rhea_swarm.sh relay; sleep 60; done"

  # Create executor window (autonomous task loop)
  tmux new-window -t "$SESSION" -n "executor" \
    "cd $PROJECT_ROOT && python3 scripts/rhea_executor.py --daemon --agent rex --interval 120"

  # Create heartbeat window
  tmux new-window -t "$SESSION" -n "heartbeat" \
    "cd $PROJECT_ROOT && python3 scripts/rhea_heartbeat.py --daemon"

  green "Swarm started. Attach with: bash scripts/rhea_swarm.sh attach"
}

# ─── STOP ───
cmd_stop() {
  yellow "Stopping Rhea Swarm..."

  # Kill agent processes
  for pid_file in "$PID_DIR"/*.pid; do
    [ -f "$pid_file" ] || continue
    local pid=$(cat "$pid_file")
    local name=$(basename "$pid_file" .pid)
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null && green "  Stopped $name (pid=$pid)"
    fi
    rm -f "$pid_file"
  done

  # Kill tmux session
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux kill-session -t "$SESSION"
    green "  Killed tmux session"
  fi

  green "Swarm stopped."
}

# ─── ATTACH ───
cmd_attach() {
  if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    red "No swarm session. Start with: bash scripts/rhea_swarm.sh start"
    return 1
  fi
  tmux attach -t "$SESSION"
}

# ─── RELAY — move outbox → inbox ───
cmd_relay() {
  local moved=0
  local inbox="$RELAY_DIR/inbox"
  local outbox="$RELAY_DIR/outbox"

  # Pattern: AGENT_DATE_topic.md in outbox
  # Route to inbox as RELAY_DATE_FROM_to_TO.md
  for file in "$outbox"/*.md; do
    [ -f "$file" ] || continue
    local basename=$(basename "$file")

    # Extract sender from filename (first field before _)
    local sender=$(echo "$basename" | cut -d'_' -f1)

    # Check if already relayed (has a RELAY_ counterpart in inbox)
    if find "$inbox" -name "RELAY_*_${sender}_*" -newer "$file" 2>/dev/null | grep -q .; then
      continue  # Already delivered
    fi

    # Route to all other agents
    local ts=$(date -u +%Y%m%d_%H%M%S)
    for agent_def in "${AGENTS[@]}"; do
      IFS=: read -r target_name _ _ <<< "$agent_def"
      local target=$(echo "$target_name" | tr '[:lower:]' '[:upper:]')
      if [ "$target" != "$sender" ]; then
        local relay_name="RELAY_${ts}_${sender}_to_${target}.md"
        if [ ! -f "$inbox/$relay_name" ]; then
          cp "$file" "$inbox/$relay_name"
          moved=$((moved + 1))
        fi
      fi
    done
  done

  if [ "$moved" -gt 0 ]; then
    green "Relay: delivered $moved messages"
  else
    dim "Relay: no new messages"
  fi
}

# ─── TASK LOOP — autonomous claim/execute cycle ───
cmd_loop() {
  green "Starting autonomous task loop..."
  python3 - <<'PYEOF'
import sys, time, json, subprocess
sys.path.insert(0, "src")
from task_queue import TaskQueue
from datetime import datetime, timezone

q = TaskQueue()
AGENT = "rex"  # which agent this loop runs as
INTERVAL = 120  # seconds between cycles

while True:
    # 1. Check for stale tasks
    stale = q.stale_check(hours=2)
    if stale:
        print(f"[{datetime.now(timezone.utc).isoformat()}] STALE: {len(stale)} tasks")
        for t in stale:
            print(f"  - {t['id']}: {t['title']} (claimed by {t['claimed_by']})")

    # 2. Claim next available task
    task = q.claim(AGENT)
    if task:
        print(f"[{datetime.now(timezone.utc).isoformat()}] CLAIMED: {task['id']} — {task['title']}")
        # Execute via heartbeat check first
        subprocess.run(["python3", "scripts/rhea_heartbeat.py"], capture_output=True)
        # Mark done (actual execution would be delegated to agent)
        # For now: just log the claim. Real execution comes from the agent session.
    else:
        print(f"[{datetime.now(timezone.utc).isoformat()}] No available tasks. Sleeping {INTERVAL}s.")

    # 3. Run heartbeat
    subprocess.run(["python3", "scripts/rhea_heartbeat.py"], capture_output=True)

    # 4. Git push check
    result = subprocess.run(
        ["git", "log", "--oneline", "@{push}..HEAD"],
        capture_output=True, text=True
    )
    unpushed = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
    if unpushed > 0:
        print(f"  WARNING: {unpushed} unpushed commits")

    time.sleep(INTERVAL)
PYEOF
}

# ─── LOGS ───
cmd_logs() {
  local agent="${1:-}"
  if [ -z "$agent" ]; then
    tail -f "$LOG_DIR"/*.log
  else
    tail -f "$LOG_DIR/${agent}.log"
  fi
}

# ─── LaunchAgent install (persistent daemon) ───
cmd_install() {
  local plist_path="$HOME/Library/LaunchAgents/com.rhea.swarm.plist"
  cat > "$plist_path" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.rhea.swarm</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>python3</string>
    <string>${SCRIPT_DIR}/rhea_executor.py</string>
    <string>--daemon</string>
    <string>--agent</string>
    <string>rex</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${PROJECT_ROOT}</string>
  <key>StartInterval</key>
  <integer>120</integer>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/launchd-stdout.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/launchd-stderr.log</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    <key>HOME</key>
    <string>${HOME}</string>
  </dict>
</dict>
</plist>
PLIST

  launchctl bootout gui/$(id -u) "$plist_path" 2>/dev/null || true
  launchctl bootstrap gui/$(id -u) "$plist_path"
  green "Installed LaunchAgent: com.rhea.swarm"
  green "  Loop runs every 120s. Survives reboot."
  green "  Logs: $LOG_DIR/launchd-*.log"
}

cmd_uninstall() {
  local plist_path="$HOME/Library/LaunchAgents/com.rhea.swarm.plist"
  launchctl bootout gui/$(id -u) "$plist_path" 2>/dev/null || true
  rm -f "$plist_path"
  green "Removed LaunchAgent: com.rhea.swarm"
}

# ─── DISPATCH ───
case "${1:-status}" in
  start)     cmd_start ;;
  stop)      cmd_stop ;;
  status)    cmd_status ;;
  attach)    cmd_attach ;;
  relay)     cmd_relay ;;
  loop)      cmd_loop ;;
  logs)      cmd_logs "${2:-}" ;;
  install)   cmd_install ;;
  uninstall) cmd_uninstall ;;
  *)
    echo "Usage: rhea_swarm.sh {start|stop|status|attach|relay|loop|logs|install|uninstall}"
    exit 1
    ;;
esac
