#!/bin/sh
# xray_router_client.sh - diskless Xray (xcore) client for router blueshoes
# Play with v2raya/xcore as alternative or addition to sing-box/Passwall2 for clean Iowa IP.
# Usage (once tunnel live, scp this + xray binary to router /tmp, run):
#   scp -P 2222 ... xray_router_client.sh root@35.224.79.36:/tmp/
#   scp -P 2222 ... xray root@35.224.79.36:/tmp/xray
#   ssh -p 2222 root@35.224.79.36 'cd /tmp; chmod +x xray_router_client.sh xray; ./xray_router_client.sh start'
# Then on iPhone, set manual SOCKS proxy to router_lan_ip:1080 for the probe app (or use for testing).
# For transparent, integrate with passwall or use redsocks (advanced play).
# Config params must match gcloud sing-box Reality inbound (get from gcloud /etc/sing-box/config.json inbounds[0]).

set -eu

XRAY_BIN="/tmp/xray"
CONFIG="/tmp/xray_client.json"
LOG="/tmp/xray_router.log"
PIDFILE="/tmp/xray.pid"

# TODO: Replace with real values from gcloud sing-box Reality server config
# (uuid from users[0].uuid or password, shortId, publicKey= the server's x25519 pub from privateKey, serverName e.g. gstatic.com or the one used, fingerprint chrome/safari etc.)
UUID="PUT_YOUR_UUID_FROM_G CLOUD_SINGBOX_HERE"
SHORT_ID="PUT_SHORTID_HERE"
PUBLIC_KEY="PUT_X25519_PUBLIC_KEY_HERE"
SERVER_NAME="gstatic.com"  # or whatever the sing-box uses for serverNames

cat > "$CONFIG" << CONF
{
  "log": {"loglevel": "warning"},
  "inbounds": [
    {
      "listen": "0.0.0.0",
      "port": 1080,
      "protocol": "socks",
      "settings": {"auth": "noauth", "udp": true}
    }
  ],
  "outbounds": [
    {
      "protocol": "vless",
      "settings": {
        "vnext": [{
          "address": "35.224.79.36",
          "port": 9443,
          "users": [{
            "id": "$UUID",
            "flow": "xtls-rprx-vision",
            "encryption": "none"
          }]
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
      },
      "tag": "gcloud-xray-reality"
    }
  ]
}
CONF

start() {
  if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
    echo "Xray already running"
    return
  fi
  echo "Starting Xray client (diskless)..."
  nohup "$XRAY_BIN" run -c "$CONFIG" > "$LOG" 2>&1 &
  echo $! > "$PIDFILE"
  sleep 2
  echo "Xray started, pid $(cat $PIDFILE). SOCKS on router:1080. Check $LOG"
  echo "Test: curl -x socks5h://127.0.0.1:1080 ifconfig.me"
}

stop() {
  if [ -f "$PIDFILE" ]; then
    kill $(cat "$PIDFILE") 2>/dev/null || true
    rm -f "$PIDFILE"
    echo "Xray stopped"
  fi
}

status() {
  if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
    echo "Running, pid $(cat $PIDFILE)"
    tail -5 "$LOG"
  else
    echo "Not running"
  fi
}

case "$1" in
  start) start ;;
  stop) stop ;;
  restart) stop; sleep 1; start ;;
  status) status ;;
  *) echo "Usage: $0 {start|stop|restart|status}"; exit 1 ;;
esac
