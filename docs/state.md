# RHEA ACTIVE STATE (v3.3)
> Date: 2026-02-28 | Agent: REX (Opus 4.6) | Mode: SOVEREIGN

## System
- **CHECK:** `bash scripts/rhea/check.sh` → OK
- **GIT:** `stage4-release` — 69 commits today
- **D-METRIC:** ~269 — HEALTHY

## Architecture
- **Cloud:** GCR + Firebase + Redis Cloud + Oracle Free
- **Bridge:** src/rhea_bridge.py — 6 providers, 31 models, 4 tiers
- **Themis (:8000):** rhead.py → /aletheia/*
- **Tribunal (:8400):** + /agents/status (unified, new)
- **Atlas (:3000):** Next.js — live

## Aletheia — LIVE (7 proofs)
- Capture: 3 hooks in tribunal_api.py
- Read: 9 endpoints (/stats,proofs,search,chain,verify,submit,dedup,ontology)
- Storage: data/proof.db + friends/aletheia/

## iOS App — IN PROGRESS
- Radio (SSE + composer), Governor, Pulse, Dialog tabs
- TestFlight pipeline built — upload blocked on URLs
- 14 deps forked to serg-alexv (supply chain sovereign)

## Absorbed Today
- Entire.io → lib_rhea_hooks.sh (ADR-016)
- python-dotenv → env_loader.py
- Bonsai/ZMQ → archive/absorbed/
- OpenClaw → patterns only (ADR-015), no runtime dep

## Blocked
- TestFlight: needs Marketing URL + Privacy Policy URL
- Gemini key expired — Dialog tab dead
- 13+ stale tasks in queue (Orion diagnosed)
- Share Extension: workspace contention

## Full day log: docs/TODAY_2026-02-28.md
