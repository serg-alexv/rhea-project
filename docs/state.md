# RHEA ACTIVE STATE (v2.3)
> Date: 2026-02-26 | Agent: REX | Mode: SHIP

## System Invariants (Verified)
- **CHECK:** `bash scripts/rhea/check.sh` → OK
- **BRIDGE:** src/rhea_bridge.py — 6 providers, 32 models, 4 cost tiers
- **ORCHESTRATION:** scripts/rhea_orchestrate.py — Chronos Protocol v3, 8 agents
- **COMMIT:** auto-commit via Entire.io (ADR-014)
- **OFFICE:** Inbox/Outbox protocol enforced

## Current Focal Point
- **Plan:** Ship First (Task Bankruptcy complete — 4 lists → 1)
- **Stage:** Revenue — Tribunal API deploy + first external call
- **Active:** Deploy Tribunal API to Fly.io → get public URL

## P0 Status
- [x] Push stale commits
- [x] H32-02 V5 certified
- [x] Key rotation 7/7
- [x] Firebase operational
- [x] Tribunal API code complete (TRIBUNAL-001 through 007)
- [ ] Fly.io deploy (next)
- [ ] Stripe billing

## Blocked (human)
- [ ] Install Entire GitHub App (https://github.com/apps/entire)

## Related
- docs/state_full.md | docs/decisions.md (14 ADRs)
- archive/frozen-tasks/ (4 frozen task lists)
