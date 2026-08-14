# Rhea — Evaluation Suite

> Purpose: Detect regression, measure improvement, validate self-upgrade techniques.

## Structure

```
eval/
├── README.md           ← this file
├── tasks/              ← legacy/manual YAML tasks
├── continuity_v1/      ← machine-checkable continuity + semantic-boundary corpus
│   ├── README.md
│   ├── cases.jsonl
│   └── golden.jsonl
└── results/            ← timestamped run results (gitignored if large)
```

## Continuity Corpus v1

The new `continuity_v1` slice is the first eval surface whose oracle is deliberately outside the model. It tests identity/intent preservation, evidence and provenance, contradictions, deterministic replay, stale-data behavior, capability boundaries, rollback, blind multi-model independence, long-context retrieval gaps, and local GGUF/llama.cpp semantic-contract portability.

Run it from a clean clone:

```bash
python3 scripts/validate_continuity_corpus.py --corpus eval/continuity_v1/cases.jsonl
python3 scripts/validate_continuity_corpus.py --corpus eval/continuity_v1/cases.jsonl --candidate eval/continuity_v1/golden.jsonl
```

GitHub Actions runs the same checks on push/PR via `.github/workflows/continuity-corpus.yml`.

## Legacy/manual tasks

1. Pick a task from `eval/tasks/`.
2. Feed the `prompt` to the appropriate agent/model.
3. Compare output against `expected_output` or `rubric`.
4. Log pass/fail + score in `eval/results/`.

### Planned generic automation

```bash
python3 scripts/rhea_eval.py --task eval/tasks/memory_recall.yaml
```

## Task YAML Format

```yaml
id: unique-task-id
name: Human-readable name
category: memory | reasoning | scheduling | tribunal | integration
difficulty: easy | medium | hard | expert
prompt: "The exact prompt to send"
expected_output: "What correct output looks like (or null if rubric-based)"
rubric:
  - criterion: "Mentions X"
    weight: 0.3
  - criterion: "Correct calculation"
    weight: 0.7
model_tier: cheap | balanced | expensive | reasoning
timeout_seconds: 30
tags: [tag1, tag2]
```

## Scoring

- Binary tasks: pass (1.0) or fail (0.0).
- Rubric tasks: weighted sum of criteria (0.0–1.0).
- Continuity corpus: exact match on typed semantic oracle fields.
- Regression threshold for legacy scored tasks: if score drops >10% from baseline, flag for review.

## Relation to Memory Benchmark

The memory benchmark (`scripts/memory_benchmark.sh`) tests structural integrity.
The eval suite tests functional correctness and continuity semantics.
Both should pass before any release or major refactor.
