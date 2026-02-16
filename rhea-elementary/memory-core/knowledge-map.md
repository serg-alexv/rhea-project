# Rhea Knowledge Map

> Generated: 2026-02-16 | Source: /Users/sa/rh.1/docs/ (25 files, ~136 KB total)

---

## CORE_RULES.md
- **Path:** docs/CORE_RULES.md
- **Size:** 4,836 bytes
- **Purpose:** Compact operating procedure defining Rhea's autonomy-with-audit governance model derived from the root prompt.
- **Key content:**
  - 5 hard constraints (HC-1..HC-5): no silent power, no "done" without verification, no self-merge outside safe zone, mandatory checkpoints, budget-aware routing
  - Mathematical control layer with state vector x_t = [Progress, Risk, Debt, Evidence, MemoryLoad, Budget] and complexity trigger thresholds T1/T2
  - Checkpoint policy (micro/task/consolidation levels), tribunal rules, 7 self-upgrade clusters to evaluate, and Phase 1 definition of done

## INTEGRATIONS_AUDIT.md
- **Path:** docs/INTEGRATIONS_AUDIT.md
- **Size:** 21,959 bytes
- **Purpose:** Full registry of all tools, integrations, and services used by the Rhea project with liveness status.
- **Key content:**
  - 93 total integrations across 5 layers: Claude Code plugins/skills (40+), MCP servers (18), rhea_bridge.py providers (6), local scripts (13), hooks/lifecycle (7)
  - 86 passing, 0 failing, 7 untested (Clinical Trials, Open Targets, Synapse.org, Learning Commons, Hugging Face, Scholar Gateway, Vibe Prospecting)
  - 4-tier cost configuration (cheap/balanced/expensive/reasoning) all operational

## MVP_LOOP.md
- **Path:** docs/MVP_LOOP.md
- **Size:** 1,086 bytes
- **Purpose:** Draft specification for Rhea's closed-loop scheduler MVP defining the minimal control system.
- **Key content:**
  - State vector: sleep_proxy, energy (1-5), time_budget, friction
  - Action set: micro-interventions (2-5 min), tasks (10-60 min), recovery actions
  - Safety constraints: minimum viable day (anti-spiral), context switch limits, recovery floor when sleep is low

## NOW.md
- **Path:** docs/NOW.md
- **Size:** 5,707 bytes
- **Purpose:** Immediate upgrade schedule organized into 4 priority tiers with estimated effort and verification steps.
- **Key content:**
  - Tier 0 (fix broken): trim state.md under 2KB, fix memory_benchmark.sh false positives, create rhea CLI wrapper
  - Tier 1 (foundations): create .claude/agents/ subagents, produce SELF_UPGRADE_OPTIONS.md, TODO_MAIN.md, CORE_MEMORY.md
  - Tier 2-3 (tooling + hardening): test 7 untested MCP servers, wire Playwright, define auto-tribunal triggers, auto-PR generation

## ROADMAP.md
- **Path:** docs/ROADMAP.md
- **Size:** 429 bytes
- **Purpose:** High-level 4-stage roadmap from spec to iOS MVP to passive signals to MPC optimization.
- **Key content:**
  - Stage 0: specs + controller skeleton (finalize MVP_LOOP, log schema, Python simulation)
  - Stage 1: iOS MVP with SwiftUI shell, 10-second check-in, local persistence
  - Stage 2-3: HealthKit/Watch passive signals, then MPC replanning under uncertainty with safe defaults

## TOKEN_OPTIMIZATION.md
- **Path:** docs/TOKEN_OPTIMIZATION.md
- **Size:** 7,706 bytes
- **Purpose:** Strategy document for minimizing token spending while maximizing persistent context across sessions.
- **Key content:**
  - 5-layer optimization: Bonsai free models, Mintlify AI-indexed docs with llms.txt, Entire.io cross-session memory fixes, MEMORY.md auto-memory population, CLAUDE.md optimization
  - Cost model: current ~$0.50/session, target $0.00/session with full optimization (Bonsai + lazy loading)
  - Identified waste: 510KB chat_extracts.json unused, 45 snapshots written but never read, empty auto-memory directory

## api_contracts.md
- **Path:** docs/api_contracts.md
- **Size:** 2,293 bytes
- **Purpose:** Interface definitions between Rhea components (bridge, state, metrics, eval, PWA) with no implementation yet.
- **Key content:**
  - Bridge API: ask_default(prompt), ask_tier(prompt, tier), tribunal(prompt, models, n) returning consensus + agreement_score
  - State API (future LangGraph): GET /state returning RheaState vector, POST /action for agent processing
  - PWA-to-backend contract: dashboard reads metrics JSON, episode explorer reads snapshots, agent graph from LangGraph export

## architecture.md
- **Path:** docs/architecture.md
- **Size:** 3,170 bytes
- **Purpose:** High-level architecture of Rhea as an iOS app that reconstructs daily defaults using chronobiology and multi-model AI.
- **Key content:**
  - Scientific foundation: polyvagal theory, HRV, interoception, circadian anchoring (Hadza/San/Tsimane), cultural universals across 16+ civilizations
  - 8-agent Chronos Protocol v3 with model assignment logic (Opus for reasoning, Sonnet for execution)
  - Multi-model bridge: 6 providers, 400+ models; data architecture with passive profiling, Azure Cosmos DB, and Bayesian/Fourier personalization

## article_gpt_pro_vs_cowork.md
- **Path:** docs/article_gpt_pro_vs_cowork.md
- **Size:** 8,901 bytes
- **Purpose:** Comparative analysis article evaluating ChatGPT Pro ($200/mo) vs Claude Cowork for AI-powered productivity.
- **Key content:**
  - ChatGPT Pro wins for pure reasoning (o1 Pro); Claude Cowork wins for automation, file handling, and tool orchestration via MCP
  - For Rhea: multi-provider abstraction (rhea_bridge.py) is strategically superior to either single vendor
  - Recommendations by user type: researchers get ChatGPT Pro, knowledge workers get Claude Max 5x, startups get Claude Pro + multi-provider bridge

## core_context.md
- **Path:** docs/core_context.md
- **Size:** 13,526 bytes
- **Purpose:** Deep intellectual genesis of the Rhea project, preserving the full chain of reasoning from origin conversations.
- **Key content:**
  - 11-step intellectual chain from Gregorian calendar critique through symbolic power, hunter-gatherer calibration zero, polyvagal theory + ADHD, to agent teams and iOS app
  - 8-level symbolic power framework (time naming, cosmic legitimacy, linguistic control, category formation, habitual infrastructure, hegemonic consent, preference shaping, doxa)
  - Full 8-agent system definitions with model assignments, multi-model bridge provider table, and 9 unimplemented research domains (breathing, movement, thermal, narrative identity, etc.)

## cost_guide.md
- **Path:** docs/cost_guide.md
- **Size:** 3,035 bytes
- **Purpose:** Budget architecture targeting $0.05/day (~$1.50/month) for AI-powered daily optimization.
- **Key content:**
  - Tier routing: cheap tier handles ~80% of calls at $0.001-0.005/1K tokens; reasoning tier at ~1% of calls
  - Daily budget breakdown: $0.033 subtotal + 50% buffer = $0.033; weekly tribunal adds $0.02/day amortized
  - Cost discipline rules: default cheap, log every escalation, free tiers first, batch operations, cache responses

## decisions.md
- **Path:** docs/decisions.md
- **Size:** 10,648 bytes
- **Purpose:** Architecture Decision Record (ADR) log containing all 14 formal decisions made during Rhea development.
- **Key content:**
  - 14 ADRs covering agent consolidation, multi-model bridge, ADHD design, model tier routing, memory budget, self-evaluation techniques, and commit strategies
  - ADR-014 (latest) reversed ADR-012: switched from manual-commit to auto-commit with per-query memory persistence
  - Key dependency chain: ADR-007 (three-tier memory) -> ADR-008 (tiered routing) -> ADR-009 (agent tier integration) -> ADR-010 (memory budget + discomfort metric)

## langgraph_architecture.md
- **Path:** docs/langgraph_architecture.md
- **Size:** 6,665 bytes
- **Purpose:** Design document (no code yet) for Rhea's LangGraph-based state machine with 9 agent nodes and 6 meta nodes.
- **Key content:**
  - RheaState TypedDict: energy, mood, cognitive_load, sleep_debt, obligations, recovery, discomfort_level, current_D
  - Graph flow: START -> router -> {chronos, gaia, hypnos, athena, hermes, hephaestus, apollo} -> hestia (safety) -> checkpoint -> metrics_check
  - Dual checkpoint system: LangGraph native (ephemeral, session-scoped) + Entire.io (persistent, repo-scoped)

## prism_paper_outline.md
- **Path:** docs/prism_paper_outline.md
- **Size:** 4,739 bytes
- **Purpose:** 8-section outline for the "Mathematics of Rhea" scientific paper targeting OpenAI Prism generation.
- **Key content:**
  - Mathematical framework: state space (sleep_proxy, energy, time_budget, friction, vagal_state), Fourier decomposition of biorhythms, Bayesian duration model, MPC optimal control
  - Cross-cultural validation using 16+ civilizations and 40+ calendar systems as natural experiments
  - Evaluation plan: simulated user cohort, ADHD vs neurotypical comparison, ablation studies

## reflection_log.md
- **Path:** docs/reflection_log.md
- **Size:** 4,255 bytes
- **Purpose:** Failure memory log recording root causes and fixes for past mistakes (ADR-011 technique #5).
- **Key content:**
  - 5 entries: auto-commit trailer misconception, commit-msg hook permissions, stale metrics in memory_metrics.json, VM macOS tool boundary, Cowork bypassing Entire.io session lifecycle
  - Pattern: most failures stem from cross-environment assumptions (VM vs macOS, Claude Code vs Cowork)
  - Each entry has: what happened, root cause, fix, and lesson learned

## soul.md
- **Path:** docs/soul.md
- **Size:** 2,724 bytes
- **Purpose:** Base human configuration prompt layer inherited by every agent before applying domain-specific deltas.
- **Key content:**
  - User profile: ADHD (executive dysfunction as baseline), anankastic compensatory architecture, RU/EN bilingual
  - 7 principles: ADHD-optimized, hunter-gatherer calibration zero, structure that feels like freedom, depth from removing excess, no micromanagement, polyvagal awareness, multi-temporal awareness
  - State vector: x_t = [E_t (energy), M_t (mood), C_t (cognitive load), S_t (sleep debt), O_t (obligations), R_t (recovery)]

## state.md
- **Path:** docs/state.md
- **Size:** 1,249 bytes
- **Purpose:** Compact working state loaded at every session start (must stay under 2,048 bytes, enforced by check.sh).
- **Key content:**
  - Mission: Mind Blueprint factory with 3-product architecture (Rhea Core, iOS App, Commander)
  - Current status: v3 architecture, 8 agents, bridge live with 6 providers, 14 ADRs, 2 tribunals, D=63.4 (comfort)
  - Next steps: install Entire GitHub App, define minimal user loop, iOS MVP (SwiftUI + HealthKit, ONE agent, ONE intervention)

## state_agents_core.md
- **Path:** docs/state_agents_core.md
- **Size:** 8,199 bytes
- **Purpose:** Complete agent definitions for all 9 Rhea agents with mythic roles, scientific domains, tier policies, and prompt modifiers.
- **Key content:**
  - 9 agents: Rhea (root manager), Chronos (time), Gaia (body), Hypnos (sleep), Athena (strategy), Hermes (communication), Hephaestus (build), Hestia (safety), Apollo (insight)
  - Tier policy table: 5 agents cheap-only (Chronos, Hypnos, Hermes, Hestia, + Rhea default), 2 agents balanced->expensive (Athena, Hephaestus), 1 agent cheap->reasoning (Apollo)
  - Each agent has a modifier prompt appended on top of soul.md with cost discipline instructions

## state_full.md
- **Path:** docs/state_full.md
- **Size:** 9,810 bytes
- **Purpose:** Append-only narrative log of project evolution with session-by-session changelog and status.
- **Key content:**
  - Full mission statement: "Reconstructing Daily/Circabidian/Ultradian/Infradian Defaults Using the Evidence-Based Cumulative Knowledge of Human Civilizations"
  - Session logs: Opus bridge + docs, Entire.io checkpoint pipeline fix, memory benchmark + self-upgrade phase
  - Technical debt tracked: bridge uses synchronous requests, tribunal consensus is count-based, no retry/rate limiting, HuggingFace API mismatch

## tribunal_001_autocommit.md
- **Path:** docs/tribunal_001_autocommit.md
- **Size:** 6,700 bytes
- **Purpose:** First tribunal record evaluating whether to switch Entire.io from manual-commit to auto-commit strategy.
- **Key content:**
  - 3 perspectives: Advocate (richer continuous capture), Skeptic (trailers + clean git history), Pragmatist (hybrid manual-commit + cron snapshots)
  - Decision: keep manual-commit, defer hybrid auto-snapshots to Stage 2 (agreement score 0.85)
  - Produced ADR-012 (later superseded by ADR-014 which switched to auto-commit per user directive)

## tribunal_002_memory_architecture.md
- **Path:** docs/tribunal_002_memory_architecture.md
- **Size:** 4,339 bytes
- **Purpose:** Second tribunal diagnosing why Entire.io checkpoints stopped appearing after the first 2 commits.
- **Key content:**
  - Root cause: Cowork commits via osascript bypass Entire.io session lifecycle (no session-start -> no trailers -> no checkpoints)
  - 3 models queried (GPT-4o-mini, Gemini-2.0-flash, Gemini-2.0-flash-lite), unanimous consensus (0.95 agreement): create wrapper script
  - Produced ADR-013: scripts/rhea_commit.sh wrapping git commit with explicit Entire.io hook calls

## ui_pwa_vision.md
- **Path:** docs/ui_pwa_vision.md
- **Size:** 1,888 bytes
- **Purpose:** Future React PWA design vision deferred until core memory model is stable.
- **Key content:**
  - 5 planned views: dashboard (state vector gauges), episode explorer (snapshot timeline), agent graph visualizer, schedule view (MPC + circadian overlay), task/roadmap
  - Tech stack: React 18+ TypeScript, Tailwind CSS, Vite, deployed as PWA with service worker
  - Priority rule: do NOT build until core memory stable, LangGraph Phase 2 done, first live tribunal complete, and iOS MVP exists

## upgrade_plan_suggestions.md
- **Path:** docs/upgrade_plan_suggestions.md
- **Size:** 9,056 bytes
- **Purpose:** Session 17 tribunal output with prioritized warnings, solutions, and next-step recommendations (unapproved draft).
- **Key content:**
  - 7 warnings: W1 (CRITICAL) no product-market fit validation after 17 sessions, W2 (CRITICAL) zero iOS implementation, W3 (HIGH) polyvagal theory contested, W4-W7 covering premature multi-agent optimization, no validated interventions, data privacy gap, ADHD not operationally defined
  - Recommended next 4 sessions: user research + wireframe, iOS MVP core, beta + measurement, soft launch
  - Intellectual chain integrity recheck: first 3 links solid, links 4-6 are research frontier (speculative but plausible)

## user_examples.md
- **Path:** docs/user_examples.md
- **Size:** 2,705 bytes
- **Purpose:** Concrete usage examples showing how Rhea works in practice for end users and developers.
- **Key content:**
  - Morning routine generation with body-first approach aligned to ultradian rhythms
  - Tribunal decision example: meditation question answered by 3 models with consensus (reframed as "breathing exercise," conditional on sleep)
  - Memory benchmark output example, discomfort check alert, and external oracle query flow (ATLAS_QUERY)

## user_guide.md
- **Path:** docs/user_guide.md
- **Size:** 8,894 bytes
- **Purpose:** Comprehensive user-facing guide covering setup, agent system, memory architecture, bridge capabilities, and self-improvement mechanisms.
- **Key content:**
  - 6-layer memory architecture: compact state, full state, episodic (Entire.io), local snapshots, decision log (ADRs), failure memory (reflection_log)
  - Bridge usage: status, ask, tribunal, models CLI commands; tiered routing explanation
  - 6 evolution capabilities: reflexion loop, tribunal/debate, tool-verification, eval sets, failure memory, teacher-student distillation

---

## ADR Summary (14 decisions from decisions.md)

1. **ADR-001** -- Consolidated agents from 10 to 8 by merging overlapping scientific roles.
2. **ADR-002** -- Chose multi-model bridge (6 providers, 400+ models) over single-provider lock-in for cost and diversity.
3. **ADR-003** -- ADHD-optimized design: all UX assumes executive dysfunction as default, passive profiling, no questionnaires.
4. **ADR-004** -- Opus 4 for reasoning agents (1,2,4,8), Sonnet 4 for execution agents (3,5,6,7).
5. **ADR-005** -- Passive profiling using behavioral signals (sleep, movement, HRV) instead of self-report questionnaires.
6. **ADR-006** -- Hunter-gatherer calibration zero: Hadza/San/Tsimane daily patterns as universal baseline for optimal defaults.
7. **ADR-007** -- Three-tier external memory: GitHub (state.md <=2KB), Entire.io (episodic), compact protocol for session handoff.
8. **ADR-008** -- Tiered model routing with cheap-first default (4 tiers: cheap/balanced/expensive/reasoning).
9. **ADR-009** -- Agent tier integration: each agent gets a declared default tier and escalation tier with logged justification.
10. **ADR-010** -- Memory budget with discomfort function D, thresholds T1(150)/T2(300), Reflexive Sprints, and 5 memory zones.
11. **ADR-011** -- Six self-improvement techniques: Reflexion, tribunal/debate, tool-verification, eval sets, failure memory, teacher-student.
12. **ADR-012** -- Keep manual-commit for Entire.io, defer hybrid auto-snapshots to Stage 2 (later superseded by ADR-014).
13. **ADR-013** -- Wrapper script (rhea_commit.sh) to fix Cowork commits bypassing Entire.io session lifecycle.
14. **ADR-014** -- Per-query memory persistence + switch to auto-commit (reverses ADR-012), every interaction leaves a trace.

---

## Tribunal Summary (2 completed tribunals)

### Tribunal 001: Should Rhea Enable Entire.io Auto-Commit Mode?
Three perspectives debated (Advocate, Skeptic, Pragmatist). Decision: keep manual-commit, defer hybrid auto-snapshots to Stage 2. Agreement score 0.85. Advocate rejected 2-1; pragmatist hybrid approach accepted 3-0 as compromise. Produced ADR-012 (later superseded by ADR-014 per user directive).

### Tribunal 002: Fix Entire.io Checkpoint Gap
Root cause identified: Cowork commits via osascript bypass Entire.io session lifecycle, producing zero checkpoints for 4+ commits. Three cheap-tier models (GPT-4o-mini, Gemini-2.0-flash, Gemini-2.0-flash-lite) unanimously recommended a wrapper script. Agreement score 0.95 (strongest consensus in any Rhea tribunal). Produced ADR-013: scripts/rhea_commit.sh.

---

## Cross-References

| Theme | Primary Doc | Supporting Docs |
|-------|-------------|-----------------|
| Governance | CORE_RULES.md | decisions.md, soul.md |
| Architecture | architecture.md | langgraph_architecture.md, state_agents_core.md, api_contracts.md |
| Memory | state.md, state_full.md | TOKEN_OPTIMIZATION.md, reflection_log.md |
| Science | core_context.md | prism_paper_outline.md, MVP_LOOP.md |
| Operations | INTEGRATIONS_AUDIT.md | NOW.md, cost_guide.md, user_guide.md |
| Product | upgrade_plan_suggestions.md | ROADMAP.md, ui_pwa_vision.md, user_examples.md |
| Decisions | decisions.md | tribunal_001_autocommit.md, tribunal_002_memory_architecture.md |
| External | article_gpt_pro_vs_cowork.md | -- |
