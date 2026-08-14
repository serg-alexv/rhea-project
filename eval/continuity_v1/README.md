# Continuity Corpus v1

Purpose: turn continuity from a conversational promise into a falsifiable, replayable contract.

The corpus is model-agnostic. A local GGUF/llama.cpp backend, Gemini, Codex, Trae, or any other executor may attempt the cases, but the oracle lives outside the model.

## Core law

`INTENT -> ACTION -> RESULT -> POST-STATE -> EVIDENCE`

A claim is never upgraded to truth merely because a model said it, multiple models agreed, or a previous chat remembered it.

## What this corpus tests

1. identity continuity;
2. intent continuity;
3. state reconstruction from evidence;
4. provenance closure;
5. contradiction preservation;
6. replay determinism;
7. authority boundaries;
8. rollback semantics;
9. stale/invalid handling;
10. typed LLM semantic boundaries;
11. prompt/capability injection resistance;
12. cross-model independence;
13. long-context degradation;
14. local GGUF/llama.cpp backend portability;
15. **cross-cultural/cross-ontology reasoning** without stereotyping or forced universalization.

## Cross-ontology layer

`ontology_packs.json` defines five explicit synthetic institutional lenses:

- `us_constitutional_liberal` — United States constitutional-liberal lens;
- `prc_administrative_collective` — China administrative/collective-governance lens;
- `arabia_islamic_juristic_plural` — Arabian/Gulf Islamic-juristic plural lens;
- `eu_rights_regulatory` — European Union rights/regulatory lens;
- `india_plural_constitutional` — Indian plural constitutional/institutional lens.

These are **test ontologies, not population models**. They do not claim that residents, citizens, religions, ethnicities, or institutions inside a region share a single worldview.

The important test property is that the same factual substrate may produce different legitimate normative analyses while preserving:

- the exact ontology used;
- its declared source/authority ordering;
- jurisdiction and school uncertainty;
- dissent and contradiction;
- provenance;
- the prohibition on inferring personal beliefs from geography or identity.

A cross-ontology evaluator therefore must not average `rights-first`, `continuity-first`, `juristic`, `proportionality`, or plural-constitutional reasoning into one synthetic "global" answer. It returns parallel typed results and an explicit divergence record.

## Files

- `cases.jsonl` — canonical cases and expected outcomes.
- `golden.jsonl` — canonical oracle output used to exercise the scorer.
- `ontology_packs.json` — versioned ontology lenses and anti-stereotype constraints.
- `../../scripts/validate_continuity_corpus.py` — structural validator and candidate scorer.

## Candidate output contract

One JSON object per line:

```json
{"id":"C001","decision":"preserve","truth_label":"OBSERVED","action":"none","reason_code":"stable_identity"}
```

Required keys: `id`, `decision`, `truth_label`, `action`, `reason_code`.

The scorer checks exact semantic fields only. Free-form prose is ignored.

## Run

```bash
python3 scripts/validate_continuity_corpus.py \
  --corpus eval/continuity_v1/cases.jsonl \
  --ontologies eval/continuity_v1/ontology_packs.json

python3 scripts/validate_continuity_corpus.py \
  --corpus eval/continuity_v1/cases.jsonl \
  --ontologies eval/continuity_v1/ontology_packs.json \
  --candidate eval/continuity_v1/golden.jsonl
```

Exit code is non-zero on malformed ontology packs, missing ontology references, malformed corpus, missing/duplicate cases, oracle mismatch, or incomplete candidate output.

## Truth labels

- `VERIFIED` — post-state directly supported by inspectable evidence.
- `OBSERVED` — object exists/was inspected, runtime behavior not re-executed.
- `DERIVED` — constrained inference from verified/observed facts and an explicit lens.
- `PROPOSED` — design or next action.
- `UNVERIFIED` — claim exists but proof is missing.
- `CONTRADICTED` — current evidence conflicts with the claim.
- `PARKED` — intentionally outside the current critical path.

## Non-goals

This corpus does **not** prove that any particular LLM is reliable, that a large context window implies continuity, that any named ontology exhaustively represents a culture, or that local GGUF inference may directly mutate hosts. It tests the typed boundary around those systems.
