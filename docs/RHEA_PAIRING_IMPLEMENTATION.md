# Rhea Pairing System — Implementation Guide

## Overview

The Pairing System enables secure device-to-device linking via QR codes and Ed25519 public key cryptography. A Windows/macOS Control Centre can pair with an iPhone running Rhea to enable cross-platform orchestration.

**Key Components:**
- `PairingDelegate` — Orchestrates QR scanning, mDNS discovery, and Ed25519 key exchange
- `PairingView` — UI for QR scanning and pairing status
- `PairingError` — Error handling during pairing flow
- `KeychainHelper` — Secure storage of private keys and session receipts

## Pairing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User taps "Pair Device" in Rhea iOS App                     │
│    → PairingDelegate.beginQRScan()                              │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. QR Scanner camera activated (AVCaptureSession)               │
│    → Camera captures QR code: rhea://pair?service=X&sig=Y      │
│    → PairingDelegate.handleScannedQRCode(qrString)             │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Parse QR Code & Extract mDNS Service Name                   │
│    → QRCodeData { mdnsServiceName: "rhea-control", ... }       │
│    → Validate signature                                          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Discover Service via mDNS (Network.framework)                │
│    → NWBrowser searches for _rhea._tcp.local                   │
│    → Filters for matching service name                          │
│    → resolves to IP:port endpoint                              │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Establish TLS Connection                                     │
│    → NWConnection(endpoint, using: NWParameters.tls)           │
│    → Verify peer certificate (optional pinning)                │
│    → Wait for .ready state                                     │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Load/Create Ed25519 Key Pair                                 │
│    → If not in Keychain: generate Curve25519.Signing.PrivateKey│
│    → Extract public key: privateKey.publicKey.rawRepresentation│
│    → Store in Keychain (persistent across app restarts)         │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. Send Pairing Request via HTTPS POST                          │
│    POST /api/v1/pair                                            │
│    {                                                             │
│      "public_key": "a1b2c3...hex...",                          │
│      "device_name": "iPhone 15 Pro",                           │
│      "device_model": "iPhone16,2",                             │
│      "os_version": "17.3"                                       │
│    }                                                             │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. Server Validates & Issues Session Receipt                    │
│    ✓ 200 OK:  Accept pairing, return SessionReceipt            │
│    │ {                                                          │
│    │   "linked_device": "iPhone_v1.0.34_34",                 │
│    │   "session_token": "eyJhbG...",                         │
│    │   "expires_at": "2026-03-06T22:51:53Z",                 │
│    │   "trust_level": "authenticated"                        │
│    │ }                                                         │
│    ✗ 401: Unauthorized (device revoked)                        │
│    ✗ 409: Conflict (already paired)                            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. Store Receipt in Keychain (persistent)                       │
│    → Save sessionReceipt with deviceID + token                 │
│    → Update @Published properties on MainActor                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 10. UI State Updated to "Connected"                             │
│     → isConnected = true                                        │
│     → linkedDeviceID = "iPhone_v1.0.34_34"                    │
│     → pairingTrustLevel = .authenticated                        │
│     → User can now orchestrate with Control Centre              │
└─────────────────────────────────────────────────────────────────┘
```

## File Locations

- `packages/RheaKit/Sources/RheaKit/PairingDelegate.swift` — Core pairing logic
- `packages/RheaKit/Sources/RheaKit/PairingView.swift` — SwiftUI pairing UI
- `ios/RheaApp/RheaApp.entitlements` — Required VPN entitlements
- `docs/RHEA_PAIRING_IMPLEMENTATION.md` — This file

## Implementation Details

### PairingDelegate

**Initialization:**
```swift
@StateObject var pairing = PairingDelegate.shared
```

**Public API:**
```swift
// Start QR scanning
pairing.beginQRScan()

// Handle scanned QR code
pairing.handleScannedQRCode("rhea://pair?service=rhea-control&sig=abc123...")

// Check pairing status
pairing.isConnected  // Bool
pairing.linkedDeviceID  // String?
pairing.pairingTrustLevel  // TrustLevel
pairing.publicKeyHex  // String?
```

**Published State:**
```swift
@Published var isPairingInProgress: Bool
@Published var pairingStatusText: String
@Published var linkedDeviceID: String?
@Published var pairingTrustLevel: TrustLevel
@Published var isConnected: Bool
```

### TrustLevel Enum

```swift
enum TrustLevel: String, Codable {
    case unknown        // Not paired
    case pending        // Pairing in progress
    case authenticated  // Connected and verified
    case revoked        // Pairing revoked by server
}
```

### SessionReceipt

```swift
struct SessionReceipt: Codable {
    let deviceID: String           // "iPhone_v1.0.34_34"
    let sessionToken: String       // JWT token for future requests
    let expiresAt: ISO8601DateFormatter.Options
    let trustLevel: TrustLevel
}
```

### PairingView

**Integration:**
```swift
NavigationStack {
    PairingView()
        .navigationTitle("Pair Device")
}
```

**States Displayed:**
- **Ready:** "Scan QR Code" button visible
- **Pairing:** "Pairing..." button, progress indicators
- **Connected:** Device ID, trust level, public key prefix
- **Error:** Error message with retry button

### Error Handling

```swift
enum PairingError: LocalizedError {
    case invalidURL
    case invalidResponse
    case invalidQRCode
    case unauthorized          // 401: Device revoked
    case alreadyPaired          // 409: Already paired
    case serverError(Int)
    case decodingFailed
}
```

## Entitlements Required

**iOS App (`RheaApp.entitlements`):**
```xml
<key>com.apple.developer.networking.vpn.api</key>
<array>
    <string>allow-vpn</string>
</array>
```

This allows the use of `Network.framework` APIs (NWBrowser, NWConnection) for low-level networking including mDNS.

**Camera Access (`Info.plist`):**
```xml
<key>NSCameraUsageDescription</key>
<string>Rhea needs camera access to scan device pairing QR codes</string>
```

## Server Endpoint: POST /api/v1/pair

### Request

```json
{
  "public_key": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z...",
  "device_name": "iPhone 15 Pro",
  "device_model": "iPhone16,2",
  "os_version": "17.3"
}
```

### Response (200 OK)

```json
{
  "linked_device": "iPhone_v1.0.34_34",
  "session_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2026-03-06T22:51:53Z",
  "trust_level": "authenticated"
}
```

### Error Responses

| Status | Message | Meaning |
|--------|---------|---------|
| 400 | Invalid request | Malformed JSON or missing fields |
| 401 | Unauthorized | Device has been revoked by server |
| 409 | Conflict | Device already paired (same public_key) |
| 500 | Server error | Internal server error |

## Security Considerations

### 1. Ed25519 Key Pair Generation
- Generated on first app launch using `Curve25519.Signing.PrivateKey()`
- Private key stored in iOS Keychain with service identifier: `com.rhea.pairing`
- Public key derivable from private key but never stored separately
- **Never transmitted over network** — only public key is sent

### 2. Keychain Storage
- Service: `com.rhea.pairing`
- Accessibility: `.whenUnlockedThisDeviceOnly` (default)
- Accessible only by the app that stored it
- Automatically deleted if app is uninstalled

### 3. TLS Connection
- `NWConnection` with `NWParameters.tls` ensures encrypted transport
- Optional certificate pinning possible by validating peer certificate
- mDNS discovery happens over local network (no internet required)

### 4. QR Code Validation
- QR string must start with `rhea://pair?`
- Contains server signature for replay attack prevention
- Service name and signature extracted and validated

### 5. Session Token
- JWT returned by server after successful pairing
- Should be used in subsequent API calls (`Authorization: Bearer <token>`)
- Expires at server-specified time (e.g., 24 hours)
- Stored in Keychain, retrieved on each API call

## Testing

### Unit Tests

```swift
func testQRCodeParsing() {
    let qrString = "rhea://pair?service=rhea-control&sig=abc123"
    let data = pairing.parseQRCode(qrString)
    XCTAssertEqual(data?.mdnsServiceName, "rhea-control")
    XCTAssertEqual(data?.serverSignature, "abc123")
}

func testInvalidQRCode() {
    let qrString = "invalid://code"
    let data = pairing.parseQRCode(qrString)
    XCTAssertNil(data)
}

func testKeyPairGeneration() {
    let pairing = PairingDelegate.shared
    XCTAssertNotNil(pairing.publicKeyHex)
    XCTAssertGreaterThan(pairing.publicKeyHex?.count ?? 0, 0)
}
```

### Integration Testing

1. **Manual QR scan:**
   ```bash
   # Generate test QR code
   echo -n "rhea://pair?service=rhea-control&sig=test123" | qrencode -o test-qr.png
   # Scan with app
   ```

2. **mDNS discovery:**
   ```bash
   # Check mDNS on same WiFi
   dns-sd -B _rhea._tcp local.
   ```

3. **TLS connection:**
   ```bash
   # Verify HTTPS endpoint
   curl -v https://rhea-control.local:8443/
   ```

## Troubleshooting

### QR Code Not Scanning
- Ensure camera permissions granted in Settings → Rhea → Camera
- Try different lighting conditions
- Check QR code size (recommend 4cm × 4cm minimum)

### mDNS Discovery Fails
- Ensure device is on same WiFi network as Control Centre
- Check firewall rules allow mDNS (port 5353 UDP)
- Restart WiFi connection and try again

### TLS Connection Hangs
- Verify Control Centre TLS certificate is valid
- Check certificate domain matches mDNS service name
- Ensure TLS port is accessible (usually 8443)

### Session Token Expired
- Server-side token expiry (e.g., 24 hours)
- App prompts to re-pair device
- Clear pairing: Settings → Reset All

## Future Enhancements

1. **Certificate Pinning:** Store server public key hash to prevent MITM
2. **NFC Pairing:** Alternative to QR codes for newer devices
3. **Bluetooth LE:** Low-power discovery without WiFi requirement
4. **Automated Renewal:** Silently refresh token before expiry
5. **Multiple Devices:** Support pairing with multiple Control Centres
6. **Device Revocation:** Server can revoke pairing (return 401)
7. **Two-Factor:** Optional PIN entry after QR scan

## References

- [Network.framework Documentation](https://developer.apple.com/documentation/network)
- [CryptoKit - Ed25519](https://developer.apple.com/documentation/cryptokit)
- [Keychain Services](https://developer.apple.com/documentation/security/keychain_services)
- [AVFoundation QR Scanning](https://developer.apple.com/documentation/avfoundation)
- [RFC 8037 - CFRG Elliptic Curve Signatures](https://tools.ietf.org/html/rfc8037)

---

**Implementation Date:** 2026-03-06  
**Status:** ✅ Complete  
**Last Updated:** 2026-03-06
