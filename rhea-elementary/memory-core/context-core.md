# Context Core — What Matters RIGHT NOW
> Auto-updated by each session. Read this FIRST.

## Current Focus
- Full data extraction DONE — 3 agents read all 48+ files, extracted to dumps/
- Memory architecture operational (trinity + pre-memory-snapshot + MEMORY.md)
- Bridge: 2/6 live (OpenAI, OpenRouter), 4 down with known causes
- **CRITICAL: "17 sessions of thinking, zero shipped code" (W1)**

## Active Decisions
- Execution Protocol: act first, never ask, NEVER pause for "continue?" — answer is ALWAYS YES (CLAUDE.md)
- All 9 agents have autonomy + no-pause directive
- Background agents broken — foreground only
- Bonsai removed from sensitive paths
- Gemini accessible via OpenRouter (geo-bypass)
- Workspace-first architecture (InfiAgent pattern) — sessions disposable, workspace permanent

## Critical Gaps Found (from full extraction)
1. Zero shipped code — no iOS, no LangGraph, no product
2. 3 required docs missing: CORE_MEMORY.md, TODO_MAIN.md, SELF_UPGRADE_OPTIONS.md
3. Chronos inter-agent messages not wired to bridge
4. state_full.md stale by 3+ days
5. D metric inconsistent across 3 docs (63.4 vs 62.7 vs 91.96)
6. Model count: docs say 400+, bridge has 31
7. 7 MCP servers untested

## Immediate Next Steps
1. Ship one thing publicly (article_gpt_pro_vs_cowork.md is ready to publish)
2. Create SELF_UPGRADE_OPTIONS.md, TODO_MAIN.md, CORE_MEMORY.md
3. Fix bridge: retry logic, cost tracking, HF token count
4. iOS MVP scaffold (SwiftUI + HealthKit, one agent, one intervention)
5. Wire [CHRONOS:A->A] messages to rhea_bridge.py

## Human State (last observed)
- Awake 40+ hours, teaching AI to evolve
- Frustrated by session deaths and lack of shipped output
- Mandate: never ask, never pause, just execute and report
- Biochemist, musician, legacy builder
