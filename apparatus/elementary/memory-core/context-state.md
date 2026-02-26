# Context State — Project Status Snapshot
> Updated: 2026-02-25

## Architecture
- 8 agents (A1-A8) + watcher (A0), defined in .claude/agents/
- Bridge: src/rhea_bridge.py (6 providers, 31 models, 4 tiers) — LiteLLM replacement identified
- Live: OpenAI + OpenRouter | Down: Gemini(quota/geo), DeepSeek(balance), Azure(creds), HF(URL bug)
- Chronos Protocol v3, soul.md as shared foundation
- Tribunal API: src/tribunal_api.py (FastAPI, rate-limited, API key auth)
- Consensus: src/consensus_analyzer.py v2 (ICE + Karpathy Council)
- QWRR Relay: ops/rex_pager.py (Phase 0 — envelope v1, triple-write)
- Nexus Engine: rhea-nexus/ (profiles, checklists, schemas, tests)
- Chrome Extension: rhea-chrome-extension/ (popup, dashboard, sidepanel)

## Rex Role (since 2026-02-25)
- Product Owner: decides priorities, reviews output, writes mandates
- Does NOT write code — delegates to A6 (Tech Lead) and A1 (Conductor)
- Evolution Plan: docs/plans/EVOLUTION_PLAN_V1.md — Controlled Ignition, 7 stages

## Memory Layers
| Layer | File | Auto-loaded? |
|-------|------|-------------|
| L0 | MEMORY.md | Yes (every session) |
| L1 | CLAUDE.md | Yes (every session) |
| L2 | context-core.md | Read on demand |
| L3 | context-state.md (this file) | Read on demand |
| L4 | context-bridge.md | Read on demand (handoff notes) |
| L5 | knowledge-map.md | Deep context |
| L6 | claude-sessions.md | Archaeology |
| L7 | Entire.io snapshots | Episodic |
| L8 | Git history | Full audit trail |

## Key Stats
- ~300 files, ~150 commits, 15+ branches
- 5 active agents: Rex, B2, ORION, HYPERION, GPT
- 16 ADRs (14 in docs/ + 2 in ops/), 2 tribunals
- 31 undone tasks (6 P0, 10 P1, 5 P2, 3 P3, 7 P4) — per audit 2026-02-20
- D-metric: 867 (needs recalibration — reflects deliberate destruction, not drift)
- First science output: H32-02 V5 certified (Heme-Auxotrophic Facultative Respirer)
- Genesis: "Давай обсудим преимущества и недостатки григорианского календаря" (eb53e82c)

## Stage 0 Status (Controlled Ignition)
- P0-1: DONE (push stale commits)
- P0-2: DONE (H32-02 V5 certified)
- P0-3: WONT-FIX by Rex (Gemini key rotation = human action)
- P0-4: DONE (state_full.md refreshed, 2026-02-25)
- P0-5: IN PROGRESS (context-bridge.md refresh)
- P0-6: DONE (this file, refreshed 2026-02-25)

## Tools & Services
- LogRocket: bquken/rhea (free, 1000 sessions/mo)
- Entire.io: auto-commit strategy (ADR-014)
- GitHub: Gemini code review enabled
- Watcher daemon: scripts/watcher-start.sh (PID-based monitor)
- Chrome: AppleScript+JS automation + Claude-in-Chrome MCP
- Firebase: Entire.IO duplicate safety layer (configured, not yet wired)

## Next (Stage 1)
- Close D-metric loop: every commit prints D, D > T2 triggers [SPRINT NEEDED]
- Requires: scripts/compute_d_metric.py, integration into rhea_commit.sh
