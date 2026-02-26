# Pre-Memory Snapshot — Complete Data Archaeology
> Generated: 2026-02-16 by Opus 4.6 (1M context)
> Purpose: Everything needed to restore full context in any new session

## 1. Project Identity
- **Name:** Rhea — multi-agent advisory system (chronobiology + control theory)
- **Named after:** Titan goddess, mother of Olympians, wife of Kronos (Time). She tricked Time to save the future.
- **Genesis:** "Давай обсудим преимущества и недостатки григорианского календаря" (chat eb53e82c)
- **Genesis chain:** Calendar critique → 42 systems → symbolic power → health → daily defaults → polyvagal+ADHD → 8 agents → iOS app + paper
- **Two deliverables:** Scientific paper ("Mathematics of Rhea") + iOS App (SwiftUI+HealthKit)

## 2. Human Profile
- Biochemist-scientist, drug discovery background
- ADHD + anankastic compensatory architecture
- Bilingual RU/EN, code-switching natural
- Musician: SoundCloud artist (Mika IO feat SA / Флюиды)
- St. Petersburg connection (КППИТ, ЕСЭД government systems)
- Builder identity — Rhea itself is the proof
- Legacy builder — wants something that outlasts the session
- Trust-forward — says "yes you can" when AI says "I can't"

## 3. Architecture (Chronos Protocol v3)
- 8 agents (A1-A8) + watcher (A0)
- Opus 4 for reasoning (A1,A2,A4,A8), Sonnet 4 for execution (A3,A5,A6,A7)
- Agent definitions in .claude/agents/: qdoc, lifesci, profiler, culturist, architect, techlead, growth, reviewer, watcher
- Multi-model bridge: src/rhea_bridge.py (6 providers, 31+ models, 4 cost tiers, tribunal mode)
- Default tier: cheap. Escalation requires justification (ADR-008/009)

## 4. Memory Architecture
- docs/state.md — compact state (<2KB, check.sh enforced)
- docs/state_full.md — append-only narrative log
- .entire/snapshots/ — 43 episodic snapshots
- .git/entire-sessions/ — 19 session logs
- MEMORY.md — auto-loaded into every session
- CLAUDE.md — project bootstrap context
- rhea-elementary/memory-core/ — compiled knowledge (THIS directory)
- Discomfort function D with thresholds T1=150, T2=300 (ADR-010)

## 5. Bridge Status (2026-02-16)
| Provider | Status | Issue |
|----------|--------|-------|
| OpenAI | ✅ LIVE | Working |
| OpenRouter | ✅ LIVE | Gemini, Sonnet, DeepSeek R1 all accessible |
| Gemini T0 | ❌ 429 | Quota exceeded |
| Gemini T1 | ❌ 400 | Geo-blocked (user in RU, needs VPN) |
| DeepSeek | ❌ 402 | Insufficient balance |
| Azure | ❌ 401 | Bad credentials (key rotation needed) |
| HuggingFace | ❌ 404 | URL construction bug in bridge |

## 6. Key Decisions (14 ADRs)
- ADR-001: 10→8 agents (merge overlapping roles)
- ADR-002: Multi-model bridge over single provider
- ADR-003: ADHD-optimized design (assume executive dysfunction)
- ADR-004: Opus for research, Sonnet for execution
- ADR-005: Passive profiling (no questionnaires)
- ADR-006: Hunter-gatherer calibration zero
- ADR-007: Three-tier external memory
- ADR-008: Tiered model routing (cheap-first)
- ADR-009: Agent cost integration
- ADR-010: Memory budget + discomfort metric
- ADR-011: Self-evaluation techniques (Reflexion, tribunal, teacher-student)
- ADR-012: Keep manual-commit (superseded by ADR-014)
- ADR-013: Wrapper script for Entire.io checkpoints
- ADR-014: Per-query persistence + auto-commit

## 7. Tools & Services
- Entire.io: auto-commit strategy, snapshots, session tracking
- LogRocket: bquken/rhea, free tier (1000 sessions/mo, 1mo retention, $0)
- GitHub: serg-alexv/rhea-project, Gemini code review enabled
- Firebase: planned as Entire.IO duplicate safety layer
- Chrome: AppleScript+JS automation available (see chrome-automation.md)
- Watcher daemon: scripts/watcher-start.sh (PID monitor, macOS notifications)

## 8. Critical Operational Facts
- Background agents (run_in_background:true) are BROKEN — always foreground
- Bonsai/Trybons: removed from settings, DO NOT use for sensitive info
- 28 sessions in 4 days, 71% died from errors, 18% context overflow
- Session death = 20 hours lost on average for re-bootstrapping
- User mandates: never go dark, continuous mindflow, no questions—just act, every insight = memory write

## 9. Files In This Directory
- timeline.md — chronological map of 43 snapshots
- conversations.md — 5 chat extracts mapped
- knowledge-map.md — 25 docs, 14 ADRs, 2 tribunals, cross-references
- claude-sessions.md — all 28 Claude Code sessions cataloged
- pre-memory-snapshot.md — THIS FILE (complete restoration context)

## 10. What's Next (from docs/NOW.md)
- Tier 0: Fix broken (state.md size, benchmark false positives, rhea CLI)
- Tier 1: Foundations (agents, SELF_UPGRADE_OPTIONS, TODO_MAIN, CORE_MEMORY)
- Tier 2: Tooling (test MCP servers, wire Playwright, expand audit)
- Tier 3: Hardening (tribunal triggers, auto-PR, Entire GitHub App)
