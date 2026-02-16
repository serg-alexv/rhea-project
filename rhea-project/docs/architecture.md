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
