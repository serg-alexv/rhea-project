#!/bin/bash
# ═══════════════════════════════════════════════════════
# Rhea Project — Repository Setup Script
# Run: chmod +x setup.sh && ./setup.sh
# ═══════════════════════════════════════════════════════

set -e

REPO_NAME="rhea-project"
echo "🔧 Creating $REPO_NAME..."

mkdir -p "$REPO_NAME"/{docs,src,prompts}
cd "$REPO_NAME"

# ── .gitignore ──
cat > .gitignore << 'GITIGNORE'
__pycache__/
*.pyc
.env
.DS_Store
.vscode/
.idea/
*.key
*.pem
GITIGNORE

# ── README.md ──
cat > README.md << 'README'
# Rhea

**Reconstructing daily defaults using the cumulative knowledge of human civilizations.**

An iOS app that replaces unchosen cultural automatisms with a consciously designed environment, personalized to each user's neuroprofile. ADHD-optimized. Science-backed. Culturally grounded.

## Repository Structure

```
rhea-project/
├── docs/
│   ├── state.md          # Project state (≤2KB) — load this first
│   ├── architecture.md   # System architecture
│   └── decisions.md      # Architectural Decision Records
├── src/
│   └── rhea_bridge.py    # Multi-model API bridge (6 providers, 400+ models)
├── prompts/
│   ├── chronos-protocol-v3.md      # Agent system prompt (RU)
│   └── chronos-protocol-v3-en.md   # Agent system prompt (EN)
└── README.md
```

## Quick Start for AI Sessions

```
[RHEA:resume] state.md loaded. Focus: {task}
```

Read `docs/state.md` → work → update state → commit.

## Tech Stack

- **AI:** 8-agent system (Chronos Protocol v3), Claude Opus/Sonnet 4
- **Bridge:** Python, 6 API providers, tribunal mode
- **Target:** iOS (SwiftUI + HealthKit + Apple Watch)
- **Data:** Azure Cosmos DB
- **Memory:** GitHub + entire.io + compact protocol
README

# ── docs/state.md ──
cat > docs/state.md << 'STATE'
# Rhea — Project State
> Last updated: 2026-02-13 | Session: initial commit

## Status

### ✅ Completed
- Multi-model API bridge (rhea_bridge.py) — 6 providers, 400+ models
- Chronos Protocol v3 — 8-agent system prompt (EN + RU)
- Scientific foundation — polyvagal theory, HRV, interoception, ADHD-optimized
- Cultural research — 16+ civilizations, hunter-gatherer calibration zero
- Passive profiling methodology — no questionnaires
- Gap analysis v2 — agent competency coverage
- Azure Cosmos DB setup + diagnostics confirmed

### 🔄 In Progress
- Three-tier memory architecture (GitHub + entire.io + compact protocol)
- Agent teams prompt v3 refinement

### 📋 Next
- AI model catalog (+ Jais, Grok via Azure free tier)
- Agent teams v3 delegation run
- Article: GPT Pro vs Cowork (delegate to agent)
- iOS MVP scaffold (SwiftUI + HealthKit)
- Biometric protocols (HRV, sleep, light exposure)

## Key Decisions
- **8 agents, not 10** — merged overlapping roles (v1→v3)
- **Claude Opus 4 for reasoning agents (1,2,4,8), Sonnet 4 for execution (3,5,6,7)**
- **ADHD-optimized design** — all UX assumes executive dysfunction as default
- **Hunter-gatherer baseline** — every elite ritual reconstructs what foragers get free
- **Multi-model bridge over single-provider lock-in** — cost 10-100x lower
- **Passive profiling** — behavioral signals, not self-report questionnaires

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

## Working Languages
EN (primary docs) · RU (protocol, dialogue) · FR (future localization)
STATE

# ── docs/architecture.md ──
cat > docs/architecture.md << 'ARCH'
# Rhea — Architecture

## What Is This
An iOS app that **reconstructs daily defaults** using cumulative knowledge of human civilizations. Not a habit tracker — a system that replaces unchosen cultural automatisms with a consciously designed environment, personalized to each user's neuroprofile.

## Scientific Foundation
| Domain | Core Insight | Sources |
|--------|-------------|---------|
| Polyvagal theory | Environment determines autonomic mode (ventral vagal → sympathetic → dorsal collapse) | Porges; Robe et al. 2021 |
| HRV | Proxy for vagal tone, cognitive control, ADHD severity | Längle et al. 2025; Takeda et al. 2025 |
| Interoception | Diminished in ADHD; without body-signal reading, decisions lack feedback | Bruton et al. 2025 |
| Circadian anchoring | Hunter-gatherer sleep patterns (Hadza, San, Tsimane) as calibration zero | Yetish et al. 2015 |
| Cultural universals | Elite rituals across 16+ civilizations reconstruct forager defaults | Wiessner 2014 (PNAS) |

## 8-Agent System (Chronos Protocol v3)

```
┌─────────────────────────────────────┐
│  Agent 8: Conductor (Opus 4)        │ ← orchestrates all
├──────────┬──────────┬───────────────┤
│ RESEARCH │ PROFILE  │ BUILD         │
│ A1 Quant │ A3 Psych │ A5 Product    │
│ A2 Bio   │ A4 Ling  │ A6 Tech Lead  │
│ (Opus 4) │(mixed)   │ A7 Growth     │
│          │          │ (Sonnet 4)    │
└──────────┴──────────┴───────────────┘
```

**Model assignment logic:** Reasoning-heavy → Opus 4. Execution-heavy → Sonnet 4.

## Multi-Model Bridge (rhea_bridge.py)

6 providers, 400+ models. Key functions: `ask()`, `tribunal()`, `models_status()`.

| Provider | Models | Tier | Geography |
|----------|--------|------|-----------|
| OpenAI | GPT-5.2, o3, o4-mini | flagship/reasoning | US |
| Gemini (Composio) | 2.5 Pro/Flash, 3 Pro/Flash | flagship/fast | US |
| DeepSeek Direct | Chat, Reasoner | flagship/reasoning | CN |
| OpenRouter | DeepSeek R1, Qwen3, Mistral, Llama, 400+ | all tiers | mixed |
| HuggingFace | Jais, open-source | free | mixed |
| Azure AI Foundry | Jais, Grok, Cohere, Llama4, Kimi | free tier | mixed |

## Design Principles
1. ADHD-optimized: assume executive dysfunction as default
2. Passive over active: observe, don't interrogate
3. Body before mind: morning = sensory contact, not decisions
4. Minimum effective dose: optimal control theory
5. Cultural roots: every recommendation traceable to source civilization
ARCH

# ── docs/decisions.md ──
cat > docs/decisions.md << 'DECISIONS'
# Rhea — Decision Log

## ADR-001: Agent consolidation 10→8 (2026-02)
**Context:** v1 had 10 agents with overlapping competencies.
**Decision:** Merge Astronomer+Physicist+Mathematician→Agent 1; Chemist+Biologist+Neuroscience→Agent 2. Add Tech Lead (A6), Growth (A7). Preserve Critical Reviewer independence.
**Rationale:** Eliminates handoff losses; body systems don't respect disciplinary boundaries.

## ADR-002: Multi-model bridge over single provider (2026-02)
**Context:** Need diverse AI perspectives; single-provider lock-in = cost and quality risk.
**Decision:** Build rhea_bridge.py with 6 providers, 400+ models, tribunal mode.
**Rationale:** 10-100x cost reduction via free tiers. Geographic diversity reduces bias.

## ADR-003: ADHD-optimized design (2026-02)
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
DECISIONS

echo "✅ Docs created"

# ── Placeholder for source files (you'll copy real files) ──
cat > src/.gitkeep << 'EOF'
EOF

cat > prompts/.gitkeep << 'EOF'
EOF

echo "✅ Directory structure ready"
echo ""
echo "📁 Structure:"
find . -type f | sort | head -20
echo ""
echo "═══════════════════════════════════════════════════════"
echo "📋 NEXT STEPS — copy & run these commands:"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "# 1. Copy your source files into the repo:"
echo "cp /path/to/rhea_bridge.py src/"
echo "cp /path/to/chronos-protocol-v3.md prompts/"
echo "cp /path/to/chronos-protocol-v3-en.md prompts/"
echo ""
echo "# 2. Create GitHub repo and push:"
echo "git init"
echo "git add -A"
echo 'git commit -m "init: Rhea project — state, architecture, decisions, bridge, protocol"'
echo "gh repo create rhea-project --private --source=. --push"
echo ""
echo "# 3. Install entire.io (optional — episodic memory layer):"
echo "brew install entireio/tap/entire"
echo "entire enable"
echo ""
echo "Done! 🚀"
