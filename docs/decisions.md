# Rhea — Decision Log

## ADR-001: Agent consolidation 10→8 (2026-02)
**Context:** v1 had 10 agents with overlapping competencies.
**Decision:** Merge Astronomer+Physicist+Mathematician→Agent 1; Chemist+Biologist+Neuroscience→Agent 2. Add Tech Lead (A6), Growth (A7). Preserve Critical Reviewer independence.
**Rationale:** Eliminates handoff losses; body systems don't respect disciplinary boundaries.

## ADR-002: Multi-model bridge over single provider (2026-02)
**Context:** Need diverse AI perspectives; single-provider lock-in = cost and quality risk.
**Decision:** Build rhea_bridge.py with 6 providers, 400+ models, tribunal mode.
**Rationale:** 10-100x cost reduction via free tiers (Azure, DeepSeek, OpenRouter free models). Geographic diversity (US/CN/EU) reduces bias.

## ADR-003: ADHD-first design (2026-02)
**Context:** Neurotypical UX fails for executive dysfunction. ADHD users are canary in the coal mine — if it works for them, it works for everyone.
**Decision:** All UX assumes ADHD as default: minimal decision load, passive profiling, body-first morning, no questionnaires.
**Rationale:** Bruton et al. 2025 (diminished interoception in ADHD), Längle et al. 2025 (HRV/cognitive control).

## ADR-004: Claude Opus for research, Sonnet for execution (2026-02)
**Context:** Need to balance reasoning depth vs speed/cost.
**Decision:** Opus 4 for Agents 1,2,4,8 (reasoning-intensive). Sonnet 4 for Agents 3,5,6,7 (execution).
**Rationale:** Research/critique agents need long-context reasoning. Product/growth agents benefit from faster iteration.

## ADR-005: Passive profiling methodology (2026-02)
**Context:** Self-report questionnaires have known reliability issues, especially for ADHD users.
**Decision:** Use behavioral signals (sleep patterns, movement, screen time, HRV) for profile construction. Zero questionnaires in core flow.
**Rationale:** Reduces onboarding friction to near-zero; behavioral data more reliable than self-report.

## ADR-006: Hunter-gatherer calibration zero (2026-02)
**Context:** Need a universal baseline for "optimal defaults" across cultures.
**Decision:** Hadza/San/Tsimane daily patterns as reference point. Every elite ritual across 16+ civilizations independently converges on this pattern.
**Rationale:** Yetish et al. 2015, Wiessner 2014. The nervous system is one; culture-specific rituals are approximations of the same underlying biology.

## ADR-007: Three-tier external memory (2026-02-13)
**Context:** Claude's context window = RAM. 27 transcripts, 70% context spent on "remembering."
**Decision:** GitHub (state.md ≤2KB) as long-term memory, entire.io as episodic memory, compact protocol for session handoff.
**Rationale:** Reduces context overhead from 70% to ~5%. Git provides continuity; entire.io provides searchable reasoning archive.

## ADR-008: Tiered model routing with cheap-first default (2026-02-13)
**Context:** ADR-004 assigned models per agent role, but lacked cost discipline. Most routine operations (summarisation, formatting, simple Q&A) don't need Opus-class models. Sessions were burning expensive tokens on trivial work.
**Decision:** Introduce 4-tier routing in rhea_bridge.py: cheap (Sonnet/Flash/mini), balanced (GPT-4o/Gemini-2.5-Flash), expensive (Gemini-2.5-Pro/GPT-4.5/o3), reasoning (o4-mini/DeepSeek-R1). Default tier = cheap. Expensive/reasoning tiers require explicit justification. New methods: `ask_default()` (always cheap), `ask_tier()` (explicit tier), `tribunal()` now tier-aware.
**Rationale:** Enforces cost discipline at the API layer. Cheap tier covers ~80% of agent work. Expensive models reserved for deep research, critique, and novel synthesis. Extends ADR-004 by making tier selection explicit rather than role-based.
**Supersedes:** Partially extends ADR-004 (model assignment is now tier-first, role-second).

## ADR-009: Agent team tier integration — cost-aware agents (2026-02-13)
**Context:** ADR-008 added tiers to rhea_bridge.py, but agent definitions in state_agents_core.md had no connection to the tier system. Agents couldn't self-regulate cost.
**Decision:** Each agent now has a declared default tier and escalation tier. 5 agents (Chronos, Hypnos, Hermes, Hestia, + Rhea default) are cheap-only — they never escalate. 2 agents (Athena, Hephaestus) default to balanced, escalate to expensive. Apollo defaults cheap, escalates to reasoning. Escalation requires logged rationale. Agent prompt modifiers now include explicit cost discipline instructions.
**Rationale:** Pushes cost discipline from the API layer (ADR-008) into agent behaviour. Estimated ~80% of all agent calls stay on cheap tier. Only Athena and Hephaestus routinely use balanced. Expensive/reasoning reserved for genuine novel reasoning.
**Depends on:** ADR-008 (tier routing infrastructure).

## ADR-010: Memory Budget, Discomfort Metric, and Self-Improvement Loops (2026-02-13)
**Context:** Rhea's memory accumulates snapshots, docs, and reasoning traces across sessions. Without active management, context windows fill with "remembering" instead of "thinking." Previous sessions burned 70%+ context on memory retrieval (ADR-007). Need a formal mechanism to detect bloat and trigger compaction.
**Decision:** Introduce:
1. **Discomfort function D** — weighted sum of core_docs_kb, repo_size_mb, open_todo_count, 1/insights_per_request, avg_context_tokens. Tracked in `metrics/memory_metrics.json`.
2. **Thresholds** — T1 (warning: D≥150), T2 (overload: D≥300). Current D=91.96 (comfort).
3. **Reflexive Sprint** — triggered at D≥T2 or manual request. Archivist agent proposes: summarize bloated docs, move details to `archive/`, create ADRs, compact while preserving meaning.
4. **Memory zones** — core (`docs/`), episodic (`.entire/`), metrics (`metrics/`), tasks (`data/`), archive (`archive/`).
5. **Snapshot retention** — named snapshots persist; AUTO-*/POST_COMMIT-* older than 30 days archivable.
6. **Challenging tasks registry** — `data/challenging_tasks.yaml` for investing free capacity into deep reasoning.
**Rationale:** Formalizes the "self-improving memory" concept from the ChatGPT system prompt. Ensures Rhea can grow without losing coherence. D function provides quantitative signal for when compaction is needed.
**Depends on:** ADR-007 (three-tier memory), ADR-008 (cheap-first routing for archivist agent).

## ADR-011: Self-Evaluation & Self-Upgrade Techniques (2026-02-14)
**Context:** Rhea needs mechanisms to improve its own outputs without human micro-management. The system prompt formalized 6 techniques for self-improvement, but they needed anchoring in the decision log.
**Decision:** Adopt 6 self-improvement patterns:
1. **Reflexion** — generate → self-evaluate → revise (3 cycles max). Cheap models draft, then self-critique.
2. **Tribunal/Debate** — 3+ models argue a question; synthesize into weighted consensus. Used for high-stakes decisions.
3. **Tool-Verification Loops** — after code generation, immediately run/test; iterate until passing.
4. **Eval Sets** — maintain `eval/tasks/*.yaml` with known-answer tasks; run periodically to detect regression.
5. **Failure Memory** — log failures in `docs/reflection_log.md` with root cause and fix; consult before similar tasks.
6. **Teacher-Student** — expensive models (Opus, GPT-5.1) as teachers for hard problems; distill patterns to cheap models.
**Rationale:** These patterns are proven in AI research (Shinn et al. 2023 Reflexion paper, debate/constitutional AI from Anthropic). They turn Rhea from a passive tool into an actively self-correcting system.
**Depends on:** ADR-008 (tier routing for teacher-student), ADR-010 (metrics for eval sets).

## ADR-012: Keep Manual-Commit, Defer Hybrid Auto-Snapshots (2026-02-14)
**Context:** Tribunal-001 evaluated switching Entire.io from `manual-commit` to `auto-commit` strategy. Three perspectives debated: Advocate (richer capture), Skeptic (trailers + clean history), Pragmatist (hybrid cron approach).
**Decision:** Keep `manual-commit`. Defer hybrid auto-snapshots (cron-based `entire checkpoint create` every 30 min) to Stage 2.
**Rationale:** Manual-commit was hard-won (Sessions 10–12). Trailers provide provenance in `git log`. Auto-commit creates snapshot noise and pollutes git history. The hybrid approach captures benefits of both without drawbacks.
**Depends on:** ADR-008 (cost/storage), ADR-011 (self-improvement benefits from richer data).

## ADR-013: Wrapper Script for Cross-Mode Entire.io Checkpoints (2026-02-14)
**Context:** Tribunal-002 diagnosed that Cowork commits (via `osascript do shell script "git commit..."`) bypass Entire.io's session lifecycle. No `session-start` fires → `prepare-commit-msg` has no session context → no `Entire-Checkpoint` trailer → zero checkpoints for 4+ commits. Only commits from Claude Code (which runs its own session lifecycle) produced checkpoints.
**Decision:** Create `scripts/rhea_commit.sh` wrapper that explicitly calls `entire hooks git session-start` before and `session-stop` after every commit. All Cowork sessions must use this wrapper instead of raw `git commit`.
**Rationale:** 3/3 free-tier models in Tribunal-002 unanimously recommended wrapper script (agreement score 0.95). Preserves manual-commit benefits (trailers, clean history) while fixing the cross-mode gap. Zero cost, minimal implementation.
**Depends on:** ADR-012 (manual-commit strategy), ADR-007 (three-tier memory).
