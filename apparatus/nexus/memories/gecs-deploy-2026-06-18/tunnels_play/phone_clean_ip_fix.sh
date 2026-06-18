#!/bin/sh
# phone_clean_ip_fix.sh - Fix iPhone not getting clean Iowa IP via router
# Run on router (after blueshoes-complete-bootstrap.sh)
# Primary for phone: Xray client exposing SOCKS 1080 -- set manual proxy on iPhone.
# Alternative: fix Passwall2 transparent for LAN.
# Usage on router: ./phone_clean_ip_fix.sh all
# Then on iPhone: blueshoes WiFi + manual SOCKS 192.168.1.1:1080 (or the passwall transparent if set).

set -eu

XRAY_BIN="/tmp/xray"
XRAY_CONFIG="/tmp/xray_phone.json"
LOG="/tmp/phone_fix.log"

echo "=== Phone Clean IP Fix (iPhone probe) ===" | tee -a "$LOG"
echo "Date: $(date)" | tee -a "$LOG"

deploy_xray_for_phone() {
  if [ ! -x "$XRAY_BIN" ]; then
    echo "Xray binary missing at $XRAY_BIN. From Mac (tunnel live): scp -P 2222 /Users/sa/gecs_workspace/tunnels_play/xray/xray root@35.224.79.36:/tmp/xray"
    echo "Then chmod +x /tmp/xray on router."
    return 1
  fi

  # TODO: fill real from gcloud sing-box config.
  # Fetch: from Mac with full net or when tunnel up: ssh sa@35.224.79.36 'cat /etc/sing-box/config.json' | grep -A30 -E 'reality|inbounds'
  # Or from router if can reach gcloud outbound.
  UUID="PUT_UUID_FROM_GCLOUD_HERE"
  SHORT_ID="PUT_SHORTID_HERE"
  PUBLIC_KEY="PUT_PUBLIC_KEY_HERE"
  SERVER_NAME="gstatic.com"  # match sing-box serverNames

  cat > "$XRAY_CONFIG" << CONF
{
  "log": {"loglevel": "warning"},
  "inbounds": [{
    "listen": "0.0.0.0",
    "port": 1080,
    "protocol": "socks",
    "settings": {"auth": "noauth", "udp": true}
  }],
  "outbounds": [{
    "protocol": "vless",
    "settings": {
      "vnext": [{
        "address": "35.224.79.36",
        "port": 9443,
        "users": [{"id": "$UUID", "flow": "xtls-rprx-vision", "encryption": "none"}]
      }]
    },
    "streamSettings": {
      "network": "tcp",
      "security": "reality",
      "realitySettings": {
        "serverName": "$SERVER_NAME",
        "fingerprint": "chrome",
        "shortId": "$SHORT_ID",
        "publicKey": "$PUBLIC_KEY",
        "spiderX": ""
      }
    }
  }]
}
CONF

  echo "Starting Xray phone proxy (SOCKS :1080)..." | tee -a "$LOG"
  # SAFE: pkill by exact name, not -f with path (avoids wrapper self-match)
  pkill -x xray 2>/dev/null || true
  nohup "$XRAY_BIN" run -c "$XRAY_CONFIG" > /tmp/xray_phone.log 2>&1 &
  XRAY_PID=$!
  sleep 3
  if kill -0 $XRAY_PID 2>/dev/null; then
    echo "Xray running pid $XRAY_PID. SOCKS on 192.168.1.1:1080" | tee -a "$LOG"
    echo "iPhone: WiFi blueshoes > Configure Proxy > Manual > 192.168.1.1 1080" | tee -a "$LOG"
    echo "In probe: use path with proxy_override or manual." | tee -a "$LOG"
    echo "Test: Safari ifconfig.me -> should be 35.224.79.36" | tee -a "$LOG"
  else
    echo "Xray start failed. See /tmp/xray_phone.log" | tee -a "$LOG"
  fi
}

fix_passwall_transparent() {
  echo "Passwall2 transparent fix for LAN (phone)..." | tee -a "$LOG"
  echo "Ensure in LuCI or uci:"
  echo "  passwall2 global enabled=1, node= gcloud-reality, proxy_mode=REDIR, lan_if=lan"
  echo "  Restart services."
  pkill -x passwall2 2>/dev/null || true   # safe
  /etc/init.d/passwall2 restart 2>/dev/null || echo "passwall2 not in init or not installed"
  echo "If not installed: from Mac run the fix-passwall2-install.sh when banner up."
}

phone_checks() {
  echo "iPhone must-use checks:" | tee -a "$LOG"
  echo "- Connect ONLY to blueshoes WiFi. Turn OFF mobile data/cellular."
  echo "- Forget network, rejoin."
  echo "- In probe app: claim a 'router-xray-socks' or 'blueshoes + gcloud' measure task."
  echo "- Expected: seen_ip=35.224.79.36, no fraud flags, real iOS UA/timings."
  echo "Router side: ensure no leaks (stubby DNS, no direct WAN rules)."
  echo "Current processes:"
  ps w | grep -E 'xray|passwall|sing-box|dropbear' | grep -v grep | tee -a "$LOG" || true
}

quick_test() {
  echo "Router egress test:"
  (curl -s --max-time 8 ifconfig.me || echo "fail") | tee -a "$LOG"
  echo "If shows 35.224.79.36: clean path live. Phone proxy should inherit."
}

case "${1:-all}" in
  xray) deploy_xray_for_phone ;;
  passwall) fix_passwall_transparent ;;
  checks) phone_checks ;;
  test) quick_test ;;
  all)
    deploy_xray_for_phone || true
    fix_passwall_transparent || true
    phone_checks
    quick_test
    ;;
  *) echo "Usage: $0 [xray|passwall|checks|test|all]"; exit 1 ;;
esac

echo "=== Done. Log: $LOG ===" | tee -a "$LOG"
echo "Next: test probe on phone, report to Notion. Update this script with real UUID etc."

# === A2A Structured (new CoT-language) ===
# Agent Card: PhoneFixAgent
# Capabilities: router Xray/SOCKS deploy, Passwall policy fix, iPhone proxy config, clean IP verification for probe
# Skills:
#   - deploy_xray_socks: expose 1080 for manual phone proxy (primary for iPhone)
#   - fix_passwall_lan: ensure transparent for all LAN including phone MAC
#   - phone_checks: force WiFi only, no cellular, test seen_ip
# Task: fix_phone_ip
# From: Grok-TunnelAgent (a2a mode)
# To: User (lead) + router (via bootstrap)
# Input: user report "phone нихуя не тащит", current bootstrap + Xray binary
# Output: script commands + iPhone manual proxy steps + expected probe results (seen_ip=35.224.79.36)
# Status: in_progress
# Evidence: this file, ORION phone report, tunnels_play/xray
# Verification: after run, iPhone ifconfig.me == 35.224.79.36, probe measure shows clean + no fraud flags
# Coordination: user runs on router, sets on phone, reports to Notion; then next task clean_ip_verify
