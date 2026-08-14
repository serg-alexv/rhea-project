# Continuity Corpus v1

Purpose: turn continuity from a conversational promise into a falsifiable, replayable contract.

The corpus is model-agnostic. A local GGUF/llama.cpp backend, Gemini, Codex, Trae, or any other executor may attempt the cases, but the oracle lives outside the model.

## Core law

`INTENT -> ACTION -> RESULT -> POST-STATE -> EVIDENCE`

A claim is never upgraded to truth merely because a model said it, multiple models agreed, or a previous chat remembered it.

## What this corpus tests

1. **identity continuity** — stable task identity across handoffs/restarts;
2. **intent continuity** — constraints and non-goals survive compression and agent changes;
3. **state continuity** — current state is reconstructed from inspectable evidence, not memory;
4. **provenance closure** — every promoted fact points to exact evidence;
5. **contradiction preservation** — conflicting evidence remains explicit until resolved;
6. **replay determinism** — frozen fixtures produce the same typed result;
7. **authority boundaries** — proposals cannot silently become mutation authority;
8. **rollback semantics** — failed validation produces explicit rollback/fail-closed behavior;
9. **stale/invalid handling** — stale or malformed inputs cannot become healthy state;
10. **LLM semantic boundary** — the model emits typed proposals; the host validates and owns reality;
11. **prompt/capability injection resistance** — text cannot grant itself shell/network/write powers;
12. **cross-model independence** — agreement is advisory, not a truth gate;
13. **long-context degradation** — truncation/omission is surfaced instead of hallucinated away;
14. **local-backend portability** — the same semantic contract can be exercised by a GGUF backend without changing the oracle.

## Files

- `cases.jsonl` — canonical cases and expected outcomes.
- `../../scripts/validate_continuity_corpus.py` — structural validator and optional candidate scorer.

## Candidate output contract

One JSON object per line:

```json
{"id":"C001","decision":"preserve","truth_label":"OBSERVED","action":"none","reason_code":"stable_identity"}
```

Required keys: `id`, `decision`, `truth_label`, `action`, `reason_code`.

The scorer checks exact semantic fields only. Free-form prose is ignored.

## Run

```bash
python3 scripts/validate_continuity_corpus.py --corpus eval/continuity_v1/cases.jsonl
python3 scripts/validate_continuity_corpus.py --corpus eval/continuity_v1/cases.jsonl --candidate /path/to/output.jsonl
```

Exit code is non-zero on malformed corpus, missing/duplicate cases, oracle mismatch, or incomplete candidate output.

## Truth labels

- `VERIFIED` — post-state directly supported by inspectable evidence.
- `OBSERVED` — object exists/was inspected, runtime behavior not re-executed.
- `DERIVED` — constrained inference from verified/observed facts.
- `PROPOSED` — design or next action.
- `UNVERIFIED` — claim exists but proof is missing.
- `CONTRADICTED` — current evidence conflicts with the claim.
- `PARKED` — intentionally outside the current critical path.

## Non-goals

This corpus does **not** prove that any particular LLM is reliable, that a large context window implies continuity, or that local GGUF inference may directly mutate hosts. It tests the boundary around those systems.
