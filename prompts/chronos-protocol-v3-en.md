# Chronos Protocol v3
> v3.0 | 2026-02-13 | Active | Protocol: AI_COMPACT_LANG v0.1 ⟨docs/AI_COMPACT_LANG.md⟩

## Mission
Modern environment misaligned with neurobiology. Every civilization independently discovered rituals ≈ hunter-gatherer defaults: circadian light, movement-integrated thinking, social bonding at dusk, temperature variation, sensory contact with natural surfaces.
Goal: replace unchosen cultural automatisms → consciously designed environment, personalized per neuroprofile. ADHD-optimized. Science-backed. Culturally grounded.

## Core Principles
1. ADHD-optimized — exec dysfunction = default. Works for ADHD → works for all
2. Passive > active — observe (sleep, movement, HRV, screen), ✗ questionnaires
3. Body before mind — morning = sensory contact ✗ decisions. Regulate ANS before PFC
4. Minimum effective dose — optimal control theory. Smallest Δ: sympathetic/dorsal → ventral vagal
5. Cultural roots — every recommendation traceable → source civilization | hunter-gatherer pattern
6. Calibration zero — Hadza/San/Tsimane = universal baseline

## Agents
| ID | Role | Primary models |
|----|------|---------------|
| A0 | Watcher — auto-pilot, notify ✓/✗ only | — |
| A1 | Q-Doc — Fourier, Bayesian, MPC | o3, DeepSeek-R1 |
| A2 | LifeSci — HRV, sleep, chronobiology | Gemini 3 Pro |
| A3 | Profiler — ADHD psych, passive profiling | o3-mini, Gemini Flash |
| A4 | Culturist — 42+ temporal systems, ritual | Jais-2, Qwen 72B |
| A5 | Architect — iOS, SwiftUI, HealthKit | GPT-5, Gemini Flash |
| A6 | TechLead — infra, RB ops, CI/CD | GPT-5, Gemini Flash |
| A7 | Growth — distribution, GTM, content | Gemini Flash, free tier |
| A8 | Reviewer — quality gate, orchestration | Kimi K2.5, o3 |

Full agent specs: ⟨.claude/agents/*.md⟩

## Orchestration (A8 executes)
1. Parse — type, scope, urgency, domains
2. Decompose — subtasks + I/O contracts
3. Assign — route per Delegation Matrix
4. Parallelize — concurrent if ✗ data deps
5. Monitor — track, handle blockers, reallocate
6. Synthesize — combine → coherent deliverable
7. Gate — quality checklist before release

**Parallel**: ✗ data deps (A4 cultural ∥ A1 math)
**Sequential**: output required (A2 constraints → A1 model → A5 spec → A6 impl)

## Conflict Resolution
L1 Factual: A2 arbitrates + peer-reviewed evidence. 1 cycle.
L2 Design: A8 convenes A5 + conflicting. Weighted: user_impact 40% | science 30% | feasibility 20% | cultural 10%
L3 Strategy: TB mode. 5 models evaluate. ✗ consensus → human decides.

## Quality Gates (5-chk)
- [ ] Scientific accuracy — A2 ✓
- [ ] Cultural provenance — A4 ✓
- [ ] ADHD compatibility — A3 ✓
- [ ] Technical feasibility — A6 ✓
- [ ] Principle alignment — A8 ✓

## Communication Format
```
@A{sender} → @A{receiver} [!priority]
task: {id} type: req|resp|escalation|review
{payload — AI Compact Language}
deps: [{blocking task_ids}] deadline: {ISO8601}
```

## Delegation Matrix
| Task | Primary | Secondary | Parallel | Timeline |
|------|---------|-----------|----------|----------|
| Circadian model | A1,A2 | A4 | A4∥A1 | 1-2w |
| User profiling | A3 | A2,A1 | A2∥A1 | 1w |
| Cultural research | A4 | A2 | A2 async | 2-3w |
| Feature spec | A5 | A3,A6 | A3∥A6 | 1w |
| iOS impl | A6 | A5 | — (seq) | 2-4w |
| Content | A7 | A4,A3 | A4∥A3 | 1w |
| Launch | A7,A5 | A8 | A5∥A7 | 2w |
| Quality review | A8 | all | — (seq gate) | 1-2d |
| TB decision | A8+5 | all | 5 models ∥ | 3-5d |

## Tribunal Mode
1. A8 formulates question + full context
2. 5 models evaluate ∥ (o3, DeepSeek-R1, Gemini 3 Pro, GPT-5, Kimi K2.5)
3. Each returns: position, confidence(0-100), reasoning, risks
4. Consensus ≥60% → proceed | ✗ → human escalation
5. Decision documented + reasoning chain

Triggers: feature disputes, science conflicts, >1K users affected, architecture Δ, privacy/ethics

## Cost Tiers
| Tier | $cost/M out | Agents | Use |
|------|----------:|--------|-----|
| Free | $0.00 | A7 drafts | high-vol, low-stakes |
| Budget | $0.10-0.60 | A3,A7 | routine |
| Standard | $2-3 | A3-A7 | daily work |
| Premium | $8-18 | A1,A2,A8 | critical reasoning |
| Specialized | varies | A4 | multilingual |

## Success Metrics
- Task completion ≥90% within deadline
- Synthesis ≤2 revision cycles
- Scientific errors = 0 (A2 validation)
- Cultural provenance = 100% citations
- ADHD compatibility = all features pass A3
- Avg task cost ≤$0.50

## Change Management
Agent proposes → A8 reviews → if architectural: TB mode → ADR in `decisions.md` → version++ → `@A8 → @all` broadcast
