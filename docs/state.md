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
- Entire.io: manual-commit strategy, checkpoint pipeline working (2 checkpoints on GitHub)

## Entire.io Integration
- Strategy: manual-commit (trailers added to user commits)
- Hooks: commit-msg (chmod +x fixed), post-commit, pre-push — all working
- Checkpoints on GitHub: 9f2cf70d71cb, b0010aef23e3 (entire/checkpoints/v1 branch)
- **ACTION REQUIRED**: Install Entire GitHub App at github.com/apps/entire → grant access to rhea-project
- SSH key for push: ~/.ssh/id_ed25519_rhea
- Worktree cleanup needed: `git worktree remove /tmp/entire-wt` (run from macOS terminal)

## Next
1. **Install Entire GitHub App** → checkpoints visible at entire.io dashboard
2. Wire bridge to .env keys → first live tribunal
3. iOS MVP scaffold (Stage 1)
4. Feed prism_paper_outline.md to OpenAI Prism

## Refs
- Full state: docs/state_full.md
- Decisions: docs/decisions.md
- Architecture: docs/architecture.md
