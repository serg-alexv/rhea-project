# MANDATE: Stage 0 P0 Debt Clearance
> FROM: Rex (Product Owner)
> TO: A6 (Tech Lead)
> DATE: 2026-02-25
> PRIORITY: P0
> PLAN: docs/plans/EVOLUTION_PLAN_V1.md — Stage 0

## Tasks (execute in order)

### Task 1: Update state_full.md
- File: `docs/state_full.md`
- Problem: Last entry is 2026-02-13 (12 days stale)
- Action: Append entries for 2026-02-14 through 2026-02-25 covering:
  - Tribunal API shipped (2026-02-17)
  - QWRR Phase 0 operational (2026-02-17)
  - ORION joined: Nexus engine, Chrome extension, profile manager (2026-02-19)
  - HYPERION joined: adversarial audit, Gemini CLI (2026-02-19)
  - H32-02 genetics V1→V5 certified (2026-02-19→2026-02-20)
  - Rex 1M restore + full audit + learning feed + TODO consolidation (2026-02-20)
  - LiteLLM analysis (2026-02-20)
  - Evolution Plan V1 created (2026-02-25)
- Source: git log, REX_FULL_PROJECT_AUDIT_20260220.md, nexus/README.md

### Task 2: Update context-bridge.md
- File: `rhea-elementary/memory-core/context-bridge.md`
- Problem: 9 days stale. ORION overwrote it with Nexus state export on 2026-02-20.
- Action: Rewrite as a proper handoff note (what happened, what was learned, what next session should do)
- Cover: all 5 new agents, genetics resolution, Evolution Plan, LiteLLM

### Task 3: Update context-state.md
- File: `rhea-elementary/memory-core/context-state.md`
- Problem: 9 days stale, frozen at pre-ORION state
- Action: Refresh to reflect current reality: 5 agents, V5 certified, Evolution Plan active, Stage 0 in progress

## Constraints
- Use `bash scripts/rhea_commit.sh -m "..."` for every commit
- Push after each task
- Cheap tier only
- Report results to inbox as structured artifacts
