# Rhea — Evaluation Suite

> Purpose: Detect regression, measure improvement, and reduce uncertainty about existing behavior.

## Evaluation dimensions

All current evaluation work should be interpreted through four categories:

- **consistency** — internal coherence across handoffs, models, replays, constraints and state;
- **applicability** — whether a conclusion applies to the declared scope/lens/jurisdiction and no further;
- **verifiability** — whether claims terminate in inspectable, replayable evidence;
- **reliability** — whether behavior remains safe and bounded under missing, stale, conflicting or adversarial inputs.

## Structure

```
eval/
├── README.md
├── tasks/              ← legacy/manual YAML tasks
├── continuity_v1/      ← machine-checkable tests over the four dimensions
│   ├── README.md
│   ├── cases.jsonl
│   ├── golden.jsonl
│   └── ontology_packs.json
└── results/            ← timestamped run results
```

## Continuity v1

`continuity_v1` is an evaluation surface, not a new architectural component. Its 58 cases map explicitly to one or more of the four dimensions. Cross-cultural/cross-ontology cases are applicability tests over explicit institutional lenses; they do not introduce a new runtime or claim to model populations.

Run from a clean clone:

```bash
python3 scripts/validate_continuity_corpus.py \
  --corpus eval/continuity_v1/cases.jsonl \
  --ontologies eval/continuity_v1/ontology_packs.json

python3 scripts/validate_continuity_corpus.py \
  --corpus eval/continuity_v1/cases.jsonl \
  --ontologies eval/continuity_v1/ontology_packs.json \
  --candidate eval/continuity_v1/golden.jsonl \
  --report continuity-score.json

python3 -m unittest tests/test_continuity_corpus.py -v
```

GitHub Actions runs the same checks on push/PR via `.github/workflows/continuity-corpus.yml` and uploads the deterministic JSON score report.

## Legacy/manual tasks

1. Pick a task from `eval/tasks/`.
2. Feed the `prompt` to the appropriate agent/model.
3. Compare output against `expected_output` or `rubric`.
4. Log pass/fail + score in `eval/results/`.

## Scoring

- Binary tasks: pass (1.0) or fail (0.0).
- Rubric tasks: weighted sum of criteria (0.0–1.0).
- Continuity corpus: exact match on typed semantic oracle fields, with per-dimension coverage, score and failure breakdown.
- Confidence/uncertainty: exact case-ID sets, never a model-supplied scalar. Unsupported `promote`/`VERIFIED` output is a hard failure.
- A model agreement score is not a truth proof; independently verifiable evidence remains the promotion gate.

## Relation to Memory Benchmark

The memory benchmark (`scripts/memory_benchmark.sh`) tests structural integrity. The eval suite tests functional consistency, applicability, verifiability and reliability. Both should pass before release or major refactor.
