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
- Scientific foundation — polyvagal theory, HRV, interoception, ADHD-first
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
- **ADHD-first design** — all UX assumes executive dysfunction as default
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

Rhea's memory has accumulated 28 snapshots, 124KB of core docs, 510KB of chat extracts,
and 9 sessions of thinking history. The discomfort function D = 91.96 (comfort zone, T1=150).

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

## Working Languages
EN (primary docs) · RU (protocol, dialogue) · FR (future localization)

## Refs
- Compact state: docs/state.md
- Architecture: docs/architecture.md
- Decisions: docs/decisions.md (7 ADRs)
- Roadmap: docs/ROADMAP.md
- MVP loop: docs/MVP_LOOP.md
- Paper outline: docs/prism_paper_outline.md
- Model catalog: docs/models_catalog.md | .json
