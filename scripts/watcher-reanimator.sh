#!/bin/bash
##############################################################################
# RHEA Watcher-Reanimator System
# Monitors Claude Code sessions for crashes/hangs
# Logs death events and notifies user
##############################################################################

set -e

REPO_ROOT="/Users/sa/rh.1"
WATCHER_DIR="${REPO_ROOT}/.watcher"
LOG_FILE="${WATCHER_DIR}/watcher.log"
DEATH_FILE="${WATCHER_DIR}/last-death.md"
PID_FILE="${WATCHER_DIR}/watcher.pid"

# Initialize
mkdir -p "$WATCHER_DIR"

##############################################################################
# Logging function
##############################################################################
log_event() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local message="[$timestamp] $1"
    echo "$message" >> "$LOG_FILE"
    echo "$message"
}

##############################################################################
# Record death event
##############################################################################
record_death() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S UTC%z')
    local branch=$(cd "$REPO_ROOT" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    local last_commit=$(cd "$REPO_ROOT" && git log -1 --pretty=format:"%h %s" 2>/dev/null || echo "unknown")
    local git_status=$(cd "$REPO_ROOT" && git status --short 2>/dev/null || echo "unknown")

    cat > "$DEATH_FILE" << EOF
# Claude Code Death Event

**Timestamp:** $timestamp

## Death Conditions
- Process: \`claude\` not found (pgrep -f "claude")
- Checked: $(date '+%Y-%m-%d at %H:%M:%S %Z')

## Git Context
- **Branch:** $branch
- **Last Commit:** $last_commit
- **Status:**
\`\`\`
$git_status
\`\`\`

## Recovery Steps
1. Check \`.watcher/watcher.log\` for timing details
2. \`cd $REPO_ROOT && git status\`
3. Review unsaved work in opened editors
4. Restart session: \`claude code\` or \`watcher-start.sh\`

## Notes
- Log: \`.watcher/watcher.log\`
- This file is automatically regenerated on each death
EOF

    log_event "DEATH RECORDED: Claude process not found"
}

##############################################################################
# Notify user
##############################################################################
notify_death() {
    osascript -e 'display notification "Claude died. Check .watcher/last-death.md" with title "RHEA WATCHER" sound name "Sosumi"' 2>/dev/null || true
    log_event "NOTIFICATION SENT: macOS alert dispatched"
}

##############################################################################
# Main loop
##############################################################################
main() {
    log_event "WATCHER STARTED (PID: $$)"
    echo $$ > "$PID_FILE"

    local claude_was_running=false

    while true; do
        # Check if claude process exists
        if pgrep -f "claude" > /dev/null 2>&1; then
            if [ "$claude_was_running" = false ]; then
                log_event "WATCHER: Claude process detected (running)"
                claude_was_running=true
            fi
        else
            # Claude is not running
            if [ "$claude_was_running" = true ]; then
                log_event "ALERT: Claude process died!"
                record_death
                notify_death
                claude_was_running=false
            fi
        fi

        # Sleep before next check
        sleep 10
    done
}

##############################################################################
# Signal handlers
##############################################################################
trap 'log_event "WATCHER STOPPED (signal)"; rm -f "$PID_FILE"; exit 0' SIGTERM SIGINT

##############################################################################
# Run
##############################################################################
main
