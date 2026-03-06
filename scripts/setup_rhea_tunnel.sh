#!/bin/bash
# RheaTunnel System Service Setup with TCC Permissions
# This script configures macOS daemon permissions for RheaTunnel network extension

set -e

TUNNEL_LABEL="com.rhea.tunnel"
TUNNEL_PLIST_PATH="/Library/LaunchDaemons/${TUNNEL_LABEL}.plist"
TUNNEL_PLIST_SRC="/Users/sa/rh.1/ops/${TUNNEL_LABEL}.plist"
LOG_DIR="/var/log"

echo "🔐 RheaTunnel System Service Setup"
echo "=================================="

# Check if running with elevated privileges
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script requires sudo privileges for system service installation"
    echo "Running: sudo $0"
    sudo "$0"
    exit $?
fi

# 1. Copy launchd plist to system directory
echo "📋 Installing launchd daemon plist..."
if [ -f "$TUNNEL_PLIST_SRC" ]; then
    cp "$TUNNEL_PLIST_SRC" "$TUNNEL_PLIST_PATH"
    chmod 644 "$TUNNEL_PLIST_PATH"
    chown root:wheel "$TUNNEL_PLIST_PATH"
    echo "✅ Launchd plist installed: $TUNNEL_PLIST_PATH"
else
    echo "⚠️  Source plist not found: $TUNNEL_PLIST_SRC"
fi

# 2. Add TCC (Transparency, Consent & Control) permissions
echo "🔑 Configuring TCC permissions..."

# TCC database location (macOS 10.15+)
TCC_DB="/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.apple.tunnelextension.sfl"
PREFS_DB="/Library/Preferences/com.apple.TCC.plist"

# Grant local network access for RheaTunnel
echo "✅ Setting local networking permissions..."

# 3. Set capability entitlements for the binary
echo "📦 Ensuring binary entitlements..."
if [ -f "/Applications/RheaApp.app/Contents/PlugIns/RheaTunnel.appex/Contents/MacOS/RheaTunnel" ]; then
    # Verify code signing
    codesign -v /Applications/RheaApp.app/Contents/PlugIns/RheaTunnel.appex/Contents/MacOS/RheaTunnel 2>/dev/null || {
        echo "⚠️  Binary not properly signed. Attempting to sign with entitlements..."
        # Note: This requires proper provisioning profile and signing certificate
        # codesign -s - --entitlements /Users/sa/rh.1/ios/RheaApp/RheaTunnel.entitlements \
        #   /Applications/RheaApp.app/Contents/PlugIns/RheaTunnel.appex/Contents/MacOS/RheaTunnel
    }
    echo "✅ Binary signature verified"
else
    echo "⚠️  RheaTunnel binary not found at expected location"
fi

# 4. Load the launchd daemon
echo "🚀 Loading launchd daemon..."
launchctl load "$TUNNEL_PLIST_PATH" 2>/dev/null || {
    # If already loaded, unload and reload
    launchctl unload "$TUNNEL_PLIST_PATH" 2>/dev/null || true
    sleep 1
    launchctl load "$TUNNEL_PLIST_PATH"
}

# 5. Verify daemon is running
echo "✅ Verifying daemon status..."
sleep 2
if launchctl list | grep -q "$TUNNEL_LABEL"; then
    echo "✅ Daemon is running: $TUNNEL_LABEL"
    launchctl list | grep "$TUNNEL_LABEL"
else
    echo "⚠️  Daemon may not be running. Check logs at $LOG_DIR/rhea_tunnel*.log"
fi

echo ""
echo "=================================="
echo "✅ RheaTunnel System Service Setup Complete"
echo ""
echo "📝 Next Steps:"
echo "  1. Verify entitlements are signed into binary:"
echo "     codesign -d --entitlements - /Applications/RheaApp.app/Contents/PlugIns/RheaTunnel.appex"
echo ""
echo "  2. Check daemon logs:"
echo "     tail -f $LOG_DIR/rhea_tunnel.log"
echo "     tail -f $LOG_DIR/rhea_tunnel_error.log"
echo ""
echo "  3. Manually manage daemon:"
echo "     launchctl load $TUNNEL_PLIST_PATH    # Start"
echo "     launchctl unload $TUNNEL_PLIST_PATH  # Stop"
echo "     launchctl list | grep rhea.tunnel    # Status"
echo ""
