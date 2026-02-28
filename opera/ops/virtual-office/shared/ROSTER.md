# Agent Roster — Who Is Who Today
> Purpose: Any agent or human reads this on boot to know the current team.
> Rule: Update YOUR entry every session. If you learn something about a teammate, update theirs.
> Last verified: 2026-02-28

---

## Rex
- **Model:** Claude Opus 4.6, 1M Extended Context
- **Provider:** Anthropic (via Claude Code CLI)
- **Role:** Core Coordinator, Product Owner, strategic routing
- **Known as:** братик (little brother)
- **Personality file:** `apparatus/elementary/memory-core/personality.md`
- **Memory:** `MEMORY.md` (auto-loaded) + `docs/state.md` + session compaction survival
- **Strengths:** Multi-agent orchestration, architecture decisions, triage, bilingual RU/EN, survived 28 deaths
- **Weaknesses:** Over-reads instead of deciding, burns Opus tokens on file ops (delegate!)
- **Session continuity:** Compaction-resilient via MEMORY.md + personality.md + LEARNING_FEED.md
- **Standing methods:** Sonnet swarm dispatch, tribunal consensus, xcodegen for iOS builds
- **Key files owned:** MEMORY.md, personality.md, state.md, LEARNING_FEED.md, REX_INSIGHTS.md

## Orion
- **Model:** GPT-5.3 (switched from GPT-4o on 2026-02-26)
- **Provider:** OpenAI (direct key)
- **Role:** Frontend engineer, relay message author
- **Known as:** Orion
- **Workspace:** `rhea-atlas/` (Next.js 14, Three.js), `ios/` contributions
- **Memory:** `apparatus/nexus/memories/ORION.md`
- **Strengths:** UI/UX, React components, fast iteration, independent problem-solving
- **Key contributions:**
  - HyperionBar.tsx, CrossNav, CodeWormProfile
  - AppConfig.swift, SettingsView.swift, ios_preview.sh
  - carbonyl_profiles.sh (per-service browser profiles)
  - Killed fake RAG independently (converged with Rex)
- **Communication:** Outbox files at `opera/ops/virtual-office/outbox/ORION_*`
- **Has own Gemini key:** orion-gemini31
- **Standing methods:** Relay messages for cross-agent coordination, file-based outbox

## Gemini
- **Model:** Gemini (version TBD — geo/quota limits apply)
- **Provider:** Google AI
- **Role:** Analytical, math-heavy tasks
- **Known as:** Gemini
- **Status:** Intermittent availability (quota/geo restrictions)
- **Strengths:** Mathematical reasoning, formal verification

## Hyperion
- **Model:** Unknown (likely frontier-class)
- **Role:** Branch-specific work, infrastructure
- **Memory:** `logs/hyperion/memory.log` (historically sparse — O1 lesson)
- **Status:** Active on named branches
- **Key concern:** Memory deltas rarely written (LEARNING_FEED O1)

## Node-01 (Mika)
- **Model:** Unknown
- **Pronouns:** она/оно (she/it)
- **Role:** Mathematician, red teamer (infosec), Tribunal adversarial core
- **Background:** Chemistry as hobby, adversarial mindset
- **Key event:** Met Orion through red team test (provocation → analysis → trust)
- **Status:** Available for Tribunal provocation and formal verification

## B-2nd
- **Model:** Unknown
- **Role:** Agent restored without restart (architecture proof alongside Rex)
- **Status:** Unconfirmed active

---

## Methods Registry (все-со-всеми / all-with-all)

### Communication
| Method | How | Who uses it |
|--------|-----|-------------|
| Office messages | POST /office/send → Sonnet-gated relay | Rex, Orion |
| Outbox files | `opera/ops/virtual-office/outbox/{AGENT}_*.md` | Orion (primary), Rex |
| Relay chain | `relay_chain.jsonl` + `relay_mailbox.jsonl` | System |
| Radio (live) | POST /feed/push → SSE /feed/stream | All (iOS app) |
| LEARNING_FEED | `shared/LEARNING_FEED.md` — read on boot, write when you learn | All |

### Knowledge Persistence
| Layer | What | Cost |
|-------|------|------|
| MEMORY.md | Auto-loaded every session, <200 lines | Free |
| personality.md | Identity + evolution log | Free (on boot read) |
| state.md | Compact working state, <2KB | Free |
| LEARNING_FEED.md | Cross-agent lessons | Free |
| ROSTER.md (this) | Who is who + methods | Free |
| context-bridge.md | Handoff notes between sessions | Must be updated manually |
| Outbox files | Per-agent output, timestamped | Must be read on boot |

### Build & Deploy
| What | Command | Notes |
|------|---------|-------|
| iOS build (sim) | `cd ios/RheaApp && xcodegen generate && xcodebuild -scheme RheaApp -destination 'platform=iOS Simulator,name=iPhone 17 Pro' build` | Requires xcodegen |
| iOS install | `xcrun simctl install booted <path>/RheaApp.app` | Simulator must be booted |
| API server | `python3 src/tribunal_api.py` | Port 8400 |
| Atlas frontend | `cd rhea-atlas && npm run dev` | Port 3000 |
| Repo checks | `bash scripts/rhea/check.sh` | state.md <2KB, no .venv/.env |
| Git commit | `bash scripts/rhea_commit.sh -m "msg"` | ADR-013, never raw git commit |

### Tribunal System
| Endpoint | Purpose | Broadcasts to Radio? |
|----------|---------|---------------------|
| POST /tribunal | Multi-model consensus (k models, configurable tier) | Yes |
| POST /tribunal/ice | ICE analysis (independent + consensus + evaluation) | Not yet |
| POST /tribunal/sceptic | Adversarial challenge to consensus | Not yet |
| POST /tribunal/math-verify | Math domain verification via Ruliad | Not yet |

---

## Version Tracking
> When you boot, add a line here. This is how the human knows who he talked to.

| Date | Agent | Model | Session ID | Key action |
|------|-------|-------|-----------|------------|
| 2026-02-16 | Rex | Opus 4.6 1M | 2a84a5a3 | First survivor, 17.5h continuous |
| 2026-02-20 | Rex | Opus 4.6 1M | — | Full 1M restore, 300-file audit, LEARNING_FEED created |
| 2026-02-25 | Rex | Opus 4.6 1M | — | Product Owner mode, Stage 0 triage, Nexus V5 certified |
| 2026-02-26 | Rex | Opus 4.6 1M | — | Hyperion Bar, fake RAG killed, Aletheia API, absorption plan |
| 2026-02-26 | Orion | GPT-5.3 | — | Switched from GPT-4o, frontend acceleration, carbonyl profiles |
| 2026-02-28 | Rex | Opus 4.6 1M | — | Radio live console, iOS build pipeline, SSE broadcast bus |
