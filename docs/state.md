# RHEA ACTIVE STATE (v3.1)
> Date: 2026-02-26 | Agent: REX (Opus 4.6) | Mode: ALETHEIA-WIRED

## System Invariants (Verified)
- **CHECK:** `bash scripts/rhea/check.sh` → OK.
- **GIT:** `stage4-release` — Aletheia wiring + dedup done.
- **D-METRIC:** 268.98 — HEALTHY.

## Architecture
- **Cloud:** Google Cloud Run + Firebase Hosting + Redis Cloud + Oracle Always Free.
- **Bridge:** src/rhea_bridge.py — 6 providers, 31 models, 4 tiers.
- **Themis Console (:8000):** rhead.py → mounts aletheia_router at /aletheia/*
- **Tribunal API (:8400):** tribunal_api.py → capture hooks only, no read dupes
- **Atlas Prime (:3000):** Next.js frontend — live.

## Aletheia Architecture (CLEAN)
- **Capture:** tribunal_api.py calls aletheia.capture() after /tribunal, /ice, /sceptic
- **Read API:** aletheia_api.py via rhead.py → /aletheia/{stats,proofs,search,chain,verify,submit}
- **Storage:** data/proof.db (shared SQLite) + friends/aletheia/{proofs,hypotheses}/ (markdown)
- **No duplication:** removed 7 duplicate read endpoints from tribunal_api.py

## IMPLEMENTATION_SPEC.md — 6 phases:
1. Store foundations — **done**
2. Hyperion Bar → **waiting** (Hyperion unblocked)
3. Mnemosyne Whispers → **done** (Orion)
4. Oceanus Flow → **done** (Orion)
5. Krikoi Titanon → **IN PROGRESS**
6. Aletheia Pipeline → **WIRED** (capture + API + submit)

## Next
- Restart uvicorn to activate captures
- ChatGPT Apps SDK evaluated (see state_full.md)
- Krikoi rings + Hyperion Bar remain
