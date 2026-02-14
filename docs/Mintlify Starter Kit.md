# Rhea — AI Model Catalog
> Last updated: 2026-02-13 | Companion: `models_catalog.json`

## Overview

6 providers · 25+ models · Geographic diversity (US / CN / EU / UAE)

| Provider | Key Models | Tier | Geography |
|----------|-----------|------|-----------|
| OpenAI | GPT-5.2, GPT-4.1, o3, o3-mini | Flagship + Reasoning | US |
| Google Gemini | 3 Flash, 3 Pro, 2.5 Pro/Flash | Flagship + Fast | US (GCP) |
| DeepSeek Direct | V3, R1 Chat, R1 Reasoner | Flagship + Reasoning | CN |
| OpenRouter | Qwen 72B, Mistral Medium 3, Llama 4, free tier | All tiers | Mixed |
| HuggingFace | Jais-2-70B (Arabic) | Open-source | UAE/Mixed |
| Azure AI Foundry | Grok-3/4, Kimi K2.5, Cohere R+, Llama 4 | Free tier | Mixed |

---

## Pricing Matrix ($/M tokens)

| Model | Provider | Input | Output | Cached | Context | Max Out |
|-------|----------|------:|-------:|-------:|--------:|--------:|
| GPT-5.2 | OpenAI | 1.75 | 14.00 | 0.175 | 400K | 128K |
| GPT-4.1 | OpenAI | 2.00 | 8.00 | 0.50 | 1M | 32K |
| GPT-4o-mini | OpenAI | 0.15 | 0.60 | — | 128K | 16K |
| o3 | OpenAI | varies | varies | — | 196K | var |
| o3-mini | OpenAI | 1.10 | 4.40 | — | 128K | var |
| Gemini 3 Flash | Google | 0.50 | 3.00 | — | 2M | — |
| Gemini 3 Pro | Google | 2.00–4.00 | 12–18 | — | 1M | 64K |
| Gemini 2.5 Pro | Google | 1.25–2.50 | 10–15 | — | 1M | — |
| Gemini 2.5 Flash | Google | 0.30 | 2.50 | — | 1M | — |
| Gemini 2.0 Flash | Google | 0.10 | 0.40 | — | 1M | — |
| DeepSeek-V3 | DeepSeek | 0.07–0.27 | var | 0.07 | 128K | 8K |
| DeepSeek-R1 | DeepSeek | 0.07–0.27 | var | 0.07 | 128K | 64K |
| Qwen 2.5 72B | OpenRouter | 0.04 | 0.10 | — | 128K | 8K |
| Mistral Medium 3 | OpenRouter | 0.40 | 2.00 | — | 131K | — |
| Llama 4 Maverick | OpenRouter | 0.31 | 0.85 | — | 1M | — |
| Llama 4 Scout | OpenRouter | **FREE** | **FREE** | — | **10M** | — |
| Jais-2-70B | HF/Azure | **FREE** | **FREE** | — | 8K | — |
| Grok-3 | Azure | 3.00 | 15.00 | — | 131K | 131K |
| Grok-4 | Azure | 3.00 | 15.00 | — | 256K | — |
| Grok-4 Fast | Azure | 0.20 | 0.50 | — | 2M | — |
| Cohere R+ | Azure | 2.375 | 9.50 | — | 128K | — |
| Kimi K2.5 | Azure | 0.60 | 3.00 | — | 262K | 262K |
| Kimi K2 Think | Azure | 0.60 | 2.50 | — | 256K | — |

---

## Multimodal Support

| Model | Text→ | Image→ | Audio→ | Video→ | →Text | →Image | →Audio |
|-------|:-----:|:------:|:------:|:------:|:-----:|:------:|:------:|
| GPT-5.2 | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ |
| GPT-4.1 | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Gemini 3 Flash | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| Gemini 3 Pro | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Gemini 2.5 Pro | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| Gemini 2.0 Flash | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| DeepSeek-V3/R1 | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Llama 4 Maverick | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Kimi K2.5 | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Jais-2-70B | ✓(AR/EN) | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |

---

## Benchmarks (key models)

| Model | MMLU | MATH-500 | AIME | HumanEval | SWE-bench | GPQA Diamond |
|-------|-----:|---------:|-----:|----------:|----------:|-------------:|
| o3 | — | ~95 | **96.7** | — | **71.7** | — |
| DeepSeek-R1 | **90.8** | **97.3** | — | — | — | 71.5 |
| Gemini 3 Flash | — | — | — | — | — | **90.4** |
| GPT-4.1 | — | — | — | — | 54.6 | — |
| DeepSeek-V3 | 87–88 | 90.2 | — | 65.2 | — | — |
| Gemini 2.5 Pro | 89.8 | — | — | — | — | — |

---

## Language Support

| Model | Languages | Arabic | Chinese | Russian |
|-------|----------:|:------:|:-------:|:-------:|
| Qwen 2.5 72B | 119 | ✓ | ✓✓ | ✓ |
| Gemini family | 80+ | ✓ | ✓ | ✓ |
| DeepSeek | 50+ | partial | ✓✓ | ✓ |
| Jais-2-70B | 2 | ✓✓✓ | ✗ | ✗ |
| Kimi K2.5 | multi | partial | ✓✓ | partial |
| Mistral | multi | partial | partial | ✓ |

---

## Agent ↔ Tier Mapping (ADR-008 + ADR-009)

Model selection is now **tier-first, role-second**. Each agent uses `ask_default()` or `ask_tier()` from rhea_bridge.py.

| Agent | Mythic Name | Default Tier | Escalation Tier | Escalation Trigger |
|------:|------------|-------------|----------------|-------------------|
| — | Rhea | cheap | balanced | Genuine inter-agent conflict resolution |
| — | Chronos | cheap | — | Never (deterministic scheduling) |
| — | Gaia | cheap | balanced | Multi-signal correlation (HRV + sleep + circadian) |
| — | Hypnos | cheap | — | Never (algorithmic sleep logic) |
| — | Athena | balanced | expensive | Novel life-architecture / multi-domain tradeoff |
| — | Hermes | cheap | — | Never (templated communication) |
| — | Hephaestus | balanced | expensive | Architecture decisions / novel system design |
| — | Hestia | cheap | — | Never (rule-based safety routines) |
| — | Apollo | cheap | reasoning | Novel cross-domain insight extraction |

**Legacy A1–A8 mapping (for reference):**

| Legacy | Role | Primary Models | Secondary | Rationale |
|------:|------|---------------|-----------|-----------|
| A1 | Quant Scientist | o3, DeepSeek-R1 | GPT-5.2, Kimi K2 Think | AIME 96.7%, MATH-500 97.3% |
| A2 | Life Sciences | Gemini 3 Pro, 2.5 Pro | GPT-5.2 | Multimodal + long context |
| A3 | Psychologist | o3-mini, Gemini 2.5 Flash | GPT-4o-mini | Nuanced reasoning, fast |
| A4 | Linguist-Culture | Jais-2 (AR), Qwen 72B (119 lang) | Gemini (80+ lang) | Multilingual coverage |
| A5 | Product Architect | GPT-5.2, Gemini 3 Flash | Cohere R+, Mistral Med 3 | Tool use, systems design |
| A6 | Tech Lead | GPT-5.2, Gemini 3 Flash | Llama 4 Maverick, Grok-3 | SWE-bench, code gen |
| A7 | Growth | Gemini 2.0 Flash, free models | Llama 4 Scout | Cost → $0, volume |
| A8 | Conductor | Kimi K2.5 (Swarm), o3 | DeepSeek-R1, Gemini 3 Pro | Orchestration, critique |

---

## Cost Optimization Tiers (rhea_bridge.py — ADR-008)

Default tier = **cheap**. Expensive/reasoning require explicit justification.

| Tier | rhea_bridge key | Candidates (ordered) | Cost/M out | When |
|------|----------------|---------------------|--------:|------|
| **cheap** | `"cheap"` | Claude Sonnet 4, Gemini 2.0 Flash, GPT-4o-mini, DeepSeek Chat, Azure GPT-4o-mini, Gemini 2.0 Flash Lite, GPT-4.1-nano | $0.00–0.60 | ~80% of all work. Summaries, formatting, Q&A, drafts, A3/A7 |
| **balanced** | `"balanced"` | GPT-4o, Gemini 2.5 Flash, GPT-4.1, Mistral Large, Azure GPT-4o | $2.00–8.00 | Complex reasoning cheap tier can't handle. A5/A6 hard problems |
| **expensive** | `"expensive"` | Gemini 2.5 Pro, GPT-4.5, o3, Qwen3-235B | $8.00–18.00 | Deep research, critique, novel synthesis. Requires justification. A1/A2/A8 |
| **reasoning** | `"reasoning"` | o4-mini, o3-mini, DeepSeek Reasoner, DeepSeek R1, Azure DeepSeek R1 | $1.10–4.40 | Chain-of-thought, math, logic, proofs. A1 specialised |

**API methods:**
- `ask_default(prompt)` → always cheap tier
- `ask_tier("balanced", prompt)` → explicit tier with fallback
- `tribunal(prompt, tier="cheap")` → multi-model comparison within tier

---

## Notes

1. **Pricing volatility:** DeepSeek announces scheduled updates. Verify before production.
2. **Data sovereignty:** CN models (DeepSeek, Qwen) may require data residency review. EU models (Mistral) GDPR-compliant.
3. **Rate limits:** Most providers don't publish exact RPM/TPM — contact directly for production quotas.
4. **Fine-tuning:** Available for Gemini (Vertex AI), DeepSeek (open weights), Cohere. Reasoning models (o3, R1) do NOT support fine-tuning.
5. **Function calling:** DeepSeek-R1 does NOT support function calling — use V3 for tool-use agents.
