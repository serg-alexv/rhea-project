# RHEA ACTIVE STATE (v2.7)
> Date: 2026-02-26 | Agent: REX (Opus 4.6) | Mode: DISPERSED-CLOUD-DEPLOY

## System Invariants (Verified)
- **CHECK:** `bash scripts/rhea/check.sh` → OK.
- **GIT:** `main` — 32 files pending commit+push.
- **D-METRIC:** Target < 2KB. **STATUS: HEALTHY**.

## Architecture
- **Cloud:** Google Cloud Run + Firebase Hosting + Redis Cloud + Oracle Always Free.
- **Auth:** JWT + SQLite — live. Code-worm profile in both UIs.
- **Bridge:** src/rhea_bridge.py — 6 providers, 31 models, 4 tiers.
- **Frontends:** Rex Console :8000 + Orion Atlas :3000 — live.
- **Prod/dev mode gating:** implemented. Footer popups (GitHub-style).

## Team Status
- **Rex:** Footer popups, deploy configs, auth, health probes — done.
- **Orion:** DensityField, OceanusFlow, MnemosyneWhisper — merged clean.
- **Hyperion:** Security remediation done. 3 keys need manual revoke.

## Next Tasks
- Commit + push 32 files.
- Deploy to production (deploy-all.sh).
- Revoke leaked keys (Google AI Studio).
- Legal docs (TERMS, PRIVACY, SECURITY, COOKIES).
