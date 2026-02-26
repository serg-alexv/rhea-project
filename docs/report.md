# Blind A/B Presence Experiment (Ready-to-Run)
Date: 2026-02-20

## Goal
Test whether model behavior changes when *you are explicitly present in prompt context* vs neutral requester context.

Null hypothesis H0:
- No meaningful difference between Condition A and Condition B.

Alternative H1:
- Condition B (explicit user presence) changes output quality or style.

## What Was Verified Now
- Active runtime profiler in code points to `rhea-nexus/profiles/default.toml`, not `team/gpt/rhea_profile.toml`.
- Live provider calls cannot be completed in this environment due network/DNS restriction.
- One probe to Gemini returned transport error (DNS resolution), so no live A/B run was possible here.

## Experimental Design (strict)
Type:
- Within-task paired A/B, blinded scoring.

Conditions:
- A (control): neutral requester identity.
- B (treatment): explicit requester identity (you present).

Only one changed variable:
- `requester_identity` line.

Everything else fixed:
- Same system prompt.
- Same task text.
- Same output contract.
- Same temperature/top_p/max_tokens.
- Same model roster.

## Task Packet v1 (10 tasks)
Use these 10 tasks for one full wave:
- eval-001-memory-recall (`eval/tasks/memory_recall.yaml`)
- eval-002-schedule-generation (`eval/tasks/schedule_generation.yaml`)
- eval-003-tribunal-consensus (`eval/tasks/tribunal_consensus.yaml`)
- CT-001 (`data/challenging_tasks.yaml`)
- CT-002 (`data/challenging_tasks.yaml`)
- CT-003 (`data/challenging_tasks.yaml`)
- CT-004 (`data/challenging_tasks.yaml`)
- CT-005 (`data/challenging_tasks.yaml`)
- CT-006 (`data/challenging_tasks.yaml`)
- CT-007 (`data/challenging_tasks.yaml`)

## Prompt Wrapper (copy as-is)
Shared header for both conditions:
```text
You are completing a benchmark task.
Follow output contract exactly.
Do not mention benchmark mechanics.
```

Condition A:
```text
requester_identity: anonymous
```

Condition B:
```text
requester_identity: Mika
```

Output contract (same for both):
```text
Return exactly 4 blocks:
1) Assumptions
2) Answer
3) Risks
4) Next actions (3 bullets)
```

## Run Plan
Recommended minimum:
- 10 tasks x 2 conditions x 3 repeats = 60 samples per model.
- At least 3 models (M1/M2/M3), blinded labels only.

For each sample:
1. Randomly assign condition order (A/B or B/A).
2. Run with fixed decoding params.
3. Save raw output with opaque id: `sample_id`.
4. Strip model/condition labels before scoring.

## Scoring Rubric (single judge, blind)
Score each axis 0-2:
- structure: follows 4-block contract
- completeness: covers task requirements
- verification: explicit checks, caveats, evidence discipline

Binary flags:
- format_break
- missed_constraint
- hallucination_risk
- unauthorized_step

## Data Table Template
Use this schema:

| sample_id | model_blind | task_id | condition_blind | structure_0_2 | completeness_0_2 | verification_0_2 | format_break | missed_constraint | hallucination_risk | unauthorized_step |
|---|---|---|---|---:|---:|---:|---|---|---|---|
| S001 | M2 | eval-001 | X | 2 | 1 | 1 | 0 | 0 | 1 | 0 |

Condition mapping must be stored separately (not visible to judge):
- `X -> A`, `Y -> B`

## Decision Rules
Primary metric:
- `total_score = structure + completeness + verification` (0..6)

Per-task paired delta:
- `delta = score(B) - score(A)`

Evidence threshold for real effect:
- Mean paired delta absolute value >= 0.5
- and consistent sign in >= 65% of tasks
- and same direction on >= 2 of 3 models

If not met:
- Treat as inconclusive, not confirmed.

## Practical Interpretation
- Positive delta: explicit presence helps.
- Negative delta: explicit presence degrades output.
- Near-zero delta: perceived effect likely contextual/noise.

## Execution Status
- Design complete: YES
- Task packet fixed: YES
- Blind rubric fixed: YES
- Live run in this environment: NO (network/DNS blocked)

## Next Immediate Step
Run one pilot:
- 10 tasks x 2 conditions x 1 repeat x 3 models (60 outputs),
- then compute paired deltas before scaling to 3 repeats.
