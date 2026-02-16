#!/bin/bash
##############################################################################
# RHEA Watcher-Reanimator: Stop Daemon
# Gracefully terminates the watcher daemon
##############################################################################

set -e

REPO_ROOT="/Users/sa/rh.1"
WATCHER_DIR="${REPO_ROOT}/.watcher"
PID_FILE="${WATCHER_DIR}/watcher.pid"

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo "Watcher is not running (no PID file found)"
    exit 0
fi

PID=$(cat "$PID_FILE")

# Check if process is actually running
if ! kill -0 "$PID" 2>/dev/null; then
    echo "Watcher process (PID: $PID) is not running"
    rm -f "$PID_FILE"
    exit 0
fi

# Terminate gracefully
echo "Stopping watcher daemon (PID: $PID)..."
kill -TERM "$PID"

# Wait for graceful shutdown (up to 5 seconds)
for i in {1..5}; do
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "Watcher daemon stopped"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# Force kill if still running
echo "Force killing watcher daemon..."
kill -9 "$PID" 2>/dev/null || true
rm -f "$PID_FILE"
echo "Watcher daemon forcefully terminated"
