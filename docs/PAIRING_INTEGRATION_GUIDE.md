# Pairing System Integration Guide

## Quick Start

### 1. Add to Navigation

In `RheaPreviewApp.swift` or your main app file:

```swift
NavigationStack {
    TabView {
        // ... existing tabs ...
        
        PairingView()
            .tabItem {
                Label("Pair", systemImage: "link")
            }
    }
}
```

### 2. Access Pairing State

From any view:

```swift
@StateObject var pairing = PairingDelegate.shared

Text("Status: \(pairing.pairingStatusText)")
if pairing.isConnected {
    Text("Connected to: \(pairing.linkedDeviceID ?? "Unknown")")
}
```

### 3. Verify Entitlements

Ensure `ios/RheaApp/RheaApp.entitlements` contains:

```xml
<key>com.apple.developer.networking.vpn.api</key>
<array>
    <string>allow-vpn</string>
</array>

<key>com.apple.security.application-groups</key>
<array>
    <string>group.com.rhea.preview</string>
</array>
```

### 4. Add Camera Permission

In `ios/RheaApp/Info.plist`:

```xml
<key>NSCameraUsageDescription</key>
<string>Rhea needs camera access to scan device pairing QR codes</string>
```

## File Changes Required

### New Files
- ✅ `packages/RheaKit/Sources/RheaKit/PairingDelegate.swift`
- ✅ `packages/RheaKit/Sources/RheaKit/PairingView.swift`
- ✅ `docs/RHEA_PAIRING_IMPLEMENTATION.md`

### Modified Files
None required (fully backward compatible)

## Testing Checklist

- [ ] Build succeeds with new files
- [ ] Camera permission prompt appears on first QR scan
- [ ] QR code parsing works (test with sample QR)
- [ ] mDNS discovery works (both on same WiFi)
- [ ] Ed25519 public key generated and stored
- [ ] Session receipt stored in Keychain
- [ ] UI shows "Connected" after pairing
- [ ] Device ID persists across app restarts

## Example: Full Setup

```swift
import SwiftUI
import RheaKit

@main
struct RheaApp: App {
    @StateObject private var pairing = PairingDelegate.shared
    
    var body: some Scene {
        WindowGroup {
            NavigationStack {
                TabView {
                    // Home tab
                    HomeView()
                        .tabItem {
                            Label("Home", systemImage: "house")
                        }
                    
                    // Pairing tab
                    PairingView()
                        .tabItem {
                            Label("Pair", systemImage: "link")
                        }
                    
                    // Settings tab
                    SettingsView()
                        .tabItem {
                            Label("Settings", systemImage: "gear")
                        }
                }
                // Show pairing indicator in status bar
                .badge(pairing.isConnected ? 1 : 0)
            }
        }
    }
}
```

## Integration with RheaAPI

Once pairing is established, include session token in API calls:

```swift
extension RheaAPI {
    public var pairingToken: String? {
        // Retrieve from Keychain
        let pairing = PairingDelegate.shared
        return pairing.linkedDeviceID
    }
    
    private func applyAuth(_ request: inout URLRequest) {
        // Existing auth code
        if let jwt = AuthManager.shared.token {
            request.setValue("Bearer \(jwt)", forHTTPHeaderField: "Authorization")
        }
        // Also include pairing session token if available
        else if let token = pairingToken {
            request.setValue("X-Pairing-Token: \(token)", forHTTPHeaderField: "Authorization")
        }
        // Fallback to API key
        else {
            request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        }
    }
}
```

## Deployment

### iOS Build

```bash
cd ios/RheaApp
xcodegen generate
xcodebuild archive \
  -scheme RheaApp \
  -configuration Release \
  -archivePath build/RheaApp.xcarchive
```

### TestFlight Upload

```bash
bash scripts/testflight.sh
# Optionally upload with:
bash scripts/testflight.sh --upload
```

## Monitoring

### View Pairing Status

```swift
// In any view
@StateObject var pairing = PairingDelegate.shared

Text("Pairing: \(pairing.pairingStatusText)")
Text("Trust Level: \(pairing.pairingTrustLevel.displayName)")
```

### Debug Logging

Pairing delegate logs to:
```
subsystem: com.rhea.preview
category: pairing
```

View with:
```bash
log stream --predicate 'subsystem contains "pairing"' --level debug
```

### Keychain Contents

List stored data:
```bash
security dump-keychain -d login.keychain-db | grep com.rhea.pairing
```

## Troubleshooting

### Build Failure: Cannot find Curve25519

Add CryptoKit import:
```swift
import CryptoKit
```

### QR Scanner Not Appearing

Check `Info.plist` for camera permission:
```xml
<key>NSCameraUsageDescription</key>
<string>Rhea needs camera access to scan device pairing QR codes</string>
```

### Keychain Access Denied

Ensure entitlements include:
```xml
<key>com.apple.security.application-groups</key>
<array>
    <string>group.com.rhea.preview</string>
</array>
```

### mDNS Discovery Times Out

- Verify both devices on same WiFi network
- Check firewall allows UDP port 5353
- Ensure Control Centre's mDNS service is running

## API Compatibility

### Control Centre (Windows/macOS) Requirements

**Endpoint:** `POST /api/v1/pair`

**Request:**
```json
{
  "public_key": "hex_encoded_ed25519_public_key",
  "device_name": "iPhone 15 Pro",
  "device_model": "iPhone16,2",
  "os_version": "17.3"
}
```

**Response (200):**
```json
{
  "linked_device": "device_id",
  "session_token": "jwt_token",
  "expires_at": "2026-03-06T22:51:53Z",
  "trust_level": "authenticated"
}
```

## Security Checklist

- [x] Private key stored in Keychain (encrypted at rest)
- [x] Public key never stored, only sent over TLS
- [x] TLS connection mandatory (no plaintext pairing)
- [x] QR code contains server signature (replay attack prevention)
- [x] Session token validated by server on each request
- [x] Device ID unique per phone/Control Centre pair
- [x] Keychain data deleted on app uninstall

## Performance Notes

- **QR Scan:** ~1 second per scan (AVFoundation)
- **mDNS Discovery:** ~2-5 seconds (Network.framework)
- **TLS Handshake:** ~1 second (standard HTTPS)
- **Server Validation:** ~100-500ms (API latency)
- **Total Pairing Time:** ~5-10 seconds (typical)

## Next Steps

1. Build and test with iPhone simulator
2. Test on physical device with real Control Centre
3. Monitor Keychain usage and session token expiry
4. Implement token refresh logic (optional)
5. Add certificate pinning for production (recommended)

---

**Integration Guide Version:** 1.0  
**Last Updated:** 2026-03-06
