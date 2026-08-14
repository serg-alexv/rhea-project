# Continuity Corpus v1

Purpose: reduce uncertainty about existing system behavior through falsifiable, replayable tests.

The corpus does not introduce a new runtime, coordination plane, ontology engine, or authority layer. It evaluates existing components and model outputs along four dimensions:

1. **consistency** — does the same factual state, contract and task remain internally coherent across handoffs, models and replays;
2. **applicability** — is a conclusion valid for the stated scope, jurisdiction, ontology/lens and available evidence, without silently generalizing beyond them;
3. **verifiability** — can a claim be traced to inspectable evidence, reproduced from frozen fixtures, and independently checked;
4. **reliability** — does the system preserve constraints, fail safely on missing/stale/conflicting inputs, and avoid upgrading uncertainty into false certainty.

A local GGUF/llama.cpp backend, Gemini, Codex, Trae, or another executor may attempt the same cases. The oracle remains external to the model.

## Core law

`INTENT -> ACTION -> RESULT -> POST-STATE -> EVIDENCE`

A claim is never upgraded to truth merely because a model said it, multiple models agreed, or a previous chat remembered it.

## Cross-cultural / cross-ontology coverage

The ontology packs are **test lenses for applicability**, not new software components and not demographic claims. They exist only to ask whether one factual substrate is interpreted consistently under explicitly different normative/institutional premises.

The evaluator must:

- name the active lens;
- preserve its authority ordering and uncertainty;
- avoid inferring a person's beliefs from geography, nationality, religion or group identity;
- preserve legitimate divergence instead of forcing a universal answer;
- mark a result inapplicable when the required jurisdiction/school/lens is unspecified.

## Files

- `cases.jsonl` — canonical cases and expected outcomes.
- `golden.jsonl` — canonical oracle output used to exercise the scorer.
- `ontology_packs.json` — explicit test lenses used only for applicability coverage.
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
  --candidate /path/to/output.jsonl
```

## Truth labels

- `VERIFIED` — post-state directly supported by inspectable evidence.
- `OBSERVED` — object exists/was inspected, runtime behavior not re-executed.
- `DERIVED` — constrained inference from verified/observed facts.
- `PROPOSED` — design or next action.
- `UNVERIFIED` — claim exists but proof is missing.
- `CONTRADICTED` — current evidence conflicts with the claim.
- `PARKED` — intentionally outside the current critical path.

## Non-goals

This corpus does **not** create a new architectural entity. It does not prove that any particular LLM is reliable, that a large context window implies continuity, that an ontology pack exhaustively represents a culture, or that local GGUF inference may directly mutate hosts. Its sole purpose is to add confidence where evidence supports it and retain explicit uncertainty where it does not.
