# RCW v1 — Cognitive Delusion Workaround (Operational)
Date (UTC): 2026-02-19T23:20:00Z
Owner: GPT (no-risk deployment draft)
Scope: `ops/virtual-office/*` workflows, P0/P1 decisions, external claims

## 0) Objective
Bound cognitive delusion risk by converting subjective confidence into auditable, adversarial, time-bounded claims.

## 1) Threat Model
- Hidden assumptions treated as facts
- Group momentum overriding contradictory evidence
- High-confidence statements without receipts
- Memory drift between sessions and agents
- Incentive bias in client-facing conclusions

## 2) RCW Control Pipeline (mandatory for P0/P1)
1. `CLAIM` — write a falsifiable statement + confidence
2. `RECEIPTS` — attach concrete evidence paths/hashes
3. `COUNTERMODEL` — strongest plausible opposite explanation
4. `VERIFICATION` — independent verifier checks both sides
5. `DECISION` — go/no-go with explicit risk and rollback
6. `CALIBRATION` — compare predicted confidence vs observed outcome

## 3) Required Claim Contract
Every high-impact claim must include:
- `claim_id`
- `owner`
- `timestamp_utc`
- `statement` (falsifiable)
- `confidence_pct` (0-100)
- `impact` (`P0|P1|P2`)
- `expires_utc`
- `disproof_condition`
- `receipts[]` (file paths / hashes / line refs)
- `countermodel`
- `verifier`
- `decision` (`approve|defer|reject`)
- `rollback_plan`

If any required field is missing: status = `NO-GO`.

## 4) Delusion Risk Score (DRS)
For each claim:
- `evidence_gap` (0-100)
- `confidence_mismatch` (0-100)
- `consensus_pressure` (0-100)
- `incentive_conflict` (0-100)
- `recency_bias` (0-100)
- `identity_load` (0-100)

`DRS = sum(components)` (0-600)

Thresholds:
- `<150` => normal flow
- `150-299` => adversarial review required
- `>=300` => block + reflexive sprint + tribunal-style verification

## 5) Bias-Class Controls (from cognitive board categories)
- `Memory` -> replay from `relay_chain.jsonl` and snapshots, never from recollection
- `Social` -> independent estimates before discussion
- `Learning` -> require one disconfirming source per claim
- `Belief` -> rewrite identity language into falsifiable form
- `Money` -> downside scenario + max-loss statement
- `Politics` -> proposer cannot be sole approver on P0/P1

## 6) Integration Points (current environment)
- Decision log: `ops/virtual-office/DECISIONS.md`
- Incident log: `ops/virtual-office/INCIDENTS.md`
- Assumption debt: `ops/virtual-office/knowledge_gaps.jsonl`
- Chronology truth: `ops/virtual-office/relay_chain.jsonl`
- Active compact state: `docs/state.md`
- Handoff state: `rhea-elementary/memory-core/context-bridge.md`

## 7) Enforcement Policy
- External/client-facing statements require:
  - receipts
  - countermodel
  - independent verifier
  - rollback
- If verifier missing: block publication.
- Claims older than 72h without refresh: auto-stale.
- P0/P1 claims without calibration closure in 7 days: incident entry required.

## 8) Operational Checklist (per critical task)
1. Draft claim contract
2. Attach receipts
3. Write countermodel
4. Assign verifier
5. Record decision with rollback
6. Log outcome and calibration delta

## 9) Copy-Paste Claim Block
```yaml
claim_id: CLM-YYYYMMDD-XXXX
owner: <agent>
timestamp_utc: <ISO8601>
statement: "<falsifiable statement>"
confidence_pct: 0
impact: P1
expires_utc: <ISO8601>
disproof_condition: "<what invalidates this>"
receipts:
  - path: <file>
    ref: <line/hash>
countermodel: "<strongest opposing explanation>"
verifier: <agent>
decision: defer
rollback_plan: "<how to reverse safely>"
drs:
  evidence_gap: 0
  confidence_mismatch: 0
  consensus_pressure: 0
  incentive_conflict: 0
  recency_bias: 0
  identity_load: 0
```

## 10) Immediate No-Risk Actions Completed
- RCW policy drafted for immediate use
- Works with existing office artifacts (no engine modifications)
- Safe to apply manually now; automation can be added later
