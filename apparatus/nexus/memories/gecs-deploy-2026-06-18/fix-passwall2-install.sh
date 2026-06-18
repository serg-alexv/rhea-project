#!/bin/bash
# Run this from the Mac when the reverse tunnel is UP (banner test shows SSH-2.0-dropbear on 35.224.79.36:2222).
# Transfers passwall2 core + sing-box + luci-app-passwall2 + stubby (user path) + mtr, then apk add --allow-untrusted.
# Uses full Mac network + full admin (sudo if needed) for the transfer via the gcloud forward.
# Updated for pw auth OFF on router (user: "все пароли на вход с роутера сняты!"): uses /Users/sa/.ssh/bshome key (pub must be in router /root/.ssh/authorized_keys).

set -euo pipefail

KEY="/Users/sa/.ssh/bshome"
G="35.224.79.36"
PKGS_DIR=/Users/sa/Downloads/passwall_pkgs
EX_DIR=/Users/sa/gecs_workspace/openwrt-passwall2-packages/extracted

echo "=== Checking tunnel banner ==="
if ! echo | nc -w 4 "$G" 2222 | grep -q 'SSH-2.0-dropbear'; then
  echo "ERROR: No dropbear banner on $G:2222. The nohup reverse on router is not live."
  echo "On the router shell, re-paste the chain from /Users/sa/router-tunnel-start-chain.txt or run blueshoes-complete-bootstrap.sh"
  echo "Wait for the nc test to show SSH-2.0-dropbear, then re-run this script."
  exit 1
fi
echo "Tunnel live."

echo "=== Re-scp passwall2 core (the one that failed) ==="
scp -i "$KEY" -P 2222 -O \
  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=60 \
  -o HostKeyAlgorithms=ssh-ed25519 \
  "$PKGS_DIR/passwall2_26.6.16-1_aarch64_cortex-a53.apk" root@"$G":/tmp/

echo "=== Scp sing-box (main dep for Reality in this release) ==="
scp -i "$KEY" -P 2222 -O \
  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=60 \
  -o HostKeyAlgorithms=ssh-ed25519 \
  "$EX_DIR/sing-box-1.13.13-r1.apk" root@"$G":/tmp/

echo "=== Scp luci-app-passwall2 (for LuCI UI to configure the Reality client) ==="
scp -i "$KEY" -P 2222 -O \
  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=60 \
  -o HostKeyAlgorithms=ssh-ed25519 \
  "$PKGS_DIR/luci-app-passwall2_26.6.16-1_all.ipk" root@"$G":/tmp/

echo "=== Scp mtr (as requested) ==="
MTR_SRC="/Users/sa/Downloads/mtr-0.96-r2.apk"
if [ -f "$MTR_SRC" ]; then
  scp -i "$KEY" -P 2222 -O \
    -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=60 \
    -o HostKeyAlgorithms=ssh-ed25519 \
    "$MTR_SRC" root@"$G":/tmp/mtr-0.96-r2.apk
else
  echo "mtr not found at $MTR_SRC - download mtr-0.96-r2.aarch64_cortex-a53.apk and place it"
fi

echo "=== Scp stubby (DoT for safe invisible routing, user clarif) ==="
STUBBY_SRC="/Users/sa/Downloads/stubby-0.4.3-r2.apk"
if [ -f "$STUBBY_SRC" ]; then
  scp -i "$KEY" -P 2222 -O \
    -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=60 \
    -o HostKeyAlgorithms=ssh-ed25519 \
    "$STUBBY_SRC" root@"$G":/tmp/stubby-0.4.3-r2.apk
else
  echo "stubby not found at $STUBBY_SRC - place stubby-0.4.3-r2.aarch64_cortex-a53.apk (or current) and re-run"
fi

echo "=== On router: apk add the packages (allow-untrusted) ==="
ssh -i "$KEY" -p 2222 \
  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=30 \
  -o HostKeyAlgorithms=ssh-ed25519 \
  root@"$G" 'cd /tmp && \
  ls -l passwall2_26.6.16-1_aarch64_cortex-a53.apk sing-box-1.13.13-r1.apk luci-app-passwall2_26.6.16-1_all.ipk mtr-0.96-r2.apk stubby-0.4.3-r2.apk 2>/dev/null || true && \
  apk add --allow-untrusted passwall2_26.6.16-1_aarch64_cortex-a53.apk sing-box-1.13.13-r1.apk luci-app-passwall2_26.6.16-1_all.ipk mtr-0.96-r2.apk stubby-0.4.3-r2.apk 2>/dev/null || true 2>&1 | tee /tmp/passwall2-fix.log'

echo "=== Verify installed ==="
ssh -i "$KEY" -p 2222 \
  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o HostKeyAlgorithms=ssh-ed25519 \
  root@"$G" 'echo "=== installed packages ==="; apk list --installed | grep -E "(passwall|sing-box|mtr|stubby)" ; echo "=== log ==="; tail -30 /tmp/passwall2-fix.log || true ; echo "=== luci passwall2 dir ==="; ls -d /usr/lib/lua/luci/model/cbi/passwall2* /usr/share/passwall2 2>/dev/null || echo "check in LuCI > Passwall2 after /etc/init.d/passwall2 start or reboot" ; echo "=== passwall2 in menu? ==="; ls /usr/lib/lua/luci/view/passwall2* 2>/dev/null | head -3 || true'

echo "Done. After this, go to LuCI > Passwall2 to add the Reality client node to gcloud (VLESS+REALITY, port 9443 usually, the sing-box inbound on ba-node-us). Then set policy or redirect for LAN to use it for clean US IP on Google endpoints. mtr for diagnostics. If errors, paste the /tmp/passwall2-fix.log"
