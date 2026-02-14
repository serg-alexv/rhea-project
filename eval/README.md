# Rhea — Evaluation Suite

> Purpose: Detect regression, measure improvement, validate self-upgrade techniques.

## Structure

```
eval/
├── README.md           ← this file
├── tasks/              ← YAML task definitions with expected outputs
│   ├── memory_recall.yaml
│   ├── schedule_generation.yaml
│   └── tribunal_consensus.yaml
└── results/            ← timestamped run results (gitignored if large)
```

## How to Run

### Manual (current)
1. Pick a task from `eval/tasks/`
2. Feed the `prompt` to the appropriate agent/model
3. Compare output against `expected_output` or `rubric`
4. Log pass/fail + score in `eval/results/`

### Automated (future — Phase 3+)
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

- Binary tasks: pass (1.0) or fail (0.0)
- Rubric tasks: weighted sum of criteria (0.0–1.0)
- Regression threshold: if score drops >10% from baseline, flag for review

## Relation to Memory Benchmark

The memory benchmark (`scripts/memory_benchmark.sh`) tests structural integrity.
The eval suite tests functional correctness — can Rhea actually produce good outputs?
Both should pass before any release or major refactor.
