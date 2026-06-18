#!/bin/bash
# Run this from the Mac when the reverse tunnel is UP (banner test shows SSH-2.0-dropbear on 35.224.79.36:2222).
# Transfers passwall2 core + sing-box + luci-app-passwall2 + stubby (user path) + mtr, then apk add --allow-untrusted.
# Uses full Mac network + full admin (sudo if needed) for the transfer via the gcloud forward.

set -euo pipefail

PW='atersage4Unan!!1'
G='35.224.79.36'
PKGS_DIR=/Users/sa/Downloads/passwall_pkgs
EX_DIR=/Users/sa/gecs_workspace/openwrt-passwall2-packages/extracted

echo "=== Checking tunnel banner ==="
if ! echo | nc -w 4 "$G" 2222 | grep -q 'SSH-2.0-dropbear'; then
  echo "ERROR: No dropbear banner on $G:2222. The nohup reverse on router is not live."
  echo "On the router shell, re-paste the chain from /Users/sa/router-tunnel-start-chain.txt"
  echo "Wait for the nc test in the chain to show SSH-2.0-dropbear, then re-run this script."
  exit 1
fi
echo "Tunnel live."

echo "=== Re-scp passwall2 core (the one that failed) ==="
sshpass -p "$PW" scp -P 2222 -O \
  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=60 \
  -o HostKeyAlgorithms=ssh-ed25519 \
  "$PKGS_DIR/passwall2_26.6.16-1_aarch64_cortex-a53.apk" root@"$G":/tmp/

echo "=== Scp sing-box (main dep for Reality in this release) ==="
sshpass -p "$PW" scp -P 2222 -O \
  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=60 \
  -o HostKeyAlgorithms=ssh-ed25519 \
  "$EX_DIR/sing-box-1.13.13-r1.apk" root@"$G":/tmp/

echo "=== Scp luci-app-passwall2 (for LuCI UI to configure the Reality client) ==="
sshpass -p "$PW" scp -P 2222 -O \
  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=60 \
  -o HostKeyAlgorithms=ssh-ed25519 \
  "$PKGS_DIR/luci-app-passwall2_26.6.16-1_all.ipk" root@"$G":/tmp/

echo "=== Scp stubby (DoT DNS, as requested) ==="
STUBBY_SRC="/Users/sa/Downloads/stubby-0.4.3-r2.apk"
if [ -f "$STUBBY_SRC" ]; then
  sshpass -p "$PW" scp -P 2222 -O \
    -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=60 \
    -o HostKeyAlgorithms=ssh-ed25519 \
    "$STUBBY_SRC" root@"$G":/tmp/stubby-0.4.3-r2.apk
else
  echo "stubby not found at $STUBBY_SRC - user provided path, please ensure file is there"
fi

echo "=== Scp mtr (as requested) ==="
MTR_SRC="/Users/sa/Downloads/mtr-0.96-r2.apk"
if [ -f "$MTR_SRC" ]; then
  sshpass -p "$PW" scp -P 2222 -O \
    -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=60 \
    -o HostKeyAlgorithms=ssh-ed25519 \
    "$MTR_SRC" root@"$G":/tmp/mtr-0.96-r2.apk
else
  echo "mtr not found at $MTR_SRC - download mtr-0.96-r2.aarch64_cortex-a53.apk and place it"
fi

echo "=== On router: apk add the packages (allow-untrusted) ==="
sshpass -p "$PW" ssh -p 2222 \
  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=30 \
  -o HostKeyAlgorithms=ssh-ed25519 \
  root@"$G" 'cd /tmp && \
  ls -l passwall2_26.6.16-1_aarch64_cortex-a53.apk sing-box-1.13.13-r1.apk luci-app-passwall2_26.6.16-1_all.ipk stubby-0.4.3-r2.apk mtr-0.96-r2.apk 2>/dev/null || true && \
  apk add --allow-untrusted passwall2_26.6.16-1_aarch64_cortex-a53.apk sing-box-1.13.13-r1.apk luci-app-passwall2_26.6.16-1_all.ipk stubby-0.4.3-r2.apk mtr-0.96-r2.apk 2>/dev/null || true 2>&1 | tee /tmp/passwall2-fix.log'

echo "=== Verify installed ==="
sshpass -p "$PW" ssh -p 2222 \
  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o HostKeyAlgorithms=ssh-ed25519 \
  root@"$G" 'echo "=== installed packages ==="; apk list --installed | grep -E "(passwall|sing-box|stubby|mtr)" ; echo "=== log ==="; tail -30 /tmp/passwall2-fix.log || true ; echo "=== luci passwall2 dir ==="; ls -d /usr/lib/lua/luci/model/cbi/passwall2* /usr/share/passwall2 2>/dev/null || echo "check in LuCI > Passwall2 after /etc/init.d/passwall2 start or reboot" ; echo "=== passwall2 in menu? ==="; ls /usr/lib/lua/luci/view/passwall2* 2>/dev/null | head -3 || true'

echo "Done. After this, go to LuCI > Passwall2 to add the Reality client node to gcloud (VLESS+REALITY, port 9443 usually, the sing-box inbound on ba-node-us). Then set policy or redirect for LAN to use it for clean US IP on Google endpoints. Stubby for DoT DNS, mtr for diagnostics. If errors, paste the /tmp/passwall2-fix.log"
