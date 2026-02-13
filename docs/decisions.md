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
