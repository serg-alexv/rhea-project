---
sidebar_position: 1
---

# Tribunal — Multi-Model Consensus

The Tribunal is Rhea's core differentiator: instead of trusting a single AI model's answer, it queries multiple models simultaneously and analyzes their agreement, disagreement, and reasoning patterns.

## Why Multi-Model Consensus?

Every individual LLM has biases, knowledge gaps, and hallucination patterns. By querying 3–10 models and comparing:
- **High agreement** (&gt;80%) with diverse models → likely reliable
- **Low agreement** (&lt;50%) → genuine ambiguity or poorly-defined question
- **Split opinions** → important divergence worth investigating

## Three Consensus Levels

### Level 1 — Local Analysis (Free)

All `k` models are queried in parallel. The `ConsensusAnalyzer` performs statistical analysis locally:
- Semantic similarity between responses
- Stance classification (positive/negative/neutral/mixed)
- Agreement and divergence point extraction

No additional API call is made for synthesis.

### Level 2 — Chairman Synthesis (+1 API call)

After Level 1, a "chairman" model (typically from a higher tier) reads all model responses and produces a structured synthesis:
- Unified consensus statement
- Weighted confidence based on model agreement
- Identification of strongest arguments on each side

### Level 3 — ICE (Iterative Critique and Elaboration)

The most thorough (and expensive) mode:

1. **Round 1:** Query `k` models with the original prompt
2. **Critique:** Each model reviews others' answers and provides critiques
3. **Round 2:** Models revise their answers based on critiques
4. **Repeat:** Until convergence or max rounds reached
5. **Chairman:** Final synthesis by a higher-tier model

```
Round 1: Query k models → get initial responses
                ↓
Round 2: Models critique each other → refined responses
                ↓
Round N: Convergence check (agreement_score > threshold?)
                ↓
Chairman: Final synthesis from balanced/expensive tier
```

## Adversarial Layer

Every tribunal response includes an **adversarial check** — a devil's-advocate counter-argument:

```rust
pub fn adversarial_check(claim: &str, agreement_score: f64) -> (String, f64) {
    // High agreement → warn about groupthink
    // Low agreement → acknowledge ambiguity
    // Moderate → request more evidence
    let confidence_adjusted = agreement_score * 0.85; // 15% skepticism discount
    (note, confidence_adjusted)
}
```

The **15% skepticism discount** is always applied. A 90% agreement score becomes 76.5% adjusted confidence. This prevents false certainty.

## Ontology Lenses

Tribunal queries can be filtered through specialized ontology lenses that add domain-specific system prompts:

| Ontology | Focus |
|----------|-------|
| `general` | No special lens |
| `pharmacology` | Drug interactions, receptor binding, ADME |
| `biochemistry` | Molecular mechanisms, enzyme kinetics |
| `logic` | Formal logic, proof structure, axioms |
| `topology` | Continuity, connectedness, invariants |
| `systems_biology` | Network dynamics, feedback loops, emergence |

## Cost Awareness

Tribunal costs scale with `k × tier`:
- 3 models × cheap tier ≈ $0.001 per query
- 5 models × balanced tier ≈ $0.05 per query
- 7 models × expensive tier ≈ $0.50 per query
- ICE with 3 rounds × 5 models ≈ $0.50–$2.00 per query

The bridge enforces cost discipline through tiers and execution profiles.
