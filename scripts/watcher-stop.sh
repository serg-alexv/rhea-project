#!/usr/bin/env bash
PID_FILE="/Users/sa/rh.1/.watcher/watcher.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"; rm -f "$PID_FILE"
        echo "Watcher stopped (PID $PID)"
    else
        rm -f "$PID_FILE"
        echo "Stale PID cleaned"
    fi
else
    echo "No watcher running"
fi
