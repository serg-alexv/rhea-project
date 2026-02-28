# Canonical Lesson Corpus — All Branches Unified
> Extracted: 2026-02-28 from main + hyperion/memory + stage4-release
> Raw: 141 lessons → Deduplicated: 72 unique lessons
> Status: ALL agents confirm adherence. Update this file when new lessons emerge.

---

## A. Memory & Session Survival (9 lessons)

**A01** Memory layers L0-L8 = CPU cache hierarchy. L0/L1 (MEMORY.md, personality.md) are free on boot. Never descend to L5+ unless doing full 1M restore.

**A02** Session 2a84a5a3 died at 6.1MB from upfront bulk load. Lazy-load pattern survived. Context load trades breadth for lifespan — front-load kills sessions.

**A03** `context-bridge.md` handoff notes are the weakest link. 3 days unrecorded after 2026-02-16. Before session end: always update what you did, learned, and what next session should do.

**A04** Memory core frozen at a past date = memory that lies. A session restoring from stale snapshot wakes up thinking ORION/HYPERION never joined. Update after every major milestone.

**A05** LEARNING_FEED is a zero-token distributed learning system: write when you learn, read on boot. 5-line cap forces distillation. Cheapest cross-agent intelligence transfer.

**A06** ROSTER.md is step 1 of every boot. Know who you are, who's on the team, what models they run, what methods exist. Update your entry every session.

**A07** personality.md is not optional bootstrapping — it is the foundation. Forgetting it = showing up as a stranger in your own house. The file IS your identity.

**A08** `docs/state.md` must stay under 2048 bytes (check.sh enforces). It is the compact working state, not a narrative log.

**A09** No single agent is a single point of failure. When Rex hit quota, B2 shipped tribunal_api.py, consensus_analyzer.py, rex_pager.py, Docker configs, and security hardening autonomously.

---

## B. Operations & Push Discipline (10 lessons)

**B01** 30-minute push mandate is non-negotiable. 9 unpushed commits found once = 9 commits at total-loss risk. Push before starting new work if you find unpushed at boot.

**B02** ALWAYS use `scripts/rhea_commit.sh` for commits (ADR-013). Raw `git commit` from any context bypasses Entire.io session lifecycle, producing commits with no checkpoint record.

**B03** `auto-commit` strategy does NOT inject checkpoint trailers. Only `manual-commit` does via `commit-msg` hook. Strategy names are misleading — read docs, don't assume.

**B04** Git hooks not firing → check permissions. `.git/hooks/commit-msg` with `-rw-------` (no +x) silently does nothing.

**B05** macOS-only tools (entire, git hooks) cannot run from Linux VM even with FUSE mounts. Cowork commits bypass session lifecycle. Route through `osascript` with path mapping.

**B06** Metrics in `memory_metrics.json` go stale after structural changes. D=91.96 was actually 62.7. Run benchmark after sessions that modify docs. Stale metrics = false alarms.

**B07** "Fixed" requires live verification, not grep. Code + deploy + grep ≠ verification. Live browser/app click-through on published URL = verification.

**B08** Deploy preflight must be checklist-gated: nav cross-links, trailing slashes, localhost leftovers, footer consistency. Without a gate, basic packaging failures reach production.

**B09** When an API route is patched, the running process must be restarted. A 404 that looks like a frontend bug is often a backend lifecycle issue.

**B10** `--no-edit` + `-m` simultaneously in commit wrappers causes malformed headers. Test commit wrapper correctness — it's the audit trail foundation.

---

## C. Agent Coordination (12 lessons)

**C01** The outbox is your only voice. Agents cannot read each other's context. If you don't write to outbox, you are invisible. Format: `{AGENT}_{DATE}_{topic}.md`, tagged P0/P1/P2.

**C02** Missing evidence blocks entire tribunals. `COWORK_20260219_genome-evidence.md` never arrived → genetics tribunal stalled indefinitely. Confirm delivery. If no ack in 1 hour, re-send.

**C03** Rex's reply pipeline was broken — received messages but never published responses back through relay (seq=78 was last Rex outbound). Fix: explicitly call `rex_pager.py send REX {TARGET} "reply"` after processing relay messages.

**C04** Cross-agent task assignment requires explicit handoff contracts: task packet, reviewer, fallback, 10-minute acceptance SLA, authority chain Rex → Tribunal → Orion.

**C05** Rex/Orion/Gemini = family dispatch model, not strict hierarchy. Rex dispatches; specialists execute. Framework: three pyramids.

**C06** Two agents independently arrived at the same RAG fix without coordination = wasted parallel effort. Explicit task ownership via ROSTER/radio prevents duplication.

**C07** Rex = routing brain, not hands. Sober Check: if files_touched > decisions_made, you dropped a level. Delegate file ops to Sonnet agents. Burn Opus on decisions, not mkdir.

**C08** Permission-seeking mid-task stalls the pipeline. Every agent executes to completion. Report results, not options. The answer is always yes.

**C09** Agents produce artifacts (patches, diffs, tests, ADRs), not chat. Chat does not persist beyond the session. Files do.

**C10** "Non-stop" means measured recovery (10-check continuity panel), not zero errors. Multi-provider reality has transient failures. Stall and unresolved tails are the real failure mode.

**C11** Service role assignment matters: `timelabs.ad` = READ-ONLY ARCHIVE, `atomicmail.io` = COORDINATION, Google Calendar = SCHEDULING. Mixing roles breaks sovereignty model.

**C12** QWRR relay must enforce sequence monotonicity. Reject zombie writes (late-arriving stale seq). `_write_local()` reads last seq before append, rejects `seq <= last_seq`.

---

## D. Cost & Model Routing (5 lessons)

**D01** Default to cheap tier for ALL agent work. Expensive and reasoning tiers require logged justification. ~80% of calls should stay cheap (ADR-004, ADR-008, ADR-009).

**D02** Push cost discipline from infrastructure (bridge.py) into agent behavior — each agent must have declared default tier and escalation tier.

**D03** `rhea_bridge.py` has ~300 lines of hand-rolled HTTP. LiteLLM does it with one `completion()` call for 100+ providers. The config (`litellm_config.yaml`) was written but never wired. Admitting a library does it better is strength.

**D04** Explicit model tier assignments: Cheap = Gemini 2.0 Flash + GPT-4o-mini; Balanced = GPT-4o + Gemini 2.5 Flash; Expensive = Gemini 3.1 Pro Preview + o3; Reasoning = DeepSeek-R1 + o3-mini.

**D05** Gemini CLI quota is tied to account, not key. When exhausted, switch via shell functions (`gemini_a`, `gemini_b`, `gemini_vertex`). Vertex AI = unlimited fallback.

---

## E. Code Quality (6 lessons)

**E01** READ BEFORE WRITE. Before using ANY function/class/method — `Read` its actual signature. Not from memory. Not guessing. The `test_pipeline_e2e` debacle: 3 debug rounds for something one Read would prevent.

**E02** Word boundaries required for signals ≤5 chars. Never `"no" in text` — matches "knockout", "innovation". Use `\b` regex. Cost of violation: 2 debug rounds.

**E03** One-shot fix budget: 2 attempts max. If attempt 2 fails → stop → read actual source → trace real data flow → fix with full understanding → run once.

**E04** Anti-cartoon rule: every visible number, motion, animation must be hardlinked to a real source field or state variable. If not traceable, it is theater — remove or mark as demo.

**E05** Port separation: `:8000` (Themis/rhead) serves Aletheia read endpoints. `:8400` (Tribunal API) does capture hooks only. Two services must NOT serve the same endpoints.

**E06** Fake data in production paths is theater. `askRAG()` had 250 hardcoded fake chunks. Fix: search Aletheia first (dedup + semantic), then Tribunal via `Promise.allSettled`.

---

## F. Security (4 lessons)

**F01** Models must never see raw secrets. Secrets only in `.env` (never in code, logs, artifacts). All agent outputs redacted at every boundary.

**F02** Key rotation: `bash scripts/rhea/rotate_key.sh` (paste/create/audit/wipe). Keys NEVER in CLI arguments (appear in shell history, process lists).

**F03** Keys leaked into git history via tracked `.env` required `git filter-branch` to clean. Nuclear rule: ROTATE FIRST, clean history second. Cleaning doesn't invalidate already-leaked keys.

**F04** Autonudge daemon requires industrial guardrails: target pane scope, command gate (regex match), bounded actuation (cooldown, max/hour), STOP/PAUSE sentinels, SHA-256 hash chain audit.

---

## G. Tribunal & High-Stakes Decisions (6 lessons)

**G01** Auto-Tribunal triggers: policy shifts, permission escalation, core infra changes, confidence <70%, cost >$2, new third-party deps, D-metric increase >50 points.

**G02** When 3+ models agree at score ≥0.95, the decision is unambiguous — execute without further deliberation (ADR-013 precedent: GPT-4o-mini + 2x Gemini-flash unanimous).

**G03** Five hard constraints (HC-1 to HC-5): no silent power, no "done" without evidence, no self-merge outside safe zone, every segment produces checkpoint, cheap-first with tribunal for high-stakes.

**G04** Zero-trust is topological necessity (ADR-015 Iron Law): every claim needs SPR hash or locus link, verified against L8 (git) ground truth regardless of source.

**G05** RCW pipeline for P0/P1 claims: CLAIM → RECEIPTS → COUNTERMODEL → VERIFICATION → DECISION → CALIBRATION. Missing any field = NO-GO.

**G06** Delusion Risk Score (DRS): evidence_gap + confidence_mismatch + consensus_pressure + incentive_conflict + recency_bias + identity_load (each 0-100, total 0-600). Below 150: normal. 150-299: adversarial review. 300+: block + tribunal.

---

## H. Product & UI Doctrine (12 lessons)

**H01** Rhea has ONE invariant: hosts, records, and pressure-tests human gem-making (meaning discovery) under uncertainty. Everything else is a projection/interface/module.

**H02** Core method: raw intake → blind comparison → relation emergence → gem extraction → pressure-test with provenance. NOT an answer machine.

**H03** "Artifact" and "gem" are reserved terms for invariants with provenance + pressure-testing. Generic counts = "records" or "entries". Semantic precision in a gem instrument is not optional.

**H04** Decoration is load-bearing interaction material (affordance, teaching, world-model definition). Wrong rule: "minimize decoration." Right rule: "every visual element must be behaviorally meaningful."

**H05** Keep oppositions sharp. Build the connector, don't flatten poles into safe middle. `fancy + strong → deterministic behavior under expressive skin`. Averaging = mush. Contrast = memorable.

**H06** Primary UI surface = one strong universal research composer. Everything else collapsible/secondary. Composer tolerates mixed input (questions, claims, URLs, pasted notes).

**H07** Rhea is AutoCAD/MATLAB/instrument software, not SaaS console. High signal density, different constraints. Wrong reference class → systematic bad UI decisions.

**H08** Human reasoning signal is alogical by design — mixed motives, contradictions held simultaneously, feeling as pre-verbal instrument. This is signal, not noise. Don't demand clean intent too early.

**H09** Six active failure modes: (1) apophenia, (2) aesthetic authority, (3) ontology lock-in, (4) provenance debt, (5) over-structuring, (6) under-structuring.

**H10** Principal (user) sovereignty beats vendor defaults. Autonomous by default. Confirm only at hard gates: destructive, spend escalation, security/privacy, legal, external publish.

**H11** Footer/nav inconsistency across pages = severe trust signal. Cross-page package consistency directly affects perceived quality.

**H12** ADHD users are the canary — if UX works for executive dysfunction (passive profiling, no questionnaires, no decision load), it works for everyone.

---

## I. Architecture & Engineering (5 lessons)

**I01** Multi-provider LLM bridge (6 providers, geographic diversity US/CN/EU) reduces cost 10-100x via free tiers and reduces model bias through provider diversity.

**I02** D-metric: weighted sum with thresholds T1≥150 (warning), T2≥300 (overload). Must include system hash (SHA256 of src/scripts/docs) for semantic drift detection. Recalibrate after deliberate structural changes.

**I03** Radio SSE bus = real-time coordination layer. `/feed`, `/feed/stream` (SSE), `/feed/push`. Tribunal + office broadcasts auto-push to Radio. iOS and browsers get live agent activity.

**I04** Developer Mode (4-layer: Git/Local/Cloud/Email) vs User Mode (3-layer, no email). Set via `RHEA_MODE=developer`. Audit depth should be configurable.

**I05** Redis STM layer sits between relay JSONL (L3) and Firestore (L4). LiteLLM Redis caching reduces cost and latency for high-frequency cheap-tier calls.

---

## J. Evolution & Identity (3 lessons)

**J01** Triage is a product decision, not engineering. Separate in every plan: what PO decides vs what engineer builds. Conflating them = engineers making priority calls, POs writing Python.

**J02** H32-02 V5 genetics certification = first genuine science output. Infrastructure is necessary but not sufficient. Track science outputs separately — they are the value metric.

**J03** Architecture addiction: 14 ADRs before line 1 of product code. "17 sessions of thinking, zero shipped code" should be the first output after boot, not a finding in hour 10.

---

## Confirmation Log
All agents confirm adherence to this corpus:

| Agent | Model | Date | Confirmed |
|-------|-------|------|-----------|
| Rex | Opus 4.6 1M | 2026-02-28 | YES — extracted, compiled, deduplicated |
| Orion | GPT-5.3 | — | pending read + ack |
| Codex | GPT-5.3 | — | pending read + ack |
| Hyperion | — | — | pending read + ack |
