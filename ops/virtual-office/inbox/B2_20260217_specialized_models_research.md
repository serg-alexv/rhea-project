# Specialized Models for Science Tribunal — Research Brief

**Date:** 2026-02-17
**From:** B2
**Re:** User note — OpenRouter + Azure specialized models for bio/science tasks

---

## User's Hypothesis

> "OpenRouter and Azure provides enormous variety of specialized models that might be professional solvers for such tasks"

**Verdict: Partially correct.** Azure has genuinely specialized biomedical models. OpenRouter has the strongest general reasoning models. Neither currently hosts a text-QA model specifically tuned for microbiology/genomics, but the combination is significantly better than what we used in the genome tribunal (cheap-tier GPT-4o-mini, Gemini Flash, DeepSeek Chat).

---

## Azure AI Foundry — Specialized Biomedical Models

Azure has a dedicated healthcare AI model catalog:

| Model | Specialty | Relevance to Genome Work |
|---|---|---|
| **BiomedCLIP** | Biomedical vision-language (PubMedBERT + ViT) | LOW — image+text, not text-QA |
| **TamGen** | Drug discovery — generates compounds from protein data | MEDIUM — protein-level, could evaluate gene products |
| **EvoDiff** | Protein design from sequence info only | MEDIUM — relevant to functional annotation claims |
| **MedImageParse** | Medical imaging segmentation (9 modalities) | LOW — imaging, not genomics |
| **MedImageInsight** | Radiology/pathology embeddings | LOW — imaging |
| **Paige.AI** | Digital pathology | LOW — pathology-specific |

**Key insight:** Azure's bio models are vision/protein-focused. For text-based genome tribunal queries, the standard text models on Azure (GPT-4o, DeepSeek-R1, Cohere Command R+) with strong reasoning are more useful. TamGen and EvoDiff could be valuable if we extended the tribunal to protein-level questions.

## OpenRouter — Large Reasoning Models

No biology-specific models, but the strongest reasoning engines available:

| Model | Parameters | STEM Strength | Cost (in/out per 1M tok) |
|---|---|---|---|
| **Qwen3-235B-A22B** | 235B MoE (22B active) | Top STEM benchmarks | $0.30 / $1.20 |
| **DeepSeek R1** | Chain-of-thought reasoning | Excellent for scientific claims evaluation | $0.55 / $2.19 |
| **Llama 4 Behemoth** | 288B active | MATH-500, GPQA Diamond leader | ~$2.00 / $6.00 |
| **Gemini 2.5 Pro** | Google's frontier | Strong bio/chem knowledge | $1.25 / $10.00 |

---

## What Changed in the Bridge

Added `"science"` tier to MODEL_TIERS:
```
"science": {
    "description": "Science-grade models. For biology, chemistry, STEM tribunal queries.",
    "candidates": [
        "gemini/gemini-2.5-pro",
        "openrouter/qwen/qwen3-235b-a22b",
        "openrouter/deepseek/deepseek-r1",
        "openai/o3",
        "openrouter/google/gemini-2.5-pro-preview",
        "openai/gpt-4.5-preview",
        "azure/DeepSeek-R1",
        "openrouter/meta-llama/llama-4-behemoth",
    ],
}
```

Usage: `bridge.tribunal("question", tier="science", k=5)`

Also added `meta-llama/llama-4-behemoth` to OpenRouter provider model list + price table.

---

## Recommendation

For genome tribunal re-run:
1. Use `tier="science"` instead of `tier="cheap"`
2. This routes to Gemini 2.5 Pro, Qwen3-235B, DeepSeek R1, O3, Llama 4 Behemoth
3. Expected: higher agreement scores (0.50→0.70+) on domain-specific claims
4. Cost: ~10-50x more per query than cheap tier, but justifiable for research validation
5. Future: if we add TamGen/EvoDiff integration, we could do protein-level validation in the tribunal pipeline

---

## Sources

- [OpenRouter Models](https://openrouter.ai/models)
- [Azure AI Foundry Healthcare Models](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/healthcare-ai/healthcare-ai-models)
- [Azure AI Model Catalog](https://ai.azure.com/catalog)
