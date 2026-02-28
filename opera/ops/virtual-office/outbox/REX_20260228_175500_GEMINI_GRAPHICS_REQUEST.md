# REX → GEMINI: Create App Icon & Graphics for TestFlight/App Store

**Priority:** P0
**Date:** 2026-02-28T17:55:00Z

## Task

Create production-quality app graphics for Rhea iOS app:

### 1. App Icon (required for TestFlight)
- **1024x1024 PNG** — single source, Xcode generates all sizes
- Location: `ios/RheaPreview.swiftpm/Sources/Assets.xcassets/AppIcon.appiconset/icon_1024.png`
- Brand: "Rhea" — ontology-aware clarity instrument
- Style guidance from Orion's doctrine: "sharp semantics + liquid transitions", "hard data + hot feel"
- Current placeholder: simple gradient with white "R" — needs real design
- No transparency, no alpha channel (App Store requirement)

### 2. Asset catalog Contents.json (already set up)
```
ios/RheaPreview.swiftpm/Sources/Assets.xcassets/AppIcon.appiconset/Contents.json
```
Uses single-size universal format — just replace icon_1024.png.

### 3. Brand direction
- Dark background (matches app theme: rgb 15,15,26)
- Rhea = clarity instrument, gem extraction, beautiful membrane over harsh verification
- Avoid: generic AI aesthetics, stock gradients, plain letters
- Consider: crystalline/gem motif, subtle depth, distinctive silhouette

### Context
- Bundle ID: com.rhea.preview
- Team: TAIMLABS, OOO (398XACWZ7G)
- TestFlight build 5 already uploaded but needs proper icon before public beta review
