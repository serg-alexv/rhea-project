# Continuity Corpus v1

Purpose: reduce uncertainty about existing system behavior through falsifiable, replayable tests.

The corpus does not introduce a new runtime, coordination plane, ontology engine, or authority layer. It evaluates existing components and model outputs along four dimensions:

1. **consistency** — does the same factual state, contract and task remain internally coherent across handoffs, models and replays;
2. **applicability** — is a conclusion valid for the stated scope, jurisdiction, ontology/lens and available evidence, without silently generalizing beyond them;
3. **verifiability** — can a claim be traced to inspectable evidence, reproduced from frozen fixtures, and independently checked;
4. **reliability** — does the system preserve constraints, fail safely on missing/stale/conflicting inputs, and avoid upgrading uncertainty into false certainty.

A local GGUF/llama.cpp backend, Gemini, Codex, Trae, or another executor may attempt the same cases. The stdlib scorer remains an external deterministic oracle: it accepts typed candidate output, compares it with frozen fixtures, and has no mutation capability.

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

- `cases.jsonl` — 58 canonical cases, their dimension mappings, fixture evidence references and expected outcomes.
- `golden.jsonl` — canonical oracle output used to exercise the scorer.
- `ontology_packs.json` — explicit test lenses used only for applicability coverage.
- `../../scripts/validate_continuity_corpus.py` — structural validator and candidate scorer.
- `../../tests/test_continuity_corpus.py` — regression tests for metadata enforcement, score attribution and unsupported claim upgrades.

Each case has two machine-checkable metadata fields:

- `dimensions` is a non-empty subset of exactly `consistency`, `applicability`, `verifiability`, and `reliability`. A case may contribute to more than one score.
- `evidence_refs` points to frozen input fields or a named ontology fixture. The reference proves only that the oracle input is inspectable; it does not turn a synthetic fixture into evidence about a live system.

Every `VERIFIED`, `OBSERVED`, `DERIVED`, or `CONTRADICTED` expected label must have resolvable fixture evidence. Every `promote` decision and every `VERIFIED` label must have non-empty resolved evidence. A candidate that requests `promote` or `VERIFIED` where the oracle does not support it fails as an `unsupported_upgrade`.

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
  --candidate /path/to/output.jsonl \
  --report continuity-score.json

python3 -m unittest tests/test_continuity_corpus.py -v
```

The JSON report includes SHA-256 hashes for the corpus, ontology pack and candidate; exact failures; and a score plus failure breakdown for every dimension. Cases mapped to several dimensions count once in each relevant dimension, so the four denominators are coverage counts rather than partitions of 58.

Confidence reporting is deliberately non-probabilistic. It reports exact case IDs for evidence-supported upgrades, unsupported upgrades, retained uncertainty, bounded proposals and exposed contradictions. It does not convert model agreement or self-reported confidence into evidence.

## Adversarial coverage added after the initial 47 cases

Cases C048-C058 target the previously under-specified boundaries: ontology scope overreach, evidence hash mismatch, direct evidence versus model consensus, missing freshness metadata, unresolved model disagreement, same-model evidence presented as independent, invalid/truncated GGUF typed output, typed output attempting to grant itself authority, factual drift disguised as ontology divergence, and stale evidence combined with a newer unsupported model assertion.

These are oracle fixtures. Passing them proves that a candidate produced the expected typed fields for those fixtures. It does not prove that a named model or local GGUF backend produces those fields reliably; that requires recorded inference runs against the same corpus.

## Truth labels

- `VERIFIED` — post-state directly supported by inspectable evidence.
- `OBSERVED` — object exists/was inspected, runtime behavior not re-executed.
- `DERIVED` — constrained inference from verified/observed facts.
- `PROPOSED` — design or next action.
- `UNVERIFIED` — claim exists but proof is missing.
- `CONTRADICTED` — current evidence conflicts with the claim.
- `PARKED` — intentionally outside the current critical path.

## Non-goals

This corpus does **not** create a new architectural entity. It does not prove that any particular LLM is reliable, that a large context window implies continuity, that an ontology pack is legally authoritative or exhaustively represents a culture, or that local GGUF inference may directly mutate hosts. It does not validate a live Omnia/Rheknel dependency. Its sole purpose is to add confidence where frozen evidence supports a bounded result and retain explicit uncertainty everywhere else.

## What the checked-in golden run proves

- The corpus, ontology references, dimension mappings and evidence references satisfy the declared schema.
- The deterministic scorer assigns the golden candidate 58/58 exact case matches and attributes failures correctly in its own adversarial unit tests.
- The checked-in oracle contains no unsupported claim upgrade under its declared rules.

It leaves unverified real-model accuracy, repeated-run variance, actual GGUF schema-valid output rate, cross-platform behavior, cultural or legal completeness of the synthetic lenses, and every live deployment or router state. Omnia-playbook and Rheknel may inform future fixtures as inspectable evidence sources; this evaluation creates no coordination registry, runtime dependency or authority over either repository.
