#!/bin/sh
# blueshoes-gecs-cron.sh
# Diskless GECS pipeline cron job for OpenWrt router (GL.iNet Beryl AX / blueshoes).
# Every 30min: git pull latest from rhea-project branch grok-mem0-native-identity (shallow clone to /tmp),
# then ensure reverse SSH tunnel to gcloud (self-healing nohup -R using EXACT flags from chain.txt),
# ensure clean Iowa egress via Passwall2/sing-box, log ONLY to /tmp (no flash wear).
# This IS the "бездисковый конвейер" for the router: pull + self-heal.

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
  log "WARN: git clone failed (auth/net/git not on router?); running with embedded ensure only"
  cd /tmp
fi

ensure_reverse_tunnel() {
  if pgrep -f 'ssh.*-R 0.0.0.0:2222:192.168.1.1:22.*35.224.79.36' >/dev/null 2>&1; then
    log "reverse tunnel ssh process alive"
    return 0
  fi
  log "reverse tunnel dead, re-launching nohup (exact chain logic, diskless)"
  mkdir -p /root/.ssh
  chmod 700 /root/.ssh || true
  # EXACT from /Users/sa/router-tunnel-start-chain.txt (the authoritative one)
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
  log "egress seen_ip=$IP (target 35.224.79.36 Iowa for clean US/low fraud)"
  if [ "$IP" = "35.224.79.36" ]; then
    log "egress CLEAN"
  else
    log "egress dirty/unknown -> restart passwall2/sing-box"
    /etc/init.d/passwall2 restart >> "$LOG" 2>&1 || true
    /etc/init.d/sing-box restart >> "$LOG" 2>&1 || true
    /etc/init.d/firewall reload >> "$LOG" 2>&1 || true
    sleep 4
  fi
}

run_higher_orchestrator() {
  if command -v python3 >/dev/null 2>&1 && [ -f gecs_workspace/gecs_orchestrator.py ]; then
    log "running pulled gecs_orchestrator.py (diskless)"
    python3 gecs_workspace/gecs_orchestrator.py --diskless --router-blueshoes --log /tmp/gecs-orchestrator.log >> "$LOG" 2>&1 || log "orchestrator non-fatal issues"
  else
    log "sh-only mode (no py or no pulled orchestrator)"
  fi
}

ensure_reverse_tunnel
ensure_clean_egress
run_higher_orchestrator

log "=== GECS diskless cron cycle complete ==="
