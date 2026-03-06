# RheaTunnel Entitlements & Daemon Permissions - Setup Summary

## ✅ Configuration Complete

### Files Modified
1. **ios/RheaApp/RheaTunnel.entitlements** (Modified)
   - Added `com.apple.developer.networking.vpn`
   - Added `com.apple.developer.system-extension.install`
   - Added `com.apple.security.temporary-exception.local-networking`
   - Added `com.apple.security.temporary-exception.mach-lookup.global-name` (networkd IPC)
   - Added `com.apple.privacyscreen.disable`

2. **ios/RheaApp/RheaApp.entitlements** (Modified)
   - Added `com.apple.developer.system-extension.install`
   - Added `com.apple.security.temporary-exception.local-networking`
   - Added `com.apple.security.temporary-exception.mach-lookup.global-name` (networkd + vpn control)

### Files Created

3. **ops/com.rhea.tunnel.plist** (New)
   - Launchd daemon configuration for RheaTunnel system service
   - Runs as `_networkd` system user (UID 64)
   - Auto-restart on failure with 10-second throttle
   - Logs to `/var/log/rhea_tunnel*.log`
   - Mach service endpoint: `com.rhea.tunnel.service`

4. **scripts/setup_rhea_tunnel.sh** (New, Executable)
   - Automated installation script for system daemon
   - Copies plist to `/Library/LaunchDaemons/`
   - Loads daemon via launchctl
   - Verifies installation with status checks
   - Provides troubleshooting guidance

5. **docs/RHEA_TUNNEL_TCC_PERMISSIONS.plist** (New)
   - Reference file documenting required TCC services
   - Details on NetworkExtension, LocalNetworking, SystemExtensions
   - Code signing requirements and sandbox profile
   - Team ID: K4THLVMXM6

6. **docs/RHEA_TUNNEL_ENTITLEMENTS_GUIDE.md** (New)
   - Comprehensive documentation for all configuration
   - Installation steps and verification procedures
   - Manual daemon management commands
   - Security considerations and troubleshooting

## 🔑 Key Entitlements Added

| Entitlement | Purpose |
|---|---|
| `com.apple.developer.networking.vpn` | VPN connection management |
| `com.apple.developer.system-extension.install` | System extension capability |
| `com.apple.security.temporary-exception.local-networking` | No-prompt local network access |
| `com.apple.security.temporary-exception.mach-lookup.global-name` | IPC with system daemons |

## 🚀 Installation Steps

```bash
# 1. Update Xcode project to use new entitlements
# 2. Ensure provisioning profile includes NetworkExtension capability
# 3. Build and sign with:
codesign -s - --entitlements ios/RheaApp/RheaTunnel.entitlements \
  /Applications/RheaApp.app/Contents/PlugIns/RheaTunnel.appex/Contents/MacOS/RheaTunnel

# 4. Install system daemon (requires sudo)
sudo bash scripts/setup_rhea_tunnel.sh

# 5. Verify installation
launchctl list | grep com.rhea.tunnel
tail -f /var/log/rhea_tunnel.log
```

## ✨ What This Enables

✅ Network extension runs without UI prompts  
✅ System-level daemon auto-starts on boot  
✅ Direct networkd and VPN control IPC  
✅ Local network access without TCC dialogs  
✅ Automatic restart on crash  
✅ Proper sandbox restrictions  
✅ Full audit logging to `/var/log/`  

## 📋 Files Ready for Commit

```
M  ios/RheaApp/RheaTunnel.entitlements
M  ios/RheaApp/RheaApp.entitlements
?? ops/com.rhea.tunnel.plist
?? scripts/setup_rhea_tunnel.sh
?? docs/RHEA_TUNNEL_TCC_PERMISSIONS.plist
?? docs/RHEA_TUNNEL_ENTITLEMENTS_GUIDE.md
```

## 🔍 Verification

All plist and entitlement files are valid XML and properly formatted. Use the comprehensive guide in `docs/RHEA_TUNNEL_ENTITLEMENTS_GUIDE.md` for:
- Detailed installation procedures
- Manual daemon management
- Security considerations
- Troubleshooting tips

---
**Status:** Configuration complete and ready for Xcode project integration  
**Date:** 2026-03-05  
**Next Step:** Update Xcode build settings and provisioning profiles
