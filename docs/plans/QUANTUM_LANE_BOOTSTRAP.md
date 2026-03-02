# Quantum Lane Bootstrap (Aletheia-Class, not Full Pillar Yet)
Date: 2026-02-28
Owner: ORION
Status: Execution-ready

## 1) Decision
Adopt a staged path:
1. Create **Aletheia-Quantum lane** first (reproducible evidence lane).
2. Do **not** elevate to independent pillar (Ruliad/Aletheia parity) until hard reliability gates are met.

Reason:
- High scientific upside, but easy to produce non-reproducible "quantum theater".
- We prioritize auditability and proof receipts over marketing complexity.

## 2) Platform Review (Practical)
Scoring model (1-10):
- Scientific depth
- Engineering maturity
- Integration fit with Rhea
- Reproducibility friendliness

### Qiskit (IBM)
- Score: **8.6/10**
- Strength: mature transpiler/runtime stack, strong docs, strong ecosystem.
- Risk: API migration churn across major versions.
- Role in lane: **Primary baseline SDK**.

### CUDA-Q (NVIDIA)
- Score: **7.8/10**
- Strength: strong HPC/GPU hybrid simulations.
- Risk: heavier infra assumptions.
- Role in lane: performance tier (phase 2).

### PennyLane
- Score: **7.9/10**
- Strength: differentiable quantum workflows, hybrid ML experiments.
- Risk: can blur physics validity if used only as ML utility.
- Role in lane: optional QML track (phase 2/3).

### Cirq
- Score: **7.2/10**
- Strength: circuit-level control, clean abstractions.
- Risk: weaker fit as cross-provider default in this stack.
- Role in lane: secondary adapter.

### Amazon Braket SDK
- Score: **7.4/10**
- Strength: provider orchestration and managed jobs.
- Risk: cloud coupling/cost profile for always-on experimentation.
- Role in lane: execution backend bridge (phase 3).

### pytket / Quantinuum
- Score: **7.6/10**
- Strength: powerful compilation and optimization.
- Risk: narrower adoption footprint in this codebase today.
- Role in lane: optimization plugin after baseline.

## 3) What "Aletheia-Quantum" Means
Every run emits verifiable receipts, not just narrative outputs.

Required receipt fields:
1. circuit_hash (canonical serialization hash)
2. sdk + version
3. transpiler/config hash
4. backend id + mode (sim/hardware)
5. seed + shots
6. result digest + timestamp
7. provenance pointer (task id / commit / run id)

No receipt -> no claim.

## 4) 2-Week Bootstrap (Execution Plan)

### Week 1 — Baseline and Controls
1. Build minimal runner `quantum_lane/runner.py` with Qiskit simulator-first execution.
2. Add deterministic experiment templates:
- bell_state_baseline
- superposition_collapse_baseline
- entanglement_consistency_baseline
3. Emit JSON receipts to `logs/quantum_lane/*.jsonl`.
4. Add validator to reject runs missing required receipt fields.

Acceptance (Week 1):
- 100 reproducible local runs across 3 templates with fixed seeds.
- Receipt completeness = 100%.
- Drift on repeated fixed-seed run = 0 for digest-level checks.

### Week 2 — Bridge Integration + Governance
1. Add Rhea adapter endpoint for submitting lane runs and fetching receipts.
2. Integrate with TaskQueue and relay summaries.
3. Add governance gates:
- fail run if receipt invalid
- mark result "non-claimable" if backend metadata missing
4. Add docs/playbook entry for non-quantum users (why this matters, how to read outputs).

Acceptance (Week 2):
- End-to-end run from task -> receipt -> dashboard summary.
- P0 failure paths tested (invalid receipt, missing backend metadata).
- At least one iOS-safe compact summary payload generated for UI.

## 5) Promotion Gates to "Independent Pillar"
Do not promote until all are true:
1. >= 30 days stable operation.
2. >= 95% successful runs (excluding intentional fault tests).
3. Reproducibility audit passed by second agent lane (Hyperion).
4. Clear user value cases linked to economic impact metrics (F, m, a framing).

## 6) Risks and Controls
1. Risk: "Quantum theater" without scientific control.
- Control: receipts + deterministic baselines + validator hard-fail.
2. Risk: SDK ecosystem churn.
- Control: pinned versions + compatibility matrix.
3. Risk: cost explosion on hardware backends.
- Control: simulator-first, explicit budget gate, hardware opt-in only.

## 7) Immediate Next Actions
1. Create queue tasks for baseline runner, receipt schema, and integration endpoint.
2. Assign reproducibility audit to Hyperion.
3. Sync iOS lane with compact quantum summary contract (text-first, no cognitive overload).
