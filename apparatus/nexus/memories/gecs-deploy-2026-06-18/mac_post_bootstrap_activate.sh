#!/bin/bash
# mac_post_bootstrap_activate.sh
# Run this on the Mac (full admin granted) AFTER user has pasted and run blueshoes-complete-bootstrap.sh on the router.
# It waits (polls) for the banner on 35.224.79.36:2222, then automatically runs the full Passwall2/sing-box/stubby/mtr install via the tunnel.
# This makes the "when banner up -> I do the Mac side" automatic.
# Usage: bash /Users/sa/gecs_workspace/mac_post_bootstrap_activate.sh
# (or run in background while you do other things)

set -euo pipefail

G="35.224.79.36"
PORT=2222
INSTALL_SCRIPT="/Users/sa/fix-passwall2-install.sh"
LOG="/tmp/mac_activate_$(date +%Y%m%d_%H%M%S).log"

echo "=== Mac Post-Bootstrap Activator (prepared during user rest) ===" | tee -a "$LOG"
echo "Waiting for banner on $G:$PORT (the reverse tunnel from blueshoes-complete-bootstrap)..." | tee -a "$LOG"
echo "Once live, will auto-execute $INSTALL_SCRIPT (which does scp + apk --allow-untrusted for clean Iowa routing)." | tee -a "$LOG"
echo "Logs: $LOG" | tee -a "$LOG"

# Poll for banner (SSH-2.0-dropbear)
BANNER_UP=0
for i in {1..60}; do  # up to ~10-15 min if slow
  if echo | nc -w 3 "$G" "$PORT" 2>/dev/null | grep -q 'SSH-2.0-dropbear'; then
    echo "[$(date)] Banner UP! Proceeding to install..." | tee -a "$LOG"
    BANNER_UP=1
    break
  fi
  echo -n "." 
  sleep 10
done
echo

if [ "$BANNER_UP" -eq 0 ]; then
  echo "ERROR: Banner still not up after polling. Check router bootstrap run, pub append, and tun.log on router." | tee -a "$LOG"
  echo "Manual fallback: once banner appears, just run: $INSTALL_SCRIPT" | tee -a "$LOG"
  exit 1
fi

# Now run the install (it has its own banner check + scp with key /Users/sa/.ssh/bshome ; pw auth off)
echo "[$(date)] Running the install script..." | tee -a "$LOG"
if [ -x "$INSTALL_SCRIPT" ]; then
  "$INSTALL_SCRIPT" 2>&1 | tee -a "$LOG"
else
  echo "ERROR: $INSTALL_SCRIPT not executable or missing. Make sure it is updated with correct PKGS_DIR and paths." | tee -a "$LOG"
  exit 1
fi

echo "[$(date)] Install complete (or as far as script went). Verify on router:" | tee -a "$LOG"
echo "  ssh -i /Users/sa/.ssh/bshome -p 2222 -o StrictHostKeyChecking=no root@$G 'apk list --installed | grep -E passwall|sing|stubby|mtr ; ip route ; curl -s ifconfig.me'" | tee -a "$LOG"
echo "Then test clean IP from iPhone on blueshoes WiFi." | tee -a "$LOG"
echo "Cron should already be running from the bootstrap (30min self-heal + pull from rhea)." | tee -a "$LOG"

echo "=== Activator done. System should now be self-sustaining for the trial. ===" | tee -a "$LOG"
