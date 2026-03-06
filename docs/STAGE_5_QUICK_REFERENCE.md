# Stage 5 Multi-Platform Release — Quick Reference

## 🚀 Quick Start

```bash
# Create a release (triggers GitHub Actions)
git tag -a v1.0.35 -m "Release notes here"
git push origin v1.0.35

# Monitor workflow
# → https://github.com/timelabs/rhea-project/actions
```

## 📋 Workflow Jobs

| Job | Runner | Purpose |
|-----|--------|---------|
| **audit-and-verify** | Ubuntu | Security scan + entitlements check |
| **build-ios** | macOS | Archive & export IPA for TestFlight |
| **build-windows** | Windows | Create rhea.bat + installer |
| **build-macos** | macOS | Package daemon + launchd config |
| **create-release** | Ubuntu | GitHub release with artifacts |
| **notify** | Ubuntu | Final status notification |

## 📦 Release Artifacts

```
v1.0.35/
├── RheaApp.ipa               (iOS - TestFlight)
├── rhea-windows-latest.zip   (Windows binaries)
│   ├── rhea.bat
│   ├── rhea-win-init.ps1
│   └── install_receipt.json
├── rhea-macos.dmg            (macOS installer)
│   ├── com.rhea.tunnel.plist
│   ├── setup_rhea_tunnel.sh
│   └── README-macOS.md
└── Release Notes             (automated)
```

## 🔐 Required Secrets (GitHub)

Set in: **Settings → Secrets and variables → Actions**

```
APPSTORE_ISSUER_ID         (App Store Connect)
APPSTORE_KEY_ID            (App Store Connect)
APPSTORE_PRIVATE_KEY       (base64 encoded)
WIN_CERT_B64               (optional)
```

## ✅ Entitlements Verified

### iOS App
```
✓ com.apple.developer.networking.networkextension
✓ com.apple.developer.networking.vpn.api
✓ com.apple.security.application-groups
✓ keychain-access-groups
```

### iOS Network Extension
```
✓ com.apple.developer.networking.networkextension
✓ com.apple.security.application-groups
✓ keychain-access-groups
```

### macOS Daemon
```
✓ Label: com.rhea.tunnel
✓ User: _networkd (restricted)
✓ RunAtLoad: yes
✓ KeepAlive: yes
✓ Mach Service: com.rhea.tunnel.service
```

## 🔍 Security Checks

- [x] No "DPI" or "Bypass" strings
- [x] No invalid entitlements
- [x] Code signing verified
- [x] Daemon runs as restricted user
- [x] Proper permissions set

## 📝 Manual Build (if needed)

```bash
# iOS only
bash scripts/testflight.sh

# macOS daemon
bash scripts/build_macos.sh --output build/dist

# Windows
python3 scripts/build_windows.py --output build/dist
```

## 🔗 Key Files

| File | Purpose |
|------|---------|
| `.github/workflows/rhea-release.yml` | Release automation |
| `scripts/build_macos.sh` | macOS packaging |
| `scripts/build_windows.py` | Windows packaging |
| `scripts/testflight.sh` | iOS build |
| `ios/RheaApp/RheaApp.entitlements` | iOS app entitlements |
| `ios/RheaApp/RheaTunnel.entitlements` | Network extension |
| `ops/com.rhea.tunnel.plist` | macOS daemon config |
| `docs/STAGE_5_RELEASE_SETUP.md` | Full documentation |

## 📊 Build Status

**Latest Local Build:**
- iOS: #34 (Ready for TestFlight)
- macOS: Daemon configured
- Windows: Scripts ready

**To Test Workflow:**
```bash
git tag v1.0.35-test
git push origin v1.0.35-test
# Check Actions tab
git tag -d v1.0.35-test
git push origin :refs/tags/v1.0.35-test
```

## 💡 Notes

- Entitlements files updated: Only valid iOS entitlements included
- Swift compilation fixes: AppConfig and BioRendererView corrected
- Xcode project: Regenerated with XcodeGen
- No forbidden strings: Full codebase scanned
- macOS daemon: Runs as `_networkd` system user (UID 64)

---
**Setup Date:** 2026-03-06  
**Status:** ✅ Ready for production releases
