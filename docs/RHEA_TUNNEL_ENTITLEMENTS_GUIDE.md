# RheaTunnel Entitlements & Daemon Permissions

## Overview
This document describes the macOS entitlements and system daemon configuration for RheaTunnel Network Extension, enabling it to run as a system service without UI prompts.

## Files Modified/Created

### 1. RheaTunnel.entitlements (Enhanced)
**Location:** `ios/RheaApp/RheaTunnel.entitlements`

**Key Entitlements:**

| Entitlement | Purpose |
|-------------|---------|
| `com.apple.developer.networking.networkextension` | Enable packet tunnel provider capability |
| `com.apple.developer.networking.vpn` | Allow VPN connection management |
| `com.apple.developer.system-extension.install` | Permission to install system extensions |
| `com.apple.security.application-groups` | Shared data container with main app |
| `com.apple.security.temporary-exception.local-networking` | Local network access without user prompt |
| `com.apple.security.temporary-exception.mach-lookup.global-name` | IPC with networkd daemon |
| `keychain-access-groups` | Secure credential storage |

### 2. RheaApp.entitlements (Enhanced)
**Location:** `ios/RheaApp/RheaApp.entitlements`

**New Entitlements:**
- `com.apple.developer.system-extension.install` — Allow system extension installation
- `com.apple.security.temporary-exception.mach-lookup.global-name` — Direct networkd/vpn control communication

### 3. Launchd Daemon Configuration
**Location:** `ops/com.rhea.tunnel.plist`

**Configuration Details:**

```xml
Label:             com.rhea.tunnel
RunAtLoad:         true (start on system boot)
KeepAlive:         true (restart if crashed)
UserName:          _networkd (system-level user)
GroupName:         _networkd (network daemon group)
MachServiceName:   com.rhea.tunnel.service (IPC endpoint)
ThrottleInterval:  10 seconds (restart throttle)
ExitTimeOut:       30 seconds (graceful shutdown window)
```

## TCC (Transparency, Consent & Control) Permissions

### Required TCC Services
1. **Network Extension** (`kTCCServiceNetworkExtension`)
   - Enables packet tunnel provider functionality
   - Requires entitlement: `com.apple.developer.networking.networkextension`

2. **Local Networking** (`kTCCServiceLocalNetworking`)
   - Grants local network access without prompt
   - Requires entitlement: `com.apple.security.temporary-exception.local-networking`

3. **System Extensions** (`kTCCServiceSystemExtensions`)
   - Allows installation of network extensions
   - Requires entitlement: `com.apple.developer.system-extension.install`

**Reference:** `docs/RHEA_TUNNEL_TCC_PERMISSIONS.plist`

## Installation & Setup

### Prerequisites
- Xcode with iOS/macOS development kit
- Valid Apple Developer certificate (Team ID: K4THLVMXM6)
- Proper provisioning profiles with NetworkExtension capability
- Administrator (sudo) access on macOS

### Installation Steps

1. **Update Entitlements**
   - Modify Xcode project to use updated `RheaTunnel.entitlements`
   - Ensure provisioning profile includes Network Extension capability
   - Update Team ID in build settings

2. **Sign Binary with Entitlements**
   ```bash
   codesign -s - --entitlements ios/RheaApp/RheaTunnel.entitlements \
     /Applications/RheaApp.app/Contents/PlugIns/RheaTunnel.appex/Contents/MacOS/RheaTunnel
   ```

3. **Install System Daemon**
   ```bash
   sudo bash scripts/setup_rhea_tunnel.sh
   ```

4. **Verify Installation**
   ```bash
   # Check daemon is running
   launchctl list | grep com.rhea.tunnel
   
   # Check logs
   tail -f /var/log/rhea_tunnel.log
   tail -f /var/log/rhea_tunnel_error.log
   
   # Verify code signature
   codesign -d --entitlements - /Applications/RheaApp.app/Contents/PlugIns/RheaTunnel.appex
   ```

## Manual Daemon Management

```bash
# Start daemon
sudo launchctl load /Library/LaunchDaemons/com.rhea.tunnel.plist

# Stop daemon
sudo launchctl unload /Library/LaunchDaemons/com.rhea.tunnel.plist

# Check status
launchctl list | grep com.rhea.tunnel
launchctl show com.rhea.tunnel

# View logs
log stream --predicate 'eventMessage contains "rhea_tunnel"' --level debug

# Restart daemon
sudo launchctl unload /Library/LaunchDaemons/com.rhea.tunnel.plist
sleep 1
sudo launchctl load /Library/LaunchDaemons/com.rhea.tunnel.plist
```

## Security Considerations

### Sandbox Restrictions
- Network: Outbound allowed, inbound restricted
- File system: Limited to `/Library/Application Support/RheaTunnel`
- IPC: Restricted to approved mach services

### Code Signing Requirements
- Binary must be signed with development certificate
- Entitlements must be baked into code signature
- Signature must be verified before launch

### Privilege Escalation
- Runs as `_networkd` system user (UID 64)
- Limited to network management operations
- No shell access or file modification capabilities

## Troubleshooting

### Daemon Won't Start
```bash
# Check for syntax errors in plist
plutil -lint /Library/LaunchDaemons/com.rhea.tunnel.plist

# View system logs
log stream --predicate 'process == "launchd"' --level debug

# Check permissions
ls -la /Library/LaunchDaemons/com.rhea.tunnel.plist
# Should be: -rw-r--r-- root:wheel
```

### TCC Permission Denied
```bash
# Reset TCC database (macOS)
sudo rm /Library/Application\ Support/CrashReporter/DiagnosticMessagesHistory.db

# Or for specific service
sudo sqlite3 /Library/Application\ Support/com.apple.sharedfilelist/com.apple.TCC.plist \
  DELETE FROM access WHERE client LIKE 'com.rhea%'
```

### Signature Validation Fails
```bash
# Check signature
spctl --assess --verbose /Applications/RheaApp.app

# Re-sign if needed
codesign --force --sign - --entitlements ios/RheaApp/RheaTunnel.entitlements \
  /Applications/RheaApp.app/Contents/PlugIns/RheaTunnel.appex
```

## References

- [Apple NetworkExtension Framework](https://developer.apple.com/documentation/networkextension)
- [System Extensions Documentation](https://developer.apple.com/documentation/systemextension)
- [launchd.plist Manual](https://www.manpagez.com/man/5/launchd.plist/)
- [Code Signing & Entitlements](https://developer.apple.com/support/code-signing/)
- [macOS Security & Privacy](https://support.apple.com/en-us/102577)

## Last Updated
2026-03-05

## Related Files
- `ios/RheaApp/RheaTunnel.entitlements` — Network extension entitlements
- `ios/RheaApp/RheaApp.entitlements` — Main app entitlements
- `ops/com.rhea.tunnel.plist` — Launchd daemon configuration
- `scripts/setup_rhea_tunnel.sh` — Installation script
- `docs/RHEA_TUNNEL_TCC_PERMISSIONS.plist` — TCC permission reference
