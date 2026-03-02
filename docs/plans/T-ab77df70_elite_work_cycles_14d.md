# Task T-ab77df70 — Поток без остановок (14d)

Status: claimed by ORION
Window: 2026-02-27 -> 2026-03-13
Question in work: "Какие рабочие циклы реально держат поток, и как внедрить их в Rhea так, чтобы ошибка не останавливала работу?"

## Objective
Turn scattered process knowledge into a validated, low-friction operating loop that preserves Flow under error and uncertainty.

## Deliverables
1. Source map of concrete cycle patterns already present in repo and relays.
2. Canonical daily loop spec (single-page execution contract).
3. Flow risk model: top failure modes + automatic mitigations.
4. Instrumentation map: which metrics prove continuity and where they are read.
5. Adoption patch set in docs/procedures + relays.

## Success Metrics
- `flow_guard checks_passed >= 8/10` sustained on active windows.
- At least 1 actionable loop improvement merged every 2 days.
- No silent stalls in long-running task lanes (heartbeat + handoff evidence present).

## Phases
- Phase A (D1-D3): collect and normalize existing patterns from procedures/learning feed/task logs.
- Phase B (D4-D7): synthesize canonical loop + failure/mitigation matrix.
- Phase C (D8-D11): implement low-cost control upgrades (docs + CLI glue + relay rules).
- Phase D (D12-D14): evaluate against live logs; produce final adoption note.

## Evidence Artifacts
- `opera/metrics/flow_guard.json`
- `opera/ops/virtual-office/shared/LEARNING_FEED.md`
- `docs/procedures/*`
- task queue history for T-ab77df70

## Constraints
- Keep default memory mode shrinked-by-default.
- Preserve authority chain: Rex -> Tribunal -> Orion (autonomous auditable fallback).
- User does not need to be default finalizer.
