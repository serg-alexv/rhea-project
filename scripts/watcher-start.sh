#!/bin/bash
##############################################################################
# RHEA Watcher-Reanimator: Start Daemon
# Launches watcher-reanimator.sh as a background daemon via nohup
##############################################################################

set -e

REPO_ROOT="/Users/sa/rh.1"
SCRIPTS_DIR="${REPO_ROOT}/scripts"
WATCHER_DIR="${REPO_ROOT}/.watcher"
DAEMON_LOG="${WATCHER_DIR}/daemon.log"
PID_FILE="${WATCHER_DIR}/watcher.pid"

# Ensure directories exist
mkdir -p "$WATCHER_DIR"

# Check if watcher is already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Watcher is already running (PID: $OLD_PID)"
        exit 0
    else
        echo "Removing stale PID file"
        rm -f "$PID_FILE"
    fi
fi

# Start the watcher in background
nohup "$SCRIPTS_DIR/watcher-reanimator.sh" > "$DAEMON_LOG" 2>&1 &
NEW_PID=$!

echo "Watcher daemon started (PID: $NEW_PID)"
echo "Logs: $DAEMON_LOG"
echo "Death events recorded to: $WATCHER_DIR/last-death.md"
