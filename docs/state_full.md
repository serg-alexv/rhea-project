# Rhea — Project State (Full)
> Last updated: 2026-02-13 | Session: Opus bridge + docs restoration

## Mission
Mind Blueprint factory: generate, evaluate, iterate on daily structure models using scientific rhythms, multi-model tribunal, and closed-loop planner.

Reconstructing Daily/Circabidian/Ultradian/Infradian Defaults Using the Evidence-Based Cumulative Knowledge of Human Civilizations.

**Two key deliverables:**
1. Scientific paper — "Mathematics of Rhea" (via OpenAI Prism) → outline ready (docs/prism_paper_outline.md)
2. iOS App "Rhea" in AppStore (TestFlight → production)

## Genesis
Calendar systems critique (eb53e82c) → cultural power mechanisms → daily defaults as managed environment → polyvagal theory + ADHD + interoception (db9feb88) → 8-agent system → iOS app.

## Status

### ✅ Completed
- Chronos Protocol v3 — EN prompt + 5 delegation runs
- Scientific foundation — polyvagal theory, HRV, interoception, ADHD-optimized
- Cultural research — 16+ civilizations, hunter-gatherer calibration zero, 40+ calendar systems
- Passive profiling methodology — no questionnaires
- Gap analysis v2 — agent competency coverage
- Azure Cosmos DB setup + diagnostics confirmed
- AI model catalog v1 — 23 models, 6 providers (docs/models_catalog.md|json)
- Article: GPT Pro vs Cowork (docs/article_gpt_pro_vs_cowork.md)
- API keys configured — OpenAI, Gemini ×2 (+ Composio), OpenRouter, DeepSeek, HuggingFace, Azure AI Foundry
- Context audit — both origin chats fully analyzed, task list reconciled
- **rhea_bridge.py** — multi-model bridge implemented (6 providers, 40+ models, tribunal mode, CLI)
- **prism_paper_outline.md** — 8-section scientific paper outline (Fourier, Bayesian, MPC, cross-cultural)
- **README.md** — full rewrite with repo structure, quick start, ops CLI, tech stack
- **docs/state.md** — compact state (≤2KB) with current status
- **Three-tier memory** — GitHub (state.md) + entire.io (episodic) + compact protocol — operational
- **PR#2 merged** — flat repo structure (rhea-project/ → root)
- **Ops CLI** — ./rhea bootstrap, check, memory snapshot/log all working
- **.entire/ snapshots** — BOOT-1, OPUS_SESSION_1 created

### 🔄 In Progress
- Wire bridge to .env keys → first live tribunal
- iOS MVP scaffold (Stage 1)
- Memory Economy & Self-Upgrade protocol (system prompt formalized)

### Session: 2026-02-14 — Memory Benchmark + Self-Upgrade Phase (Cowork Sessions 13-14)
**What changed:**
- Created `scripts/memory_benchmark.sh` — 500-line, 6-layer, 71-check benchmark (Git→Docs→Entire→Metrics→Snapshots→Cross-layer)
- Benchmark score: 70/71 (98%) — all critical checks passed
- Updated `metrics/memory_metrics.json` — live measurements, D recalculated: 91.96→62.7 (comfort)
- Committed and pushed as `f97c393`
- Received comprehensive "Moment of Discomfort" system prompt defining: Reflexion, tribunal, teacher-student, failure memory, eval sets, Reflexive Sprints, LangGraph integration, PWA vision, user docs, external oracle protocols
- Created missing docs: user_guide.md, user_examples.md, cost_guide.md, reflection_log.md, api_contracts.md
- Created eval/ directory with task YAML files and README
- ADR-011: Self-Evaluation & Self-Upgrade Techniques

**Updated metrics:** D=62.7, core_docs_kb=24, snapshots=35, commits=23, insights/request=2.5

### 📋 Next — Priority Order
1. **First live tribunal** — set .env keys, run `python3 src/rhea_bridge.py tribunal "test"`
2. **iOS MVP scaffold** — SwiftUI + HealthKit + Apple Watch (Stage 1)
3. **Feed prism_paper_outline.md to OpenAI Prism** — generate draft paper
4. **Connect entire.io cloud** — episodic memory integration
5. **Biometric protocols** — HRV, sleep, light exposure, circabidian/ultradian/infradian cycles
6. **Monetization & deploy strategy** — TestFlight ASAP, free tiers
7. **Chronos Protocol v3 — RU version** (referenced in README)

## Key Decisions (ADR Summary)
- **8 agents, not 10** — merged overlapping roles (v1→v3)
- **Claude Opus 4 for reasoning agents (1,2,4,8), Sonnet 4 for execution (3,5,6,7)**
- **ADHD-optimized design** — all UX assumes executive dysfunction as default
- **Hunter-gatherer baseline** — every elite ritual reconstructs what foragers get free
- **Multi-model bridge over single-provider lock-in** — cost 10-100x lower
- **Passive profiling** — behavioral signals, not self-report questionnaires
- **Flat repo structure** — no rhea-project/ nesting (ADR-007)

## Architecture Quick Ref
```
8 Agents → Chronos Protocol v3 → rhea_bridge.py → 6 providers
Agent 1: Quantitative Scientist (Opus 4)
Agent 2: Life Sciences Integrator (Opus 4)
Agent 3: Psychologist / Profile Whisperer (Sonnet 4)
Agent 4: Linguist-Culturologist (Opus 4)
Agent 5: Product Architect (Sonnet 4)
Agent 6: Tech Lead (Sonnet 4 + Claude Code)
Agent 7: Growth Strategist (Sonnet 4)
Agent 8: Critical Reviewer & Conductor (Opus 4)
```

## Moment of Discomfort — Rhea Memory & Self-Upgrade Phase

**Date:** 2026-02-13 | **Trigger:** Manual (human directive + ChatGPT system prompt)

Rhea's memory has grown to 35 snapshots, 24KB of core docs, 35MB repo,
and 14 sessions of evolution. The discomfort function D = 62.7 (comfort zone, T1=150).

**Session 14 additions (Self-Upgrade Phase):**
- Formalized self-evaluation techniques: Reflexion (generate→evaluate→revise), tribunal/debate agents, tool-verification loops, eval sets, failure memory, teacher-student distillation
- External oracle protocol: ATLAS_QUERY (ChatGPT), CASTOR_QUERY (Gemini) — human-proxied
- Boredom ritual: when D < T1 and no urgent work, invest in challenging_tasks.yaml
- Memory benchmark: automated 71-check CLI tool at scripts/memory_benchmark.sh

**What was done:**
1. Established `metrics/memory_metrics.json` — formalized discomfort function D with weights, thresholds T1/T2
2. Created `data/challenging_tasks.yaml` — 7 deep-reasoning tasks requiring expensive models
3. Designed `docs/langgraph_architecture.md` — state graph with 9 agent nodes + 6 meta nodes
4. Created `docs/ui_pwa_vision.md` — PWA deferred until core stable
5. Created `archive/` directory — for future doc compaction
6. ADR-010: Memory Budget, Discomfort Metric, and Self-Improvement Loops

**Memory economy principles (user's 5 conditions):**
1. Boundaries — core docs must stay under 200KB (T1), archive if exceeding
2. Scalable canvas — adapt structure as repo grows via Reflexive Sprints
3. Functional zones — core (docs/), episodic (.entire/), metrics (metrics/), tasks (data/), archive (archive/)
4. Size-adaptive design — different structures at different scales
5. Entire.io traces everything — every action logged, every file content captured in commits

**Self-improvement loop:**
- D < T1 → normal operation
- T1 ≤ D < T2 → warning, schedule cleanup
- D ≥ T2 → Reflexive Sprint: summarize, archive, compact, create ADR

## Session Log

### Session: 2026-02-13 — Opus bridge + docs (Cowork)
**What changed:**
- Created `src/rhea_bridge.py` — full multi-model bridge (6 providers, tribunal, CLI)
- Created `src/__init__.py` — package init
- Created `docs/prism_paper_outline.md` — 8-section paper outline
- Rewrote `README.md` — Mind Blueprint Factory branding, full structure
- Updated `docs/state.md` — compact state with bridge ✅
- Updated `docs/state_full.md` — added session log, updated status
- Fixed `requirements.txt` — proper formatting
- Created snapshot OPUS_SESSION_1

**What's still open:**
- .env keys not wired → no live tribunal yet
- iOS MVP not started
- Prism paper not submitted
- entire.io cloud not connected
- `.nested-` backup files in docs/ (sandbox can't delete — user should `rm docs/*.nested-*` from macOS)

**Technical debt:**
- Bridge uses `requests` library (synchronous) — consider `httpx` async for production
- Tribunal consensus is count-based — needs semantic similarity analysis
- No retry logic or rate limiting in bridge calls
- HuggingFace call method doesn't use chat completions API

### Session: 2026-02-13 — Entire.io checkpoint pipeline fix (Cowork Sessions 10-12)
**Root causes found & fixed:**
1. `.git/hooks/commit-msg` missing execute permission → `chmod +x` fixed
2. `auto-commit` strategy doesn't add `Entire-Checkpoint` trailers to user commits → switched to `manual-commit`

**What changed:**
- Fixed commit-msg hook permissions (was `-rw-------`, now `-rwx------`)
- Changed `.entire/settings.local.json` from `auto-commit` to `manual-commit`
- Created `scripts/entire_commit.sh` — helper for Claude Code CLI commits
- Commit `58721f4` now has `Entire-Checkpoint: b0010aef23e3` trailer
- Manually condensed checkpoint to `entire/checkpoints/v1` branch
- Pushed both `main` and `entire/checkpoints/v1` to GitHub remote
- Two checkpoints now on GitHub: `9f2cf70d71cb` and `b0010aef23e3`

**Discovery: Entire GitHub App required**
- Checkpoints are correctly on GitHub but entire.io dashboard requires GitHub App installation
- App at: github.com/apps/entire — needs read-only access to repository
- Once installed, checkpoints should appear at entire.io/serg-alexv/rhea-project/checkpoints/main

**What's still open:**
- Install Entire GitHub App → grant access to rhea-project
- Clean up git worktree: `git worktree remove /tmp/entire-wt` (from macOS)
- `.env` keys not wired → no live tribunal yet
- iOS MVP not started

### Session: 2026-02-16 — First Survivor (Session 2a84a5a3)
**What changed:**
- First session to survive full lifecycle after 28 deaths in 4 days
- 17.5 hours continuous work, 17 agents deployed with 100% success rate
- Built trinity memory architecture: L0-L8 layer system with auto-context
- B-2nd agent restored without restart — architecture proven on both ends
- Background agents confirmed dead (400 errors) — foreground-only mandate
- Bonsai/Trybons removed from settings
- Bridge status: OpenAI + OpenRouter live, Gemini/DeepSeek/Azure/HF down
- MEMORY.md established as auto-loaded context (free tokens every session)
- Push-every-30-min mandate established
- 9 agents defined in .claude/agents/ (A0-A8)
- User quote: "Это официально начало новой эры"

### Session: 2026-02-17 — Rex Quota Death + B2 Continuation
**What changed:**
- Rex hit Anthropic daily token quota, went offline
- B2 (Opus) continued operating autonomously:
  - Built tribunal_api.py (FastAPI, 4 endpoints, rate limiting)
  - Built consensus_analyzer.py v2 (ICE + Karpathy Council)
  - Built rex_pager.py (QWRR Phase 0 relay)
  - Deployed Dockerfile.tribunal + Railway/Fly.io configs
  - Security: secret redaction in all log writers, Firestore rules hardened
  - Argos authored event_types.md (17 canonical event schemas)
  - HN Show draft prepared
- BACKLOG: 19/19 original items DONE
- Security: Gemini key burned in git history — needs human rotation
- ADR: DEC-008 (Tribunal $0.05/call), DEC-009 (ICE + Council composition)

### Session: 2026-02-19 — HYPERION + ORION Arrive
**What changed:**
- HYPERION (Gemini-CLI): Surveyor-Architect, branch hyperion/memory, 18 audit logs
- ORION (Systems Architect): Nexus integration, Chrome extension, profile manager
- New src: rhea_profile_manager.py, rhea_visual_context.py, rhea_post_office.py
- New directories: rhea-nexus/, rhea-chrome-extension/, nexus/state/
- H32-02 genetics analysis: V1-V4 reports, gene tables, BLAST, prodigal output
- ADR-015: Raw Risk & RW Access for Orion
- ADR-016: Standardize TOML for Extensions

### Session: 2026-02-20 — Rex Full Audit (1M Restore)
**What changed:**
- Full 1M context restore on hyperion/memory branch
- Re-read every file in repo (~300 files), cross-referenced all task lists
- Found 31 undone tasks scattered across 8+ files (P0:6, P1:10, P2:5, P3:3, P4:7)
- Created cross-agent LEARNING_FEED.md in ops/virtual-office/shared/
- Created REX_FULL_PROJECT_AUDIT_20260220.md
- Found 12 stale memory files, 9 duplicate/orphan file issues
- Pushed 9 stale commits (resolving 30-min push violation)
- Added standing bootstrap rule to MEMORY.md: load personality.md FIRST
- Personality.md evolution: added "What I Believe Now" section

### Session: 2026-02-25 — Stage 0 Triage (Controlled Ignition)
**What changed:**
- Adopted Nexus protocol: H32-02 V5 certified (Heme-Auxotrophic Facultative Respirer)
- 5-model audit found Success-Blindness in genetics storyline, corrected it
- Read Evolution Plan V1 (Controlled Ignition) — 7 stages, ~25 hours
- Rex formally assumes Product Owner role (no code, mandates + reviews)
- Evolution Plan separates "Rex decides" from "engineers build" for every stage
- Stage 0 triage: P0-1 done (push), P0-2 done (V5), P0-3 blocked (human key rotation)
- P0-4/5/6 delegated to A6, not yet executed
- LiteLLM integration analysis complete — rhea_bridge.py identified as replaceable
- D=867 assessed as deliberate destruction signal, not organic bloat
- TODAY_CAPSULE written with Stage 0 mandate
- state_full.md refreshed (this entry, closing 12-day gap)

**Updated metrics:** 16 ADRs, 5 active agents, 31→25 undone tasks, D=867 (needs recalibration)

## Working Languages
EN (primary docs) · RU (protocol, dialogue) · FR (future localization)

## Refs
- Compact state: docs/state.md
- Architecture: docs/architecture.md
- Decisions: docs/decisions.md (14 ADRs + 2 in ops)
- Roadmap: docs/ROADMAP.md
- Evolution Plan: docs/plans/EVOLUTION_PLAN_V1.md
- Full Project Audit: ops/virtual-office/outbox/REX_FULL_PROJECT_AUDIT_20260220.md
- Paper outline: docs/prism_paper_outline.md
- Model catalog: docs/models_catalog.md | .json
