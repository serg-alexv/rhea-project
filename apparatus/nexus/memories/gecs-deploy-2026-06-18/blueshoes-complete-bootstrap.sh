#!/bin/sh
# blueshoes-complete-bootstrap.sh
# Decision: single block to run on router after reboot.
# Does: uci + dropbear, key, writes the FULL current blueshoes-gecs-cron.sh (from our deployed memory),
# sets it up as the persistent конвейер, launches the initial tunnel nohup (exact from chain),
# installs crontab, runs first cycle, verifies.
# After this, the cron (which pulls from grok-mem0-native-identity) owns the "life".
# User pastes this once per major reset. Cron handles the rest (30min self-heal + updates).

set -eu

echo "=== 1. DROPBEAR FOR REVERSE (lan + GatewayPorts) ==="
uci set dropbear.@dropbear[0].Interface=lan
uci set dropbear.@dropbear[0].PasswordAuth=off
uci set dropbear.@dropbear[0].RootPasswordAuth=off
uci set dropbear.@dropbear[0].GatewayPorts=on 2>/dev/null || true
uci commit dropbear
/etc/init.d/dropbear restart
sleep 2
uci show dropbear.@dropbear[0]

echo "=== 2. KEY (id_bshome) ==="
mkdir -p /root/.ssh
chmod 700 /root/.ssh
chown root:root /root/.ssh 2>/dev/null || true
# Ensure fresh valid ed25519 for router -> gcloud sa@ (outbound for -R)
if [ ! -f /root/.ssh/id_bshome ] || ! ssh-keygen -y -f /root/.ssh/id_bshome >/dev/null 2>&1; then
  echo "Generating fresh id_bshome (no valid key found)"
  ssh-keygen -t ed25519 -f /root/.ssh/id_bshome -N "" -C "bshome-router-$(date +%F)"
  chmod 600 /root/.ssh/id_bshome
  chown root:root /root/.ssh/id_bshome
fi
echo "=== COPY THIS PUB (append to gcloud sa ~/.ssh/authorized_keys from your Mac) ==="
cat /root/.ssh/id_bshome.pub

echo "=== 3. WRITE THE CRON SCRIPT (exact from our rhea memory dump) ==="
cat > /usr/local/bin/blueshoes-gecs-cron.sh << 'CRONSCRIPT'
#!/bin/sh
# blueshoes-gecs-cron.sh
# (embedded exact content from the deployed version in gecs-deploy-2026-06-18)
# Diskless, /tmp only, 30min git pull from grok-mem0-native-identity, ensure tunnel + clean Iowa egress.

set -eu
LOG="/tmp/gecs-cron.log"
PIPE_DIR="/tmp/gecs-pipe-$$"
REPO_URL="https://github.com/timelabs-npo/rhea-project.git"
BRANCH="grok-mem0-native-identity"

ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { printf '[%s] %s\n' "$(ts)" "$*" >> "$LOG"; }

log "=== GECS diskless cron cycle start (blueshoes) ==="
cleanup() { cd /tmp 2>/dev/null; rm -rf "$PIPE_DIR" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

mkdir -p "$PIPE_DIR"
cd "$PIPE_DIR"

log "diskless clone --depth 1 -b $BRANCH $REPO_URL"
if git clone --depth 1 -b "$BRANCH" "$REPO_URL" repo 2>&1 | tail -5 >> "$LOG"; then
  cd repo
  log "clone OK, HEAD=$(git rev-parse --short HEAD 2>/dev/null || echo '?')"
else
  log "WARN: clone failed; embedded ensure only"
  cd /tmp
fi

ensure_reverse_tunnel() {
  if pgrep -f 'ssh.*-R 0.0.0.0:2222:192.168.1.1:22.*35.224.79.36' >/dev/null 2>&1; then
    log "reverse tunnel ssh process alive"
    return 0
  fi
  log "reverse tunnel dead, re-launching nohup (exact chain logic)"
  mkdir -p /root/.ssh
  chmod 700 /root/.ssh || true
  nohup sh -c '
    while true; do
      ssh -i /root/.ssh/id_bshome -4 \
        -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
        -o PubkeyAcceptedAlgorithms=ssh-ed25519 -o HostKeyAlgorithms=ssh-ed25519 \
        -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ConnectTimeout=15 \
        -R 0.0.0.0:2222:192.168.1.1:22 \
        sa@35.224.79.36 \
        || echo "[loop] died at $(date) - sleep 10" && sleep 10
    done
  ' >> /tmp/tun.log 2>&1 &
  log "tunnel re-launched (nohup pid $!)"
}

ensure_clean_egress() {
  IP=""
  if command -v wget >/dev/null 2>&1; then
    IP=$(wget -qO- --timeout=8 http://ifconfig.me 2>/dev/null || echo "")
  elif command -v curl >/dev/null 2>&1; then
    IP=$(curl -s --max-time 8 http://ifconfig.me 2>/dev/null || echo "")
  fi
  [ -z "$IP" ] && IP="unknown"
  log "egress seen_ip=$IP (target 35.224.79.36 Iowa)"
  if [ "$IP" = "35.224.79.36" ]; then
    log "egress CLEAN"
  else
    log "egress dirty -> restart passwall2/sing-box"
    /etc/init.d/passwall2 restart >> "$LOG" 2>&1 || true
    /etc/init.d/sing-box restart >> "$LOG" 2>&1 || true
    /etc/init.d/firewall reload >> "$LOG" 2>&1 || true
    sleep 4
  fi
}

run_higher_orchestrator() {
  if command -v python3 >/dev/null 2>&1 && [ -f gecs_workspace/gecs_orchestrator.py ]; then
    log "running pulled gecs_orchestrator.py"
    python3 gecs_workspace/gecs_orchestrator.py --diskless --router-blueshoes --log /tmp/gecs-orchestrator.log >> "$LOG" 2>&1 || log "orchestrator non-fatal"
  else
    log "sh-only mode"
  fi
}

ensure_reverse_tunnel
ensure_clean_egress
run_higher_orchestrator

log "=== GECS diskless cron cycle complete ==="
CRONSCRIPT
chmod +x /usr/local/bin/blueshoes-gecs-cron.sh
echo "Cron script installed."

echo "=== 4. INSTALL CRON (every 30 min) ==="
echo "*/30 * * * * /usr/local/bin/blueshoes-gecs-cron.sh >> /tmp/gecs-cron.log 2>&1" | crontab -
crontab -l | tail -3

echo "=== 5. LAUNCH INITIAL TUNNEL (exact from chain) ==="
nohup sh -c "
while true; do
  ssh -i /root/.ssh/id_bshome -4 \
    -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o PubkeyAcceptedAlgorithms=ssh-ed25519 -o HostKeyAlgorithms=ssh-ed25519 \
    -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ConnectTimeout=15 \
    -R 0.0.0.0:2222:192.168.1.1:22 \
    sa@35.224.79.36 \
    || echo \"[loop] died at \$(date) - sleep 10\" && sleep 10
done
" >> /tmp/tun.log 2>&1 &
TUN_PID=$!
echo "Tunnel nohup pid $TUN_PID"
sleep 5

echo "=== 6. FIRST MANUAL CRON CYCLE (to kick off immediately) =="
/usr/local/bin/blueshoes-gecs-cron.sh || true

echo "=== 7. VERIFY ==="
echo "=== processes ==="
ps w | grep -E 'nohup|ssh.*35.224|blueshoes-gecs-cron' | grep -v grep || echo "(check manually)"
echo "=== banner test ==="
echo | nc -w 5 35.224.79.36 2222 | head -c 80 | cat -v ; echo
echo "=== logs (last 10 lines) ==="
tail -10 /tmp/tun.log /tmp/gecs-cron.log 2>/dev/null | cat

echo "=== DONE. After this, cron owns it. Reboot test: cron will re-launch on next tick. ==="
echo "If banner is up here, tell the agent to run the Mac scp/apk side."

echo ""
echo "=== POST-INSTALL (on your Mac, after this block succeeds and banner is up) ==="
echo "Run this on Mac (it will wait for banner and auto-do the Passwall2 + sing-box + stubby + mtr install):"
echo "  bash /Users/sa/gecs_workspace/mac_post_bootstrap_activate.sh"
echo ""
echo "Or manually once you see banner:"
echo "  /Users/sa/fix-passwall2-install.sh"
echo ""
echo "After install: check clean IP, then iPhone probe can start measuring for the trial."
echo "Cron is already set (*/30) and will keep everything alive + pull latest from rhea grok-mem0-native-identity."
