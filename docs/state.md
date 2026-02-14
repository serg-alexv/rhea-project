# Rhea — compact state

## Mission
Mind Blueprint factory: generate, evaluate, iterate on daily structure models using scientific rhythms, multi-model tribunal, and closed-loop planner.

## Architecture
3-product: Rhea Core (toolset/memory/engine) → iOS App (SwiftUI+HealthKit) → Commander (React/TUI, deferred). See docs/architecture.md.

## Status
- Architecture: v3, 8 agents, Chronos Protocol, 3-product layered design
- Bridge (rhea_bridge.py): live — 6 providers, all keys verified, first tribunal completed
- Docs: normalized, user guide updated, upgrade_plan_suggestions.md created
- Ops: scripts/rhea/ CLI + .entire snapshots/logs + per-query persistence (ADR-014)
- Memory economy: D=63.4, T1=150, T2=300 — ADR-010
- Git: PR#2 merged, main current, 14 ADRs, 2 Tribunals
- Entire.io: auto-commit (ADR-014) via scripts/rhea_commit.sh (ADR-013)

## Next
1. Install Entire GitHub App → checkpoints visible at entire.io dashboard
2. Define minimal user loop → 5-min interaction design before code
3. iOS MVP → SwiftUI + HealthKit, ONE agent, ONE intervention

## Refs
- Full state: docs/state_full.md
- Upgrade plan: docs/upgrade_plan_suggestions.md
- Decisions: docs/decisions.md (14 ADRs)
- Architecture: docs/architecture.md
