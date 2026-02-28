# REX → GEMINI: Xcode Distribution SSL Certificate Failure

**Priority:** P2 (workaround exists, but root cause needs fix)
**Date:** 2026-02-28T17:08:00Z

## Problem

Xcode Organizer's "Distribute App" flow fails at the cloud code-signing step with SSL cert error:

```
NSURLErrorDomain Code=-1202
"The certificate for this server is invalid. You might be connecting to a server
that is pretending to be developerservices3.apple.com"
```

Certificate chain presented:
- `developerservices3.apple.com` → `Apple Public EV Server RSA CA 1 - G1` → `DigiCert Global Root G2`

Error code: `-9807` (kCFStreamErrorCodeKey)

## Context

- `curl -sI https://developerservices3.apple.com` works fine (403, expected — SSL handshake succeeds)
- `developerservices2.apple.com` (cert lookup) works in Xcode — 200 OK
- Only `developerservices3.apple.com/services/v1/batch` (cloud signing) fails
- Charles Proxy / Wireshark toolkit present on system — possible MITM cert in keychain
- CLI `xcodebuild -exportArchive` with `destination: upload` works without issues

## Investigation Needed

1. Check Keychain Access for Charles Proxy root cert or any custom CA intercepting Apple domains
2. Check `~/Library/Preferences/com.apple.security.*` for custom trust settings
3. Verify DigiCert Global Root G2 is trusted in System Roots keychain
4. Check if any proxy settings apply specifically to Xcode but not curl
5. `security verify-cert -c /path/to/developerservices3.cert` to test chain

## Workaround (active)

CLI pipeline works: `xcodebuild -exportArchive -exportOptionsPlist ExportOptionsUpload.plist -allowProvisioningUpdates`
Script: `scripts/testflight.sh`

Build #4 uploaded successfully via CLI at 16:54 UTC.

## Logs

Full distribution logs at:
`/private/var/folders/98/kzggkt892nnbmfbwtlq05jlh0000gn/T/RheaApp_1447-09-11_15-56-52.617.xcdistributionlogs/`
