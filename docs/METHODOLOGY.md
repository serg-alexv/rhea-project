# Rhea Methodology — End-to-End

> Independent assessment compiled 2026-02-25. Claims verified against codebase.

## 1. Philosophical Motivation

Rhea begins from a critique of daily structure defaults: modern schedules are cultural artifacts, not biological optima. The "hunter-gatherer calibration zero" (ADR-006) uses Hadza/San/Tsimane patterns as a reference baseline, citing Yetish et al. 2015 and Wiessner 2014. The thesis: if a behavior must be purchased, scheduled, or technologically mediated, it was likely free in the ancestral environment.

This extends to a broader claim (not yet formally substantiated) that formalist scientific paradigms have traded cross-domain bridging capacity for predictive precision within narrow domains.

## 2. Chronobiology Foundations

The system models human state across four temporal scales:

- **Ultradian** (~90 min) — BRAC cycles, attention oscillations
- **Circadian** (~24 h) — core body temperature, cortisol, melatonin
- **Circabidian** (~48 h) — longer-period oscillations in mood and energy
- **Infradian** (weekly+) — menstrual cycles, seasonal patterns

These are established chronobiology concepts (not novel). Rhea's contribution is applying them as a unified state model for agent-based advisory.

**State vector** (from soul.md):
```
x_t = [E_t, M_t, C_t, S_t, O_t, R_t]
E = energy, M = mood, C = cognitive load, S = sleep debt, O = obligations, R = recovery
```

## 3. Mathematical Control Layer

**Objective function** (from CORE_RULES.md):
```
U = a*Progress + b*Evidence - g*Risk - d*Debt - e*MemoryLoad - z*BudgetCost
```

**Discomfort metric** (from ADR-010):
```
D = w1*core_docs_kb + w2*repo_size_mb + w3*open_todo_count + w4*(1/insights_per_request) + w5*avg_context_tokens
```
Thresholds: T1=150 (warning), T2=300 (overload → Reflexive Sprint).

**Verification status:** These are practical heuristics with hand-tuned weights. No formal convergence proofs, stability analysis, or Lyapunov functions exist. The D metric works as an engineering gauge, not a mathematically proven control system.

## 4. Memory Architecture (L0–L8)

| Layer | Type | Implementation | Status |
|-------|------|----------------|--------|
| L0/L1 | Registers | MEMORY.md, CLAUDE.md | Active |
| L2/L3/L4 | RAM | CORE_MEMORY.md, context-state, context-bridge | Active |
| L5/L6 | SSD | knowledge-map, sessions | Partial |
| L7/L8 | Archive | Entire.io snapshots, Git history | Active |

Three-tier external memory (ADR-007): GitHub state.md (≤2KB) as long-term, Entire.io as episodic, compact protocol for session handoff. Reduces context overhead from ~70% to ~5%.

**Verification status:** Architecture is sound and operational. Autonomy is incomplete — commits require manual triggering or wrapper scripts. Reflexive Sprint has never been triggered despite D now exceeding T2 by 3×.

## 5. Agent Orchestration (Chronos Protocol v3)

8 agents (ADR-001), tier-aware (ADR-008/009):

| Agent | Role | Default Tier |
|-------|------|-------------|
| A1 | Quantitative Scientist / Conductor | cheap → reasoning |
| A2 | Life Sciences Integrator | cheap → expensive |
| A3 | Psychologist / Profile Whisperer | cheap only |
| A4 | Linguist-Culturologist | cheap → expensive |
| A5 | Product Architect | cheap only |
| A6 | Tech Lead | cheap only |
| A7 | Growth Strategist | cheap only |
| A8 | Critical Reviewer | cheap → expensive |

Tribunal mode: 3+ diverse models from different providers debate; consensus_analyzer.py synthesizes via ICE (Iterative Consensus Ensemble) or Chairman mode with TF-IDF similarity.

## 6. Verification Pipeline

**Self-improvement loop** (ADR-011):
1. Reflexion (generate → evaluate → revise) — theorized, partially used
2. Tribunal/Debate — implemented in rhea_bridge.py, exercised once (tribunal_002)
3. Tool-Verification loops — principle documented, no automated pipeline
4. Eval sets — eval/tasks/*.yaml exist, not regularly run
5. Failure memory — reflection_log.md with 5 entries (operational)
6. Teacher-Student distillation — documented, not exercised

**Ontology Explorer** (built 2026-02-25): 3-layer verification:
- Layer 1: Multi-model consensus via Rhea bridge tribunal
- Layer 2: Formal proof hooks (Lean4/Z3 stubs, not connected)
- Layer 3: Red-team adversarial agents with 6 attack strategies

## 7. What Works vs. What's Aspirational

| Component | Status | Evidence |
|-----------|--------|----------|
| Multi-model bridge | Working | 32 models, 6 providers, live tribunal calls |
| Memory hierarchy | Working | L0-L8 defined, state.md enforced |
| Checkpoint system | Working | Git + Entire.io, wrapper scripts |
| Failure memory | Working | 5 entries, consulted before similar tasks |
| Agent definitions | Defined | 8 agents with tier assignments |
| Agent orchestration | Partial | Script exists, no automated dispatch |
| Formal proofs | Missing | Zero .lean/.z3 files |
| Reflexive Sprint | Never triggered | Empty history despite D >> T2 |
| Eval regression | Dormant | YAML files exist, no runner |
| Scientific validation | Missing | No experimental pipeline |

## 8. Open Questions

1. How to formalize the "trans-Gödelian" direction without it being empty philosophy?
2. What would a genuine mathematical proof of the memory architecture's robustness look like?
3. How to automate the Reflexive Sprint now that D=867 >> T2=300?
4. How to build a feedback loop from the ontology explorer's cross-domain hypotheses back into core Rhea operation?

---
*This document was generated by independent verification, not by the project's own agents.*
