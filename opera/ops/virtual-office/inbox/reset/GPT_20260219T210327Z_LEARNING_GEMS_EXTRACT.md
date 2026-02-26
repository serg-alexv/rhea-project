# LEARNING GEMS EXTRACT — rhea-elementary + rhea-advanced + docs

Generated: 2026-02-19T21:03:27Z
Scope: `rhea-elementary/`, `rhea-advanced/`, `docs/`

## A) rhea-elementary gems (01-10)
1. Finite context windows imply rolling-memory TTL (`TTL ~= W / token_rate`). Source: `rhea-elementary/01_context_vs_memory.md`.
2. External memory removes storage TTL but not retrieval bottlenecks. Source: `rhea-elementary/01_context_vs_memory.md`.
3. Build systems to be verifiable, not trusted. Source: `rhea-elementary/02_verifiable_not_trusted.md`.
4. Every durable fact/decision/plan needs provenance receipts. Source: `rhea-elementary/03_receipts_and_provenance.md`.
5. Firestore is a DB/buffer, not a queue; add leases + idempotency to make it safe. Source: `rhea-elementary/04_firestore_as_fast_memory.md`.
6. Job docs must carry retry/concurrency controls (`idempotencyKey`, `leaseUntil`, `attempt`). Source: `rhea-elementary/05_job_doc_schema.md`.
7. Drafts must pass two-phase promotion: Draft -> Verified -> Artifact. Source: `rhea-elementary/06_two_phase_promotion.md`.
8. Invariants are first-class and testable (not prose-only principles). Source: `rhea-elementary/07_invariants.md`.
9. Planner / Executor / Verifier roles must be separated by interface contract. Source: `rhea-elementary/09_planner_executor_verifier_roles.md`.
10. MVP readiness is acceptance-check driven with explicit test method + expected outcome. Source: `rhea-elementary/10_mvp_acceptance_checks.md`.

## B) rhea-advanced gems (11-20)
11. Event sourcing with append-only truth + projections prevents memory drift. Source: `rhea-advanced/11_event_sourcing_memory.md`.
12. Hash-chained audit logs make tampering detectable if canonical JSON is stable. Source: `rhea-advanced/12_hash_chained_audit_log.md`.
13. Assume at-least-once delivery; get exactly-once effects through idempotency + leases. Source: `rhea-advanced/13_queue_semantics_and_idempotency.md`.
14. Tool authorization must be default-deny and policy-evaluated per call. Source: `rhea-advanced/14_policy_engine_tool_auth.md`.
15. Retrieval quality must be measured (recall@k, precision@k, MRR, faithfulness, citation coverage). Source: `rhea-advanced/15_retrieval_evaluation.md`.
16. Sandboxed execution must be read-only by default with strict allow-lists and no network unless required. Source: `rhea-advanced/16_sandboxed_execution.md`.
17. Models should never receive raw secrets; use scoped/short-lived credentials via tooling boundary. Source: `rhea-advanced/17_secrets_kms.md`.
18. Agent systems need SLOs and alerting, not just logs. Source: `rhea-advanced/18_observability_slos.md`.
19. Red-team tests must target injection, idempotency bypass, artifact poisoning, and tool escalation. Source: `rhea-advanced/19_adversarial_testing.md`.
20. CRDT is for genuine multi-writer concurrency; otherwise prefer single-writer simplicity. Source: `rhea-advanced/20_crdt_concurrent_edits.md`.

## C) docs gems (high-signal)
21. Workspace/state-first memory is more robust than infinite chat history. Source: `docs/memory_mamaging2025-2026.md`.
22. Memory operations should be explicit (`STORE/RETRIEVE/UPDATE/SUMMARIZE/DISCARD`) and audited with "why". Source: `docs/memory_mamaging2025-2026.md`.
23. Retrieval must be gated per turn; cross-domain recall should be blocked by default. Source: `docs/memory_mamaging2025-2026.md`.
24. Use revisitable pointers to avoid summary-loss corruption. Source: `docs/memory_mamaging2025-2026.md`.
25. Do not brain-swap an agent under quota walls; preserve identity and add relay+resurrection infrastructure. Source: `docs/qwrr-layer.md`.
26. QWRR bank-grade invariants: no loss, in-order delivery, idempotent effects, STOP survives downtime, no zombie writes. Source: `docs/qwrr-layer.md`.
27. Use a strict envelope (`seq`, `idempotency_key`, `ttl`, `lease_token_required`) for replay-safe operations. Source: `docs/qwrr-layer.md`.
28. Dangerous actions should be effect intents with receipts, not direct mailbox side-effects. Source: `docs/qwrr-layer.md`.
29. Hard constraints: no silent power, no done without verification, no self-merge in risky zones, checkpoint every segment. Source: `docs/CORE_RULES.md`.
30. Budget policy: cheap-first routing; escalate with rationale; tribunal for high-stakes changes. Source: `docs/CORE_RULES.md`.
31. Failure-memory loop: capture root cause + fix + lesson to prevent repeated mistakes. Source: `docs/reflection_log.md`.
32. Lifecycle-dependent tooling must be verified in every execution context (Cowork vs Claude Code mismatch is a real failure mode). Source: `docs/reflection_log.md`.
33. VM/macOS boundary is operationally critical; macOS-only toolchains require host execution paths. Source: `docs/reflection_log.md`.
34. Operational rules that prevent drift: no-output-is-failure, Questions Gate, repetition -> GEM/PROCEDURE. Source: `docs/public/QUICKSTART.md`.
35. Token efficiency: lazy retrieval (MCP/llms index) beats repeated full-doc loads. Source: `docs/TOKEN_OPTIMIZATION.md`.
36. Keep always-loaded memory concise and high-signal (`MEMORY.md` as bootstrap cache). Source: `docs/TOKEN_OPTIMIZATION.md`.
37. Design principles for product behavior: ADHD-default, passive-over-active sensing, body-before-mind routines, minimum effective dose. Source: `docs/architecture.md`.
38. Cultural and biological framing gem: if an intervention must be bought/scheduled, it likely reconstructs an ancestral default. Source: `docs/core_context.md`.
39. Typed event contracts reduce drift: fixed `event_type`, versioned schema, and traceability fields per event. Source: `docs/event_types.md`.

## Notes
- This extract favors engineering-operational gems over narrative/marketing copy.
- Firestore office channel is permission-blocked on this host (HTTP 403), so pager+inbox relay used.
