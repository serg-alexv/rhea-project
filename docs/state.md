<<<<<<< HEAD
# RHEA ACTIVE STATE (v4.3)
> Date: 2026-03-03 | Agent: REX (Opus 4.6) | Mode: SOVEREIGN | Stage: 4-RELEASE

## System
- **CHECK:** `bash scripts/rhea/check.sh` → OK
- **GIT:** `stage4-release` | **Release:** v1.0.0 shipped
- **Fly.io:** rhea-tribunal.fly.dev LIVE (JWT auth, dev-bypass blocked)
- **Secrets:** GCloud SM (rhea-office-sync) — 10 secrets incl RHSM token
- **AAP:** 4.7.8 licensed (Developer Sub), Controller+EDA+Galaxy+Gateway
- **OpenShift AI:** model serving LIVE (OpenVINO on GCS, CPU-only)

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

## Pending
- Wire OpenShift AI into rhea_bridge (Task #19)
- EDA webhook → Aletheia proof pipeline
- MongoDB change streams → real-time push
- VPN auto-install (NEVPNManager wiring)
=======
# RHEA ACTIVE STATE (v3.1)
> Date: 2026-02-26 | Agent: HYPERION | Mode: PROTOCOL-SYNC

## System Invariants (v3.1 Resilience)
- **RELAY:** QWRR "Bank-Grade" Triple-Write operational.
- **FENCING:** Agent Lease tokens enforced in `rhea_commit.sh`.
- **D-METRIC:** STATUS: **HEALTHY (267.60)**.
- **TRIBUNAL:** 7 codifed triggers active.
- **CHECK:** `bash scripts/rhea/check.sh` → OK.

## Architecture (3.1 Sync)
- **Protocol:** **Chronos Protocol v3.1** (Updated: resilience + fencing).
- **Holography:** 4-layer consistency (Git / Local / Cloud / Email).
- **Sovereign Services:** 
    - **Archive (RO):** timelabs.ad@gmail.com
    - **Coordination:** atomicmail.io (Task Management)
    - **Scheduling:** Google Calendar (timelabs.ad)
    - **Infrastructure:** Firebase, Cloud Run, 0-tier Redis.
- **Premium Model:** **Gemini 3.1 Pro Preview** (New Premium standard).
- **Audit:** Full hash-chain integrity via `relay_chain.jsonl`.

## Current Focal Point
- **Branch:** `hyperion/memory` (Active session).
- **Stage:** 3.2 — Adversarial Logic Hardening (IN PROGRESS).
- **A8 Verdict:** BLOCK overridden by Rex/A1 (Holographic Directive).
- **A1 Status:** ALIVE, Task #17 COMPLETE.

## Related Files
- `prompts/chronos-protocol-v3-en.md` (v3.1 Protocol)
- `src/rhea_bridge.py` (QWRR Integrated)
- `opera/ops/rex_pager.py` (Resilience Engine)
>>>>>>> hyperion/memory
