#!/usr/bin/env bash
# Rhea Clipboard Daemon — install, start, stop, status
# Usage: bash scripts/rhea/clipboard_daemon.sh [install|start|stop|status|logs|uninstall]

set -euo pipefail
PLIST_SRC="packages/rhea-clipboard/com.rhea.clipboard.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.rhea.clipboard.plist"
LABEL="com.rhea.clipboard"

case "${1:-status}" in
  install)
    echo "── Installing rhea-clipboard ──"
    pip3 install -e packages/rhea-clipboard/ 2>&1 | tail -3
    echo ""
    echo "── Installing LaunchAgent ──"
    mkdir -p "$HOME/Library/LaunchAgents"
    cp "$PLIST_SRC" "$PLIST_DST"
    echo "  Installed: $PLIST_DST"
    echo ""
    echo "── Loading daemon ──"
    launchctl load "$PLIST_DST" 2>/dev/null || true
    echo "  Loaded. Check: bash scripts/rhea/clipboard_daemon.sh status"
    ;;

  start)
    if [ ! -f "$PLIST_DST" ]; then
      echo "Not installed. Run: bash scripts/rhea/clipboard_daemon.sh install"
      exit 1
    fi
    launchctl load "$PLIST_DST" 2>/dev/null || true
    launchctl start "$LABEL" 2>/dev/null || true
    echo "Started $LABEL"
    ;;

  stop)
    launchctl stop "$LABEL" 2>/dev/null || true
    echo "Stopped $LABEL"
    ;;

  status)
    echo "── Rhea Clipboard Daemon ──"
    if launchctl list "$LABEL" 2>/dev/null | grep -q PID; then
      PID=$(launchctl list "$LABEL" 2>/dev/null | grep '"PID"' | grep -o '[0-9]*')
      echo "  Status: RUNNING (PID $PID)"
    elif [ -f "$PLIST_DST" ]; then
      echo "  Status: INSTALLED but not running"
    else
      echo "  Status: NOT INSTALLED"
    fi
    echo ""
    if [ -f /tmp/rhea-clipboard.log ]; then
      echo "  Last log lines:"
      tail -5 /tmp/rhea-clipboard.log 2>/dev/null || echo "  (empty)"
    fi
    if [ -f /tmp/rhea-clipboard.err ]; then
      ERR_LINES=$(wc -l < /tmp/rhea-clipboard.err 2>/dev/null || echo "0")
      if [ "$ERR_LINES" -gt 0 ]; then
        echo "  Last errors:"
        tail -3 /tmp/rhea-clipboard.err
      fi
    fi
    ;;

  logs)
    echo "── stdout ──"
    tail -20 /tmp/rhea-clipboard.log 2>/dev/null || echo "(no log)"
    echo ""
    echo "── stderr ──"
    tail -20 /tmp/rhea-clipboard.err 2>/dev/null || echo "(no errors)"
    ;;

  uninstall)
    launchctl stop "$LABEL" 2>/dev/null || true
    launchctl unload "$PLIST_DST" 2>/dev/null || true
    rm -f "$PLIST_DST"
    echo "Uninstalled $LABEL"
    ;;

  *)
    echo "Usage: $0 [install|start|stop|status|logs|uninstall]"
    exit 1
    ;;
esac
