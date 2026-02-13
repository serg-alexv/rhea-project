# Rhea — compact state

## Mission
Mind Blueprint factory: generate, evaluate, iterate on daily structure models using scientific rhythms, multi-model tribunal, and closed-loop planner.

## Deliverables
- Scientific paper "Mathematics of Rhea" → outline ready (docs/prism_paper_outline.md)
- iOS app "Rhea" (SwiftUI + HealthKit + Apple Watch)
- Multi-provider bridge rhea_bridge.py → ✅ implemented (src/rhea_bridge.py)

## Status
- Architecture: v3 fixed, 8 agents, Chronos Protocol
- Bridge: implemented (6 providers, ask/tribunal/models_status)
- Docs: normalized, prism paper outline created
- Ops: ./rhea CLI + .entire snapshots/logs working
- Memory economy: D=91.96 (comfort), T1=150, T2=300 — ADR-010
- LangGraph: design phase (docs/langgraph_architecture.md)
- Git: PR#2 merged, main up to date
- Entire.io: auto-commit enabled, checkpoints via Claude Code CLI

## Next
1. Wire bridge to .env keys → first live tribunal
2. iOS MVP scaffold (Stage 1)
3. Feed prism_paper_outline.md to OpenAI Prism
4. Entire.io checkpoint pipeline — verify end-to-end

## Refs
- Full state: docs/state_full.md
- Decisions: docs/decisions.md
- Architecture: docs/architecture.md

## Entire.io Integration
Checkpoint pipeline: commit-msg hook fixed (chmod +x), auto-commit enabled.
Session detection: Claude Code CLI triggers Entire session creation.
