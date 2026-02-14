# Rhea — compact state

## Mission
Mind Blueprint factory: generate, evaluate, iterate on daily structure models using scientific rhythms, multi-model tribunal, and closed-loop planner.

## 3-Product Architecture (Session 17)
- **Rhea Core** — toolset, memory, self-evolution engine (foundation layer)
- **Rhea iOS App** — personal advisor (consumer surface, SwiftUI + HealthKit)
- **Rhea Commander** — React UI / TUI CLI (power-user surface, deferred to post-MVP)

## Status
- Architecture: v3 fixed, 8 agents, Chronos Protocol, 3-product layered design
- Bridge: ✅ live (6 providers, all keys verified, first real tribunal completed)
- Docs: normalized, user guide updated, upgrade_plan_suggestions.md created
- Ops: ./rhea CLI + .entire snapshots/logs + per-query persistence (ADR-014)
- Memory economy: D=63.4 (comfort), T1=150, T2=300 — ADR-010
- Git: PR#2 merged, main up to date, 14 ADRs, 2 Tribunals completed
- Entire.io: auto-commit (ADR-014, reversed ADR-012) + rhea_commit.sh wrapper (ADR-013)
- **Session 17 tribunal:** 7 warnings identified, solutions documented in upgrade_plan_suggestions.md

## Entire.io Integration
- Strategy: **auto-commit** (ADR-014) — separate `[entire]`-prefixed commits after each agent response
- Per-query persistence: `scripts/rhea_query_persist.sh` logs every interaction
- **ALWAYS use `scripts/rhea_commit.sh` instead of raw `git commit`** (ADR-013)
- Checkpoints on GitHub: entire/checkpoints/v1 branch (JSON metadata)
- **ACTION REQUIRED**: Install Entire GitHub App at github.com/apps/entire → grant access to rhea-project
- SSH key for push: ~/.ssh/id_ed25519_rhea

## Next (post-tribunal priority)
1. **Install Entire GitHub App** → checkpoints visible at entire.io dashboard
2. **Define minimal user loop** → 5-min interaction design before any code
3. **Wireframe iOS app** → days 1/7/30 UX
4. **iOS MVP implementation** → SwiftUI + HealthKit, ONE agent, ONE intervention
5. **Validate 3 interventions** → measure with beta testers
6. **Paper: pivot to chronotype alignment** → polyvagal as hypothesis, not centerpiece

## Refs
- Full state: docs/state_full.md
- Upgrade plan: docs/upgrade_plan_suggestions.md
- Decisions: docs/decisions.md (14 ADRs)
- Architecture: docs/architecture.md
