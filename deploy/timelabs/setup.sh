#!/usr/bin/env bash
## Rhea Network Stack — timelabs.ru Bootstrap
##
## Run on timelabs.ru via SSH:
##   ssh root@timelabs.ru
##   curl -sL https://raw.githubusercontent.com/timelabs/rhea-project/stage4-release/deploy/timelabs/setup.sh | bash
##
## Or copy this directory and run:
##   scp -r deploy/timelabs/ root@timelabs.ru:/opt/rhea/
##   ssh root@timelabs.ru 'cd /opt/rhea && bash setup.sh'

set -euo pipefail

GREEN='\033[0;32m'
AMBER='\033[0;33m'
NC='\033[0m'
log() { echo -e "${GREEN}[rhea-setup]${NC} $*"; }
warn() { echo -e "${AMBER}[rhea-setup]${NC} $*"; }

DEPLOY_DIR="/opt/rhea"
DOMAIN="timelabs.ru"

log "Setting up Rhea network stack on $DOMAIN..."

# ── 1. Install Docker if missing ──
if ! command -v docker &>/dev/null; then
    log "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

if ! docker compose version &>/dev/null; then
    log "Installing Docker Compose plugin..."
    apt-get update && apt-get install -y docker-compose-plugin
fi

# ── 2. Create directory structure ──
mkdir -p "$DEPLOY_DIR"/{headscale/{config,data},wireguard/config,certs}

# ── 3. Copy configs ──
cp -n docker-compose.yml "$DEPLOY_DIR/" 2>/dev/null || true
cp -n headscale/config/*.yaml "$DEPLOY_DIR/headscale/config/" 2>/dev/null || true

# ── 4. Setup DNS subdomains (reminder) ──
warn "Make sure these DNS records point to $DOMAIN's IP:"
warn "  headscale.timelabs.ru → 31.177.76.32"
warn "  derp.timelabs.ru      → 31.177.76.32"
warn "  wg.timelabs.ru        → 31.177.76.32"

# ── 5. Generate TLS certs (Let's Encrypt or self-signed for now) ──
if ! command -v certbot &>/dev/null; then
    log "Installing certbot..."
    apt-get update && apt-get install -y certbot
fi

if [ ! -f "$DEPLOY_DIR/certs/cert.pem" ]; then
    log "Generating self-signed certs (replace with Let's Encrypt later)..."
    openssl req -x509 -newkey rsa:4096 -sha256 -days 365 -nodes \
        -keyout "$DEPLOY_DIR/certs/key.pem" \
        -out "$DEPLOY_DIR/certs/cert.pem" \
        -subj "/CN=derp.timelabs.ru" \
        -addext "subjectAltName=DNS:derp.timelabs.ru,DNS:headscale.timelabs.ru,DNS:wg.timelabs.ru"
    warn "Using self-signed certs. Run 'certbot certonly' for production certs."
fi

# ── 6. Open firewall ports ──
log "Configuring firewall..."
if command -v ufw &>/dev/null; then
    ufw allow 443/tcp    # Headscale + HTTPS
    ufw allow 8443/tcp   # DERP
    ufw allow 3478/udp   # STUN
    ufw allow 51820/udp  # WireGuard
    ufw allow 9090/tcp   # Headscale UI
    ufw reload
elif command -v firewall-cmd &>/dev/null; then
    firewall-cmd --permanent --add-port=443/tcp
    firewall-cmd --permanent --add-port=8443/tcp
    firewall-cmd --permanent --add-port=3478/udp
    firewall-cmd --permanent --add-port=51820/udp
    firewall-cmd --permanent --add-port=9090/tcp
    firewall-cmd --reload
else
    warn "No firewall manager found. Manually open ports: 443, 8443, 3478/udp, 51820/udp, 9090"
fi

# ── 7. Start services ──
cd "$DEPLOY_DIR"
log "Starting Rhea network stack..."
docker compose up -d

# ── 8. Create initial Headscale user ──
log "Waiting for Headscale to start..."
sleep 5
docker exec rhea-headscale headscale users create rhea || true

# ── 9. Generate pre-auth key for iOS app ──
log "Generating pre-auth key for iOS..."
PREAUTHKEY=$(docker exec rhea-headscale headscale preauthkeys create --user rhea --reusable --expiration 720h 2>/dev/null || echo "FAILED")
if [ "$PREAUTHKEY" != "FAILED" ]; then
    log "Pre-auth key (save this for iOS app config):"
    echo "  $PREAUTHKEY"
else
    warn "Pre-auth key generation failed. Run manually:"
    warn "  docker exec rhea-headscale headscale preauthkeys create --user rhea --reusable --expiration 720h"
fi

# ── 10. Status check ──
log ""
log "=== Rhea Network Stack Status ==="
docker compose ps
log ""
log "Endpoints:"
log "  Headscale:    https://headscale.timelabs.ru"
log "  DERP relay:   https://derp.timelabs.ru:8443"
log "  WireGuard:    wg.timelabs.ru:51820"
log "  Admin UI:     https://timelabs.ru:9090"
log ""
log "Next: Configure iOS app with Headscale URL and pre-auth key"
