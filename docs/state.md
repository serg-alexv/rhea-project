# Rhea — Project State (compact)

## Mission
Reconstruct daily defaults with a multi-provider LLM bridge and an iOS closed-loop scheduler.

## Deliverables
- Scientific paper “Mathematics of Rhea”
- iOS app “Rhea” (SwiftUI + HealthKit + Apple Watch)
- Multi-provider bridge rhea_bridge.py (ask/tribunal/models_status)

## Status (high level)
- Architecture: v3 fixed (roles merged, 8→≈5 effective agents)
- Docs: imported & normalized into docs/
- Ops: ./rhea CLI + .entire snapshots/logs working locally

## Next 30 days (focus)
1. Implement rhea_bridge.ask / tribunal / models_status in src/rhea_bridge.py.
2. Build minimal iOS MVP that calls the bridge for next-best-action.
3. Connect .entire/snapshots + ops.jsonl as long-memory source into entire.io.

## Notes
- Full verbose state: docs/state_full.md
- Decisions & ADRs: docs/decisions.md
- Architecture details: docs/architecture.md
