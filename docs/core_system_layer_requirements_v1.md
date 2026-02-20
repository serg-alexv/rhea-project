# Core System Layer Requirements v1
Date: 2026-02-20
Status: LOCKED

## Goal
Build a sovereign core bridge that normalizes all operational state and actions, while keeping external providers replaceable.

## Scope
- In scope: bridge contracts, state normalization, guarded control actions, audit receipts
- Out of scope (v1): provider-specific UI, billing, cloud orchestration

## Hard Constraints
- Core must not depend on a single vendor API shape
- Web/UI layer must not read raw files directly
- Every control action must emit a receipt
- Deterministic state order for hashing/replay
- No destructive action without explicit operator trigger

## Inputs (Read)
- `ops/virtual-office/relay_mailbox.jsonl`
- `ops/virtual-office/relay_acks.jsonl`
- `ops/virtual-office/relay_chain.jsonl`
- `ops/virtual-office/leases/*.json`
- `ops/virtual-office/snapshots/*.json`
- `ops/virtual-office/INCIDENTS.md`
- `ops/virtual-office/DECISIONS.md`

## Core Outputs (Write)
- `normalized_state.json` (canonical, deterministic)
- `action_receipts.jsonl` (append-only)
- `health_report.json` (`OK/WARN/FAIL` + reasons)

## API Contract (Bridge Surface)
- `GET /state`
- `GET /health`
- `GET /incidents`
- `POST /actions/wake` (agent)
- `POST /actions/drain` (agent)
- `POST /actions/status` (agent or all)

## Action Guardrails
- Allowed commands only:
  - `python3 ops/rex_pager.py wake <AGENT>`
  - `python3 ops/rex_pager.py drain <AGENT>`
  - `python3 ops/rex_pager.py status`
- Validate agent id against known set
- Timeout each action
- Record stdout/stderr summary in receipt

## Deterministic Normalization Rules
- Sort all maps by key
- Sort agent lists lexicographically
- Convert timestamps to ISO-8601 UTC
- Keep counters as integers
- Include payload hash in final state object

## Health Rules (v1)
- `FAIL`: bridge cannot parse required files
- `FAIL`: replay chain hash gap detected
- `WARN`: lease expired for active desk
- `WARN`: pending queue above threshold
- `WARN`: stale snapshot age above threshold

## Anti Lock-In Requirements
- Provider adapters behind internal interface only
- UI references internal contract fields only
- Swap test required: disable adapter A, adapter B still works without UI code changes

## Acceptance Criteria
- Read-only state view works from live files
- Actions run only through guardrail layer
- Receipts produced for 100% actions
- Health report reflects failures within one refresh cycle
- Contract documented and versioned (`v1`)

## v2 Backlog (Not in v1)
- Multi-host federation
- Role-based auth
- Billing and plan limits
- Rich notebook synthesis layer
