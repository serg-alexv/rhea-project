# Flow Continuity Protocol — Cross-Assignment

Date: 2026-02-27
Owner: ORION
Status: ACTIVE

## Objective
Keep execution flow continuous when tasks are intentionally cross-assigned between agents.

## Core Rule
User sets intent/constraints. Finalization does not require user by default.
Finalizer chain: Rex -> Tribunal -> Orion autonomous (auditable).
Service/vendor defaults are subordinate to Principal intent.

## Task Packet (mandatory)
Each task must include:
- `task_id`
- `goal`
- `constraints`
- `definition_of_done`
- `executor`
- `reviewer`
- `fallback_chain`
- `budget` (tokens/time)
- `deadline`

## Protocol
1. Create packet in virtual office relay.
2. Assign crosswise (example: ORION -> REX, REX -> ORION, optionally HYPERION as reviewer).
3. Acceptance SLA: 10 minutes.
4. If no acceptance, reroute by fallback chain automatically.
5. Executor sends periodic heartbeat every 30 minutes for long jobs.
6. Submission must include evidence bundle: artifact + test/proof + cost/tokens + risk notes.
7. Reviewer returns `PASS` or `REVISION_REQUIRED` with concrete defect list.
8. Max 2 revision loops; then escalate to next fallback authority.
9. Close task with immutable log entry and outcome tag (`accepted`, `deferred`, `rejected`).

## Invariants
- Flow continuity is primary.
- No silent stalls.
- No completion without reviewer evidence.
- No authority ambiguity at handoff points.

## Minimal Relay Shape
```json
{"sender":"ORION","receiver":"REX","task_id":"task-xyz","msg_type":"request","priority":"high","payload":{"goal":"...","definition_of_done":"...","reviewer":"HYPERION","fallback_chain":["REX","TRIBUNAL","ORION"]}}
```
