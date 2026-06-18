#!/bin/sh
# blueshoes-gecs-cron.sh
# Diskless GECS pipeline cron job for OpenWrt router (GL.iNet Beryl AX / blueshoes).
# Every 30min: git pull latest from rhea-project branch grok-mem0-native-identity (shallow clone to /tmp),
# then ensure reverse SSH tunnel to gcloud (self-healing nohup -R), ensure clean Iowa egress via Passwall2/sing-box,
# log only to /tmp (no flash wear on overlay). 
# 
# Install (once tunnel live, from Mac):
#   scp -P 2222 -O /tmp/blueshoes-gecs-cron.sh root@35.224.79.36:/usr/local/bin/blueshoes-gecs-cron.sh
#   ssh -p 2222 root@35.224.79.36 'chmod +x /usr/local/bin/blueshoes-gecs-cron.sh; echo "*/30 * * * * /usr/local/bin/blueshoes-gecs-cron.sh >> /tmp/gecs-cron.log 2>&1" | crontab -'
# Then cron will self-maintain the setup. Update by pushing to branch; next cron cycle pulls.
#
# Requirements (one-time, when tunnel first up): git (apk add git if overlay allows or pre-placed .apk), the id_bshome key, dropbear+passwall2 configured.
# This is the "бездисковый конвейер": direct, no state on disk, ram-only workdir.

set -eu

LOG="/tmp/gecs-cron.log"
PIPE_DIR="/tmp/gecs-pipe-$$"
REPO_URL="https://github.com/timelabs-npo/rhea-project.git"
BRANCH="grok-mem0-native-identity"
GCLOUD_HOST="sa@35.224.79.36"
TUNNEL_PORT="2222"
ROUTER_LAN_IP="192.168.1.1"

ts() { date '+%Y-%m-%d %H:%M:%S'; }

log() {
  printf '[%s] %s\n' "$(ts)" "$*" >> "$LOG"
}

log "=== GECS diskless cron cycle start (blueshoes) ==="

# 1. diskless clone/pull (everything in tmpfs, rm on exit or next run)
cleanup() {
  cd /tmp
  rm -rf "$PIPE_DIR" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

mkdir -p "$PIPE_DIR"
cd "$PIPE_DIR"

log "diskless clone --depth 1 -b $BRANCH $REPO_URL"
if git clone --depth 1 -b "$BRANCH" "$REPO_URL" repo 2>&1 | tail -5 >> "$LOG"; then
  cd repo
  log "clone OK, HEAD=$(git rev-parse --short HEAD 2>/dev/null || echo '?')"
else
  log "WARN: git clone failed (auth? net?); will run local ensure with embedded logic only"
  cd /tmp
fi

# 2. the бездисковый конвейер core: ensure reverse tunnel (from chain, exact flags for ed25519-only)
ensure_reverse_tunnel() {
  if pgrep -f "ssh.*-R 0.0.0.0:2222:192.168.1.1:22.*35.224.79.36" >/dev/null 2>&1; then
    log "reverse tunnel ssh process alive"
    return 0
  fi
  log "reverse tunnel dead or missing, re-launching nohup loop (diskless)"
  # ensure key (id_bshome from prior setup)
  mkdir -p /root/.ssh
  chmod 700 /root/.ssh || true
  # exact launch from router-tunnel-start-chain.txt (nohup while, -4, ed25519 algos, ServerAlive, || sleep 10)
  nohup sh -c '
    while true; do
      ssh -i /root/.ssh/id_bshome -4 \
        -o IdentitiesOnly=yes \
        -o PubkeyAcceptedAlgorithms=ssh-ed25519 \
        -o HostKeyAlgorithms=ssh-ed25519 \
        -o StrictHostKeyChecking=no \
        -o UserKnownHostsFile=/dev/null \
        -o ServerAliveInterval=30 \
        -o ServerAliveCountMax=3 \
        -R 0.0.0.0:2222:192.168.1.1:22 '"$GCLOUD_HOST"' \
        || echo "tunnel died at $(date), retry in 10s" 
      sleep 10
    done
  ' >> /tmp/tun.log 2>&1 &
  log "tunnel re-launched (nohup pid $!)"
}

# 3. ensure clean egress (Iowa gcloud IP for low fraud). If not, restart routing services.
ensure_clean_egress() {
  # prefer wget (busybox) or curl if present; timeout to not hang cron
  IP=""
  if command -v wget >/dev/null 2>&1; then
    IP=$(wget -qO- --timeout=8 http://ifconfig.me 2>/dev/null || echo "")
  elif command -v curl >/dev/null 2>&1; then
    IP=$(curl -s --max-time 8 http://ifconfig.me 2>/dev/null || echo "")
  fi
  [ -z "$IP" ] && IP="unknown"
  log "current egress seen_ip=$IP (expect 35.224.79.36 for clean Iowa)"
  case "$IP" in
    35.224.79.36)
      log "egress CLEAN (Iowa gcloud) - good for trial"
      ;;
    *)
      log "egress NOT clean or unknown -> restarting passwall2/sing-box for clean routing"
      /etc/init.d/passwall2 restart >> "$LOG" 2>&1 || true
      /etc/init.d/sing-box restart >> "$LOG" 2>&1 || true
      # firewall/network reload if needed (light)
      /etc/init.d/firewall reload >> "$LOG" 2>&1 || true
      sleep 4
      ;;
  esac
}

# 4. optional: if python3 + pulled orchestrator present, run it (higher level конвейер)
run_higher_orchestrator() {
  if command -v python3 >/dev/null 2>&1 && [ -f gecs_workspace/gecs_orchestrator.py ]; then
    log "python3 + gecs_orchestrator.py found, running diskless cycle"
    python3 gecs_workspace/gecs_orchestrator.py --diskless --router-blueshoes --log /tmp/gecs-orchestrator.log >> "$LOG" 2>&1 || log "orchestrator cycle had issues (non-fatal)"
  else
    log "no python3 or no pulled gecs_orchestrator.py (sh-only mode)"
  fi
}

# execute the pipeline
ensure_reverse_tunnel
ensure_clean_egress
run_higher_orchestrator

log "=== GECS diskless cron cycle complete ==="
