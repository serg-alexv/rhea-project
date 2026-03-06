#!/bin/bash
# build_macos.sh — Build macOS system daemons and create distribution packages

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="${1:---output}"
OUTPUT_DIR="${OUTPUT_DIR#--output }"
OUTPUT_DIR="${OUTPUT_DIR:-.}"

echo "🍎 Building macOS Rhea Distribution"
echo "===================================="

mkdir -p "$OUTPUT_DIR"

# 1. Copy launchd daemon plist
echo "📋 Packaging launchd daemon..."
cp "$REPO_ROOT/ops/com.rhea.tunnel.plist" "$OUTPUT_DIR/com.rhea.tunnel.plist"
chmod 644 "$OUTPUT_DIR/com.rhea.tunnel.plist"

# 2. Copy installation scripts
echo "📦 Packaging installation scripts..."
cp "$REPO_ROOT/scripts/setup_rhea_tunnel.sh" "$OUTPUT_DIR/setup_rhea_tunnel.sh"
chmod +x "$OUTPUT_DIR/setup_rhea_tunnel.sh"

# 3. Create installation guide
cat > "$OUTPUT_DIR/README-macOS.md" << 'EOF'
# Rhea macOS System Service Installation

## Quick Start

1. Extract this package to `/opt/rhea/`
2. Run: `sudo bash setup_rhea_tunnel.sh`
3. Verify: `launchctl list | grep com.rhea.tunnel`

## Requirements
- macOS 13.0 or later
- Administrator (sudo) access
- RheaApp.app installed in /Applications

## What's Installed
- **com.rhea.tunnel** — System daemon for VPN/network extension
- **Logs:** `/var/log/rhea_tunnel.log` and `/var/log/rhea_tunnel_error.log`
- **IPC:** Mach service `com.rhea.tunnel.service`

## Manual Management

```bash
# Start
sudo launchctl load /Library/LaunchDaemons/com.rhea.tunnel.plist

# Stop
sudo launchctl unload /Library/LaunchDaemons/com.rhea.tunnel.plist

# Status
launchctl list | grep com.rhea.tunnel

# View logs
tail -f /var/log/rhea_tunnel.log
```

## Troubleshooting
See full documentation: https://github.com/timelabs/rhea-project/blob/main/docs/RHEA_TUNNEL_ENTITLEMENTS_GUIDE.md
EOF

# 4. Create installation receipt
cat > "$OUTPUT_DIR/install_receipt.json" << EOF
{
  "package": "rhea-macos",
  "version": "$(git describe --tags --abbrev=0 2>/dev/null || echo 'dev')",
  "platform": "macos",
  "build_date": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "components": [
    {
      "name": "com.rhea.tunnel",
      "type": "launchd-daemon",
      "path": "/Library/LaunchDaemons/com.rhea.tunnel.plist",
      "user": "_networkd",
      "auto_start": true
    },
    {
      "name": "setup_rhea_tunnel.sh",
      "type": "installation-script",
      "requires_sudo": true
    }
  ],
  "permissions": {
    "entitlements": [
      "com.apple.developer.networking.networkextension",
      "com.apple.developer.networking.vpn.api"
    ],
    "tcc_services": [
      "kTCCServiceNetworkExtension",
      "kTCCServiceLocalNetworking"
    ],
    "system_user": "_networkd"
  },
  "logs": [
    "/var/log/rhea_tunnel.log",
    "/var/log/rhea_tunnel_error.log"
  ]
}
EOF

echo "✅ macOS distribution package ready:"
echo "   - com.rhea.tunnel.plist"
echo "   - setup_rhea_tunnel.sh"
echo "   - README-macOS.md"
echo "   - install_receipt.json"
echo ""
echo "📍 Output: $OUTPUT_DIR"
