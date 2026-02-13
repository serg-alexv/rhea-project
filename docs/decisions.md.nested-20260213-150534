# Rhea — Decision Log

## ADR-001: Agent consolidation 10→8 (2026-02)
**Context:** v1 had 10 agents with overlapping competencies.
**Decision:** Merge Astronomer+Physicist+Mathematician→Agent 1; Chemist+Biologist+Neuroscience→Agent 2. Add Tech Lead (A6), Growth (A7). Preserve Critical Reviewer independence.
**Rationale:** Eliminates handoff losses; body systems don't respect disciplinary boundaries.

## ADR-002: Multi-model bridge over single provider (2026-02)
**Context:** Need diverse AI perspectives; single-provider lock-in = cost and quality risk.
**Decision:** Build rhea_bridge.py with 6 providers, 400+ models, tribunal mode.
**Rationale:** 10-100x cost reduction via free tiers. Geographic diversity reduces bias.

## ADR-003: ADHD-first design (2026-02)
**Context:** Neurotypical UX fails for executive dysfunction.
**Decision:** All UX assumes ADHD as default: minimal decision load, passive profiling, body-first morning, no questionnaires.
**Rationale:** Bruton et al. 2025, Längle et al. 2025.

## ADR-004: Claude Opus for research, Sonnet for execution (2026-02)
**Context:** Balance reasoning depth vs speed/cost.
**Decision:** Opus 4 for Agents 1,2,4,8 (reasoning). Sonnet 4 for Agents 3,5,6,7 (execution).

## ADR-005: Passive profiling methodology (2026-02)
**Context:** Self-report questionnaires unreliable, especially for ADHD.
**Decision:** Behavioral signals only. Zero questionnaires in core flow.

## ADR-006: Hunter-gatherer calibration zero (2026-02)
**Context:** Need universal baseline for optimal defaults.
**Decision:** Hadza/San/Tsimane patterns as reference. Every elite ritual converges on this.
**Rationale:** Yetish et al. 2015, Wiessner 2014.

## ADR-007: Three-tier external memory (2026-02-13)
**Context:** 27 transcripts, 70% context spent on "remembering."
**Decision:** GitHub (state.md ≤2KB) + entire.io (episodic) + compact protocol.
**Rationale:** Context overhead 70% → ~5%.
