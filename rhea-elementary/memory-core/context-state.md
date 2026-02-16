# Context State — Project Status Snapshot
> Updated: 2026-02-16

## Architecture
- 8 agents (A1-A8) + watcher (A0), defined in .claude/agents/
- Bridge: src/rhea_bridge.py (6 providers, 31 models, 4 tiers)
- Live: OpenAI + OpenRouter | Down: Gemini(quota), DeepSeek(balance), Azure(creds), HF(bug)
- Chronos Protocol v3, soul.md as shared foundation

## Memory Layers
| Layer | File | Auto-loaded? |
|-------|------|-------------|
| L0 | MEMORY.md | Yes (every session) |
| L1 | CLAUDE.md | Yes (every session) |
| L2 | context-core.md | Read on demand |
| L3 | context-state.md | Read on demand |
| L4 | context-bridge.md | Read on demand (handoff notes) |
| L5 | knowledge-map.md | Deep context |
| L6 | claude-sessions.md | Archaeology |
| L7 | Entire.io snapshots | Episodic |
| L8 | Git history | Full audit trail |

## Key Stats
- 103 commits, 15 branches, 28 sessions (71% error deaths)
- 43 snapshots, 19 Entire.io sessions, 26 doc files
- 14 ADRs, 2 tribunals, 5 reflection log entries
- Genesis: "Давай обсудим преимущества и недостатки григорианского календаря" (eb53e82c)

## Tools & Services
- LogRocket: bquken/rhea (free, 1000 sessions/mo)
- Entire.io: auto-commit strategy
- GitHub: Gemini code review enabled
- Watcher daemon: scripts/watcher-start.sh (PID-based monitor)
- Chrome: AppleScript+JS automation available
