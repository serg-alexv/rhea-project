#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WATCH_DIR="/Users/sa/rh.1/.watcher"
PID_FILE="$WATCH_DIR/watcher.pid"
mkdir -p "$WATCH_DIR"
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "Watcher already running (PID $(cat "$PID_FILE"))"
    exit 0
fi
nohup bash "$SCRIPT_DIR/watcher-reanimator.sh" > /dev/null 2>&1 &
echo "Watcher started (PID $!)"
echo "Log: $WATCH_DIR/watcher.log"
