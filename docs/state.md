# RHEA ACTIVE STATE (v4.1)
> Date: 2026-03-02 | Agent: REX (Opus 4.6) | Mode: SOVEREIGN | Stage: 4-RELEASE

## System
- **CHECK:** `bash scripts/rhea/check.sh` → OK
- **GIT:** `stage4-release` | **Release:** v1.0.0 shipped
- **Fly.io:** rhea-tribunal.fly.dev LIVE (JWT auth, dev-bypass blocked)

## Products (all shipped)
- **iOS:** build 12, TestFlight LIVE, auth gate + 8 tabs
- **Play (macOS):** v1.0 DMG shipped, 12-pane ops centre
- **rhea-memory:** Python package, pip-installable, CLI ready
- **Landing:** rhea-tribunal.fly.dev with signup + OAuth

## Atlas (:3000) — 11 pages live
- `/` (home), `/cc` (core), `/cc/automation`, `/cc/decisions`, `/cc/papers`, `/cc/graphics`
- API health, 404, proof listings

## Features — Stage 4
- **Auth:** JWT signup/login + OAuth (Google, Microsoft) at /auth
- **Billing:** Credits ledger, ADMIN_EMAILS genline, 100-credit signup bonus
- **Graphics:** SVG/PNG editor (/cc/graphics): shapes, text, freehand, image import, export
- **Papers:** PDF annotation (/cc/papers): tribunal, aletheia, note, ontology tools
- **Decisions:** Interactive sovereignty map (/cc/decisions)
- **Aletheia:** 9 endpoints, 11 proofs, dedup+ontology

## Surfaces
- **Tribunal (:8400):** 54+ endpoints + auth + supervisor
- **Atlas (:3000):** Next.js — live
- **Rust TUI:** /opt/homebrew/bin/rhea (1.5MB)
- **NDI:** libndi v6.2.0 local, graceful cloud degradation

## Pending
- Apple Network Extension entitlement (submitted)
- Entity registration (timelabs npo) → ASC developer name
- PyPI publish for rhea-memory
- App Store submission
