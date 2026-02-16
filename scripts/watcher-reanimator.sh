#!/usr/bin/env bash
# watcher-reanimator.sh — monitors Claude Code session, alerts on death
# Part of Rhea Chronos Protocol v3 — Agent 0 (Watcher)

WATCH_DIR="/Users/sa/rh.1/.watcher"
LOG="$WATCH_DIR/watcher.log"
DEATH_FILE="$WATCH_DIR/last-death.md"
PID_FILE="$WATCH_DIR/watcher.pid"
PROJECT_DIR="/Users/sa/rh.1"
CHECK_INTERVAL=10

mkdir -p "$WATCH_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"; }

notify_death() {
    osascript -e 'display notification "Claude session died. Check .watcher/last-death.md" with title "RHEA WATCHER" sound name "Sosumi"' 2>/dev/null || true
    for i in 1 2 3; do osascript -e 'beep' 2>/dev/null || true; sleep 0.3; done
}

notify_alive() {
    osascript -e 'display notification "Claude session detected alive." with title "RHEA WATCHER" sound name "Pop"' 2>/dev/null || true
}

save_death_state() {
    cat > "$DEATH_FILE" << DEATHEOF
# Last Session Death — $(date '+%Y-%m-%d %H:%M:%S %Z')
- **Branch:** $(git -C "$PROJECT_DIR" branch --show-current 2>/dev/null || echo "unknown")
- **Last commit:** $(git -C "$PROJECT_DIR" log -1 --oneline 2>/dev/null || echo "unknown")
- **Modified files:**
$(git -C "$PROJECT_DIR" status --short 2>/dev/null || echo "unknown")

## Recovery
1. cd $PROJECT_DIR && claude
2. Say: "Read docs/state.md, MEMORY.md, .watcher/last-death.md — resume previous work"
DEATHEOF
    log "Death state saved to $DEATH_FILE"
}

echo $$ > "$PID_FILE"
log "Watcher started (PID $$)"
was_alive=false

while true; do
    if pgrep -f "claude" > /dev/null 2>&1; then
        if [ "$was_alive" = false ]; then
            log "Claude session detected — monitoring"
            notify_alive
            was_alive=true
        fi
    else
        if [ "$was_alive" = true ]; then
            log "DEATH DETECTED — Claude process gone"
            save_death_state
            notify_death
            was_alive=false
        fi
    fi
    sleep "$CHECK_INTERVAL"
done
