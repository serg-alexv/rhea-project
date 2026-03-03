# RHEA ACTIVE STATE (v4.2)
> Date: 2026-03-03 | Agent: REX (Opus 4.6) | Mode: SOVEREIGN | Stage: 4-RELEASE

## System
- **CHECK:** `bash scripts/rhea/check.sh` → OK
- **GIT:** `stage4-release` | **Release:** v1.0.0 shipped
- **Fly.io:** rhea-tribunal.fly.dev LIVE (JWT auth, dev-bypass blocked)
- **Secrets:** GCloud SM (rhea-office-sync) — cockroachdb-url, mongodb-url

## Products
- **iOS:** build 28 (v1.0.28), TestFlight, auth + 8 visible tabs, VPN entitlement
- **Play (macOS):** v1.0 DMG shipped, 12-pane ops centre
- **rhea-memory:** Python package, pip-installable, CLI ready
- **Landing:** rhea-tribunal.fly.dev with signup + OAuth

## Databases (3-tier)
- **SQLite:** local proof.db, tasks.db, users.db — zero latency
- **CockroachDB:** rhea-flow v25.4.1, GCP EU-West3 — distributed SQL
- **MongoDB:** Atlas rhea v8.0.19 — documents + change streams

## Atlas (:3000) — 13 pages live
- `/cc/design` (SwiftUI tool), `/cc/paper` (biotech figures), `/cc/logic`, `/cc/graphics`
- `/cc/automation`, `/cc/decisions`, `/cc/papers`, `/cc/wallet`

## Pending
- Fly.io deploy with new Atlas landing (Orion's WOW page)
- CockroachDB schema: tasks, workflows, billing
- MongoDB change streams → real-time push
- VPN auto-install (NEVPNManager wiring)
- App Store submission + PyPI publish
