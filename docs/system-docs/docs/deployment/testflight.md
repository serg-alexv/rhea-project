---
sidebar_position: 3
---

# TestFlight & iOS

The Rhea iOS app is a SwiftUI application with multiple targets for the full mobile experience.

## App Structure

```
ios/
├── RheaApp/              # Main iOS app
├── RheaKeyboard/         # Custom keyboard extension
├── RheaShare/            # Share extension
├── RheaTunnel/           # Network extension (VPN/proxy)
├── RheaPreview.swiftpm/  # Swift Playgrounds preview
├── Frameworks/           # Shared frameworks
├── rhea-plus-ui/         # Premium UI components
└── play-extraction/      # Play UI extraction tools
```

## Targets

| Target | Type | Description |
|--------|------|-------------|
| **RheaApp** | App | Main application — sessions, tribunal, clipboard |
| **RheaKeyboard** | Keyboard Extension | Custom keyboard with AI suggestions |
| **RheaShare** | Share Extension | Share content to Rhea clipboard |
| **RheaTunnel** | Network Extension | Tunnel traffic through Rhea proxy |

## Build Prerequisites

- **Xcode 15+**
- **iOS 17+ SDK**
- Apple Developer account (for TestFlight)
- Provisioning profiles for all targets

## TestFlight Pipeline

### 1. Archive

```bash
xcodebuild archive \
  -project ios/RheaApp.xcodeproj \
  -scheme RheaApp \
  -archivePath build/RheaApp.xcarchive \
  -destination "generic/platform=iOS"
```

### 2. Export IPA

```bash
xcodebuild -exportArchive \
  -archivePath build/RheaApp.xcarchive \
  -exportPath build/ipa \
  -exportOptionsPlist ios/ExportOptions.plist
```

### 3. Upload to TestFlight

```bash
xcrun altool --upload-app \
  -f build/ipa/RheaApp.ipa \
  -t ios \
  --apiKey YOUR_API_KEY \
  --apiIssuer YOUR_ISSUER_ID
```

## API Integration

The iOS app connects to the Tribunal API:
- **Production:** `https://rhea-tribunal.fly.dev`
- **Local dev:** `http://localhost:8400`

Key features:
- Session management (character selection, message history)
- Tribunal queries with consensus visualization
- Cross-device clipboard sync via SSE
- HealthKit integration for biometric data

**Status:** App structure and targets are set up. Core UI and API integration are in active development.
