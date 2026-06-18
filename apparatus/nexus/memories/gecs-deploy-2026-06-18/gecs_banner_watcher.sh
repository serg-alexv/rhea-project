#!/bin/bash
# gecs_banner_watcher.sh
# I run this (nohup). Polls for banner. On UP: fires the Mac activator (which does fix-passwall2 with bshome key).
# Logs to /tmp/gecs_banner_watcher.log + echoes.
# Per "you run ill watch" + user ✅🚀 on bg cleanup.

set -u
LOG="/tmp/gecs_banner_watcher.log"
G=35.224.79.36
PORT=2222
ACTIVATOR="/Users/sa/gecs_workspace/mac_post_bootstrap_activate.sh"
FIX="/Users/sa/fix-passwall2-install.sh"

ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { printf '[%s] %s\n' "$(ts)" "$*" | tee -a "$LOG"; }

log "=== GECS banner watcher started (pid $$) ==="
log "Will poll every 15s for SSH-2.0-dropbear on $G:$PORT"
log "On UP will run $ACTIVATOR (key auth /Users/sa/.ssh/bshome, no pw)"
log "User signal: Killed old bg + ✅✅✅🚀🚀🚀"

trap 'log "watcher exiting"; exit' INT TERM

while true; do
  if echo | nc -w 2 "$G" "$PORT" 2>/dev/null | grep -q 'SSH-2.0-dropbear'; then
    log "BANNER UP detected!"
    if [ -x "$ACTIVATOR" ]; then
      log "firing activator..."
      "$ACTIVATOR" >> "$LOG" 2>&1 || log "activator exit $?"
    elif [ -x "$FIX" ]; then
      log "activator missing, firing fix directly..."
      "$FIX" >> "$LOG" 2>&1 || log "fix exit $?"
    else
      log "no installer found"
    fi
    log "Mac side triggered. Check /tmp/passwall2-fix.log on router via future tunnel if needed."
    log "Watcher done (one-shot trigger)."
    break
  fi
  sleep 15
done
log "=== watcher cycle complete ==="
