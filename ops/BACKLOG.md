# BACKLOG (canonical)
> Seeded: 2026-02-16 by Human
> Managed by: LEAD

## P0 -- Must ship (stability then shipping)

- **RHEA-BRIDGE-001** | Add bridge call ledger (jsonl) | Desk: OPS
  Output: logs/bridge_calls.jsonl schema + write path in rhea_bridge.py
  DoD: every call logs provider, model, tokens, latency, status, and error; daily summary script exists.
  **Status: ✅ DONE** — agent ops-fixer-bridge-logging added +272 lines, price table, daily-summary command.

- **RHEA-BRIDGE-002** | Provider health probe | Desk: OPS
  Output: ops/bridge-probe.sh + docs/procedures/auth-errors.md
  DoD: one command prints status table; categorizes 401/402/404/429/400; links to procedures.
  **Status: PARTIAL** -- probe script exists (8.7 KB), runs but env loading broken (pyenv hashlib). Procedures doc missing.

- **RHEA-OFFICE-001** | Office protocol hardening | Desk: LEAD
  Output: ops/virtual-office/OFFICE.md updated with invariant rules
  DoD: defines canonical truth, inbox/outbox SLA, promotion rules (chat→procedure/gem/incident).
  **Status: PARTIAL** -- OFFICE.md exists with protocol. Missing: SLA, promotion rules, canonical-truth definition.

- **RHEA-PUB-001** | Public output conveyor | Desk: LEAD
  Output: PUBLIC_OUTPUT.md + docs/public/ seed
  DoD: daily-artifact rule; first artifact exported (article repack or probe tool).
  **Status: ✅ DONE** — PUBLIC_OUTPUT.md + docs/public/multi-model-bridge-article.md published.

## P1 -- Context system (freeze-killer)

- **RHEA-CTX-001** | TODAY_CAPSULE generator (routes) | Desk: GPT
  Output: ops/outbox/TO_GPT_generate-paste-blocks.md → inbox result
  DoD: LEADERS / WORKERS / OPS blocks generated deterministically from TODAY_CAPSULE.
  **Status: 🔲 TODO**

- **RHEA-CTX-002** | Gems ledger w/ IDs | Desk: LEAD
  Output: ops/virtual-office/GEMS.md with ID format + promotion rule
  DoD: every gem is 1–2 lines + why/used_by; TODAY_CAPSULE references IDs only.
  **Status: PARTIAL** -- GEMS.md exists with 5 gems + IDs. Missing: promotion rule, used_by field.

- **RHEA-INC-001** | Incident template & resurrection protocol | Desk: LEAD
  Output: ops/virtual-office/INCIDENTS.md structure with INC-YYYY-MM-DD-NN IDs
  DoD: each incident has symptom/cause_guess/fix/verify/rollback/next_test.
  **Status: PARTIAL** -- INCIDENTS.md exists with 5 incidents. Missing: full template fields, dated IDs, verify/rollback/next_test.

## P2 -- iOS offline-only reboot scaffolding

- **RHEA-IOS-001** | ARCHITECTURE_FREEZE.md | Desk: LEAD
  Output: ARCHITECTURE_FREEZE.md at repo root
  DoD: core/ui boundaries, naming, folder structure, persistence strategy.
  **Status: 🔲 TODO**

- **RHEA-IOS-002** | Offline loop MVP spec → tasks | Desk: GPT
  Output: breakdown into 10–15 implementable issues
  DoD: each issue has acceptance criteria; no "research-only" tasks.
  **Status: 🔲 TODO**

## P3 -- Community growth

- **RHEA-COMM-001** | Repo narrative reboot | Desk: LEAD
  Output: VISION.md, WHY_NOW.md, COMMUNITY.md, LEARNING_PATH.md
  DoD: short, 2026-credible, no overclaims, clear contribution paths.
  **Status: 🔲 TODO**

- **RHEA-COMM-002** | Blueprint Literacy ladder | Desk: GPT
  Output: 8–12 micro-lessons + unlock map
  DoD: each lesson 2--4 min; ties to safety constraints and loop variables.
  **Status: 🔲 TODO**

## Summary
| Status | Count |
|--------|-------|
| ✅ DONE | 2 |
| ⚠️ PARTIAL | 4 |
| 🔲 TODO | 5 |
