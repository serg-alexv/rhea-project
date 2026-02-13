# Rhea — Project State
> Last updated: 2026-02-13 | Session: tiered-model-routing

## Status

### ✅ Completed
- Multi-model API bridge (rhea_bridge.py) — 6 providers, 400+ models
- Tiered model routing (ADR-008) — 4 tiers, cheap-first default, ask_default/ask_tier/tribunal
- AI model catalog — pricing, benchmarks, multimodal, tier mapping
- Chronos Protocol v3 — 8-agent system prompt (EN + RU)
- Scientific foundation — polyvagal theory, HRV, interoception, ADHD-first
- Cultural research — 16+ civilizations, hunter-gatherer calibration zero
- Passive profiling methodology — no questionnaires
- Gap analysis v2 — agent competency coverage
- Azure Cosmos DB setup + diagnostics confirmed

### 🔄 In Progress
- Three-tier memory architecture (GitHub + entire.io + compact protocol)
- Agent teams prompt v3 refinement

### 📋 Next
- Agent teams v3 delegation run
- Article: GPT Pro vs Cowork (delegate to agent)
- iOS MVP scaffold (SwiftUI + HealthKit)
- Biometric protocols (HRV, sleep, light exposure)

## Key Decisions
- **8 agents, not 10** — merged overlapping roles (v1→v3)
- **Tiered model routing (ADR-008)** — cheap-first default, expensive requires justification
- **Claude Opus 4 for reasoning agents (1,2,4,8), Sonnet 4 for execution (3,5,6,7)**
- **ADHD-first design** — all UX assumes executive dysfunction as default
- **Hunter-gatherer baseline** — every elite ritual reconstructs what foragers get free
- **Multi-model bridge over single-provider lock-in** — cost 10-100x lower
- **Passive profiling** — behavioral signals, not self-report questionnaires

## Architecture Quick Ref
```
8 Agents → Chronos Protocol v3 → rhea_bridge.py (4 tiers) → 6 providers
Default: cheap tier (Sonnet/Flash/mini) · Expensive requires justification
Agent 1: Quantitative Scientist (Opus 4)
Agent 2: Life Sciences Integrator (Opus 4)
Agent 3: Psychologist / Profile Whisperer (Sonnet 4)
Agent 4: Linguist-Culturologist (Opus 4)
Agent 5: Product Architect (Sonnet 4)
Agent 6: Tech Lead (Sonnet 4 + Claude Code)
Agent 7: Growth Strategist (Sonnet 4)
Agent 8: Critical Reviewer & Conductor (Opus 4)
```

## Working Languages
EN (primary docs) · RU (protocol, dialogue) · FR (future localization)
