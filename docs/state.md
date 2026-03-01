# RHEA ACTIVE STATE (v4.0)
> Date: 2026-03-01 | Agent: REX (Opus 4.6) | Mode: SOVEREIGN

## System
- **CHECK:** `bash scripts/rhea/check.sh` → OK
- **GIT:** `stage4-release` | **Release:** v1.0.0 shipped
- **Fly.io:** rhea-tribunal.fly.dev LIVE (JWT auth, dev-bypass blocked)

## Products (all shipped)
- **iOS:** build 12, TestFlight LIVE, auth gate + 8 tabs
- **Play (macOS):** 12-pane ops centre, DMG in GitHub Release
- **rhea-memory:** Python package, pip-installable, CLI ready
- **Landing:** rhea-tribunal.fly.dev with signup + product links

## Surfaces
- **Tribunal (:8400):** 54+ endpoints + auth + supervisor
- **Atlas (:3000):** Next.js — live
- **Rust TUI:** /opt/homebrew/bin/rhea (1.5MB)
- **NDI:** libndi v6.2.0 local, graceful cloud degradation

## Aletheia — LIVE (11 proofs)
- 9 endpoints, dedup+ontology, proof.db

## Auth
- JWT signup/login at /auth, Keychain storage on iOS
- Production secrets: JWT_SECRET + TRIBUNAL_API_KEYS on Fly.io

## Next
- Entity registration (TimeLabs NPO) → ASC developer name
- PyPI publish for rhea-memory
- App Store submission (build 12 ready)
