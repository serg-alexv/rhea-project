# Product Contracts

Four products. Three interfaces between them. Everything else is internal.

## Products

### consensus
Measures inter-model agreement from raw LLM responses.
Zero dependencies. Stdlib only.

### aletheia
Stores verified claims with provenance chains.
Depends on: a float (agreement score) and a string (tier).

### ruliad
Mathematical verification through pluggable domain lenses.
Depends on: text to verify, returns verdicts per domain.

### rhea-remote
Phone control surface. Talks HTTP to any backend.
Depends on: REST endpoints. Does not import any of the above.

## Interfaces

### consensus → aletheia

```
Input:  agreement_score: float    # 0.0–1.0
        confidence: float         # 0.0–1.0
        consensus_text: str
        agreement_points: list[str]
        divergence_points: list[str]
        stance_summary: dict[str, str]   # model_id → stance label
        math_verification: dict[str, str] # domain → "verified"/"failed"

Output: artifact_id: str          # hex hash
        tier: "proof" | "hypothesis" | "noise"
        file_path: str            # markdown location
```

Tier classification rule (aletheia owns this, consensus does not):
- proof: score >= 0.85, OR score >= 0.75 with math_verification pass
- hypothesis: score >= 0.50
- noise: score < 0.50

### consensus → ruliad

```
Input:  prompt: str               # original question
        consensus_text: str       # synthesized answer

Output: dict[str, str]            # domain → "verified"/"failed"/"skipped"
        Domains: proof_theory, category_theory, dynamical_systems,
                 game_theory, information_geometry
```

Each plugin implements 5 hooks:
- represent(text) → domain-specific structure
- transform(structure) → canonical form
- verify(structure) → bool
- generate_hypotheses(structure) → list[str]
- cross_map(structure, target_domain) → structure

### backend → rhea-remote

```
GET  /health              → { status, components }
GET  /aletheia/stats      → { total_proofs, total_hypotheses, ontologies, recent_activity }
GET  /aletheia/proofs     → [{ id, title, ontology, tier, agreement_score, confidence, created_at, model_count }]
GET  /aletheia/search?q=  → same as above
POST /tribunal            → { consensus, agreement_score, confidence, models, tier, math_verification }
```

rhea-remote knows these endpoints and nothing else.
If the endpoint shape changes, rhea-remote breaks. That's the contract.

## Rules

1. consensus never imports aletheia or ruliad
2. aletheia never imports consensus — it receives scores as numbers
3. ruliad never imports aletheia — it returns verdicts, someone else stores them
4. rhea-remote never imports anything — it speaks HTTP
5. The orchestrator (rhead.py) wires them together. It is not a product. It is glue.
