# Learning Path

How to understand Rhea from zero to contributor in 30 minutes.

## Level 1: What is this? (5 min)

Read these two files:
1. `VISION.md` — the problem and approach
2. `README.md` — how the system works, quick start commands

After this you know: what Rhea does, why it exists, and how to run it locally.

## Level 2: How does it work? (10 min)

Read these three files:
1. `architecture.md` — scientific foundation, 8-agent system, data architecture
2. `ARCHITECTURE_FREEZE.md` — iOS app structure (Core/UI/Infrastructure layers)
3. `decisions.md` — the 14 ADRs that explain every major choice

After this you know: the science behind the recommendations, the agent system, and why each architectural decision was made.

## Level 3: What's happening right now? (5 min)

Read these files:
1. `ops/BACKLOG.md` — all work items with status
2. `ops/virtual-office/TODAY_CAPSULE.md` — current priorities and blockers
3. `ops/virtual-office/INCIDENTS.md` — what's broken and how it's being handled

After this you know: what's done, what's in progress, and where help is needed.

## Level 4: How do I contribute? (10 min)

1. `COMMUNITY.md` — contribution areas and what helps
2. `ops/virtual-office/OFFICE.md` — how agents coordinate (relevant if you're adding automation)
3. `src/rhea_bridge.py` — read the first 120 lines (tier config + provider registry)

After this you know: where to plug in, what patterns to follow, and how the multi-model bridge works.

## Key concepts

| Concept | One-liner | Where to learn more |
|---------|-----------|-------------------|
| Daily defaults | The unchosen routines modern life imposes | `VISION.md` |
| Hunter-gatherer baseline | Forager patterns as calibration zero | `architecture.md`, ADR-006 |
| Passive profiling | Behavior signals, not questionnaires | ADR-005 |
| Tribunal mode | 5 models answer same question, compare | `src/rhea_bridge.py` |
| Cost tiers | Cheap-first, expensive requires justification | ADR-008, bridge tier config |
| Promotion protocol | Chat → gem → procedure → incident → decision | `ops/virtual-office/OFFICE.md` |
| Context Tax Collector | Token budget enforcement per session | `ops/virtual-office/GEMS.md` GEM-001 |

## Still confused?

Open an issue. Specific questions get specific answers.
