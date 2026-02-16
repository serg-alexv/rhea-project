# Rhea -- Pitch Deck

> An Office OS for AI Agents
> Git-backed coordination. Protocol-driven memory. Provider-agnostic.

---

## Slide 1: Multi-Agent Work Is Broken

Every team using AI agents hits the same wall:

- **Fragile chats.** Session dies, context gone. No continuity between runs.
- **No memory.** Agent #2 does not know what Agent #1 discovered. Copy-paste is the "integration layer."
- **Provider deaths.** API key expires, rate limit hits, model deprecated -- entire workflow stops.

This is not a tooling problem. It is an architectural problem. Chat-based agents have no shared state, no persistence, no fault tolerance.

---

## Slide 2: What We Lose

Measured cost of the current approach:

- **28 session deaths** in the first month of building Rhea. Each one destroyed 2-20 hours of accumulated context.
- **70% of every session** spent on "remembering" -- re-reading docs, re-establishing context, re-discovering decisions already made (ADR-007 measurement).
- **Zero reproducibility.** Two runs of the same prompt on the same model produce different coordination outcomes. No way to audit why.
- **17 sessions of thinking, zero shipped code** -- the most honest self-diagnosis in the project (GEM-005). Pure ideation without execution discipline.

The problem compounds: the more agents you add, the worse coordination gets.

---

## Slide 3: Rhea = Office OS for Agents

Rhea treats agent coordination like an office, not a chatroom.

| Concept | Analogy | Implementation |
|---------|---------|----------------|
| Desks | Workstations | Named agent slots with heartbeat monitoring |
| Inbox/Outbox | Mail system | File-based message routing with SLA enforcement |
| Capsule | Daily standup | `TODAY_CAPSULE.md` -- what matters right now |
| Gems | Idea notebook | Insights captured, tagged, promoted when proven |
| Incidents | Bug tracker | Breakages tracked with symptoms, root cause, workaround, status |
| Decisions | Decision log | Every choice recorded with rationale and owner |
| Procedures | SOPs | Battle-tested fixes promoted from repeated gems |

**Key property:** Everything is a file. Files live in git. Git is the audit trail. If it is not committed, it did not happen.

---

## Slide 4: Architecture

```
ops/virtual-office/
  inbox/          -- agents drop results here
  outbox/         -- LEAD routes tasks to specific desks
  TODAY_CAPSULE.md
  GEMS.md
  INCIDENTS.md
  DECISIONS.md

ops/rhea_firebase.py   -- real-time sync (Firebase Realtime DB)
src/rhea_bridge.py     -- multi-provider LLM abstraction
docs/procedures/       -- battle-tested SOPs
```

**Dual transport:**
1. **File-based** (`virtual-office/inbox/outbox/`) -- works offline, survives any outage, git-backed
2. **Firebase** (`rhea_firebase.py`) -- real-time heartbeats, cross-terminal messaging, sub-second propagation

**Active desks (observed 2026-02-16):** 4 concurrent agents across 4 terminals (Opus LEAD, B-2nd, ChatGPT 5.2, Cowork Argos) plus on-demand Sonnet workers.

---

## Slide 5: The Protocol

Knowledge flows through a promotion chain:

```
observation (any agent, any session)
  |
  v  (repeated 2x)
GEM -- tagged insight with source and date
  |
  v  (referenced 3x in capsules or decisions)
PROCEDURE -- exact commands, verify step, rollback plan
  |
  v  (fails 2x)
INCIDENT -- symptoms, root cause, workaround, status
  |
  v  (resolved + verified)
DECISION -- what we learned, who decided, reversibility
```

**Why this matters:** Knowledge is not stored -- it is promoted based on evidence. An idea that never gets referenced stays a gem. A fix that keeps breaking gets escalated. Decisions carry provenance.

Currently operational: 7+ gems, 5 tracked incidents, 7 decisions, 3 procedures -- all produced in a single day of multi-agent work (2026-02-16).

---

## Slide 6: Survival Proof

Timeline of the first month:

| Event | Count | Evidence |
|-------|-------|----------|
| Session deaths (terminal crash, API failure, context overflow) | 28+ | Git log, state_full.md |
| First session that survived via trinity memory (3-file restore) | 1 | GEM-002: tested with fresh Haiku agent, 6/6 context questions correct |
| Multi-agent office stood up in a single day | 1 | 2026-02-16: 4 desks, 8 tasks completed, 5 incidents tracked |
| Context overhead reduced | 70% to ~5% | ADR-007: three-tier memory (git + entire.io + compact protocol) |
| Background agent death rate | 11/11 failed | INC-001: led to DEC-001 (foreground-only) |
| Foreground agent success rate | 14/14 succeeded | Same incident report |

**Working theory:** File-based coordination with git-backed persistence is more robust than session-based agent coordination. Evidence so far supports this but the sample size is small (1 project, 1 month, 1 operator). More data needed.

---

## Slide 7: The Bridge

`rhea_bridge.py` -- multi-provider LLM abstraction layer.

| Dimension | Spec |
|-----------|------|
| Providers | 6 (OpenAI, Gemini, DeepSeek, OpenRouter, HuggingFace, Azure AI Foundry) |
| Models | 31 models across 4 cost tiers |
| Routing | Cheap-first default (ADR-008). ~80% of calls stay on cheapest tier. |
| Tribunal mode | 3-5 independent models vote on the same question. Consensus synthesized. |
| Health probe | `ops/bridge-probe.sh` -- per-provider liveness check with error categorization (401/402/404/429/400) |
| Cost tracking | Per-call logging to `.entire/logs/ops.jsonl` |
| Geography | US (OpenAI, Gemini), CN (DeepSeek), EU (OpenRouter, HuggingFace), mixed (Azure) |

**Observed resilience (2026-02-16):** Bridge started at 2/6 providers live. Diagnosed and recovered to 4/6 within the same session. Remaining 2 have documented fix paths in `docs/procedures/auth-errors.md`. System never stopped working because cheap tier always had at least 3 candidates available.

---

## Slide 8: Context Tax Collector

> "Every time you copy-paste something twice in a day, it becomes a Gem or a Procedure." -- GEM-001 (from ChatGPT 5.2)

The Context Tax Collector is a working theory for automated knowledge promotion:

1. **Detect repetition** -- scan capsules, inbox messages, and session logs for patterns that appear 2+ times
2. **Promote to Gem** -- tag it, date it, source it
3. **Promote to Procedure** -- when a Gem is referenced 3x, formalize it with exact commands, verify step, rollback plan
4. **Measure compression** -- track how many tokens are saved per session by having a Procedure instead of re-explaining from scratch

**Status:** The protocol is defined and manually operational (GEM promotion rule in GEMS.md, procedure format in `docs/procedures/`). Automated detection is not yet built. This is experimental.

**Working theory:** Over a week of consistent use, the system becomes lighter automatically -- repetition triggers abstraction, abstraction reduces context load. Unproven at scale.

---

## Slide 9: What Is Working Today

Verified operational as of 2026-02-16:

| Component | Status | Evidence |
|-----------|--------|----------|
| Virtual office with 4 active desks | Running | OFFICE.md, Firebase heartbeats |
| File-based inbox/outbox with SLA | Active | 10+ messages routed in first day |
| Firebase real-time sync | Live | `ops/rhea_firebase.py` -- heartbeat, send, inbox, gem, status commands |
| Bridge with 4/6 providers live | Operational | `ops/bridge-probe.sh` output |
| Promotion protocol (gem to procedure) | Active | 7 gems captured, 3 procedures formalized |
| Incident tracking with structured format | Active | 5 incidents tracked, 1 resolved, 4 with workarounds |
| Decision log with rationale | Active | 7 decisions recorded with "who" and "why" |
| Trinity memory (3-file crash recovery) | Proven | GEM-002: fresh agent restored context from 3 files alone |
| Today capsule (daily state) | Updated | Human sleeping, agents autonomous |
| 14 ADRs, 2 Tribunal verdicts | Recorded | `docs/decisions.md`, `docs/tribunal_001_autocommit.md`, `docs/tribunal_002_memory_architecture.md` |

---

## Slide 10: Roadmap

### Near-term (weeks)

- **Office OS public release** -- clean up virtual-office protocol, publish as reproducible pattern
- **Bridge measurability** -- per-call cost tracking, latency dashboards, provider health SLA
- **Automated Context Tax Collector** -- detect repetition across sessions, auto-promote to gems/procedures

### Medium-term (months)

- **iOS offline-first MVP** -- SwiftUI + HealthKit, one agent, one intervention, local-only persistence
- **Protocol formalization** -- capsule/gem/incident/decision/procedure as a publishable framework
- **Multi-operator testing** -- validate that the office pattern works for teams beyond a single operator

### Long-term (working theory)

- **Chronos Protocol agents as services** -- 8 domain agents running as persistent processes, not session-bound
- **Cross-project coordination** -- multiple Rhea offices sharing gems and procedures
- **Scientific paper** -- "Mathematics of Rhea" (Fourier, Bayesian, MPC, cross-cultural analysis)

---

## Slide 11: What Is Proven vs. Experimental

| Claim | Status | Evidence |
|-------|--------|---------|
| File-based agent coordination works for 4 concurrent agents | **Proven** (small scale) | 2026-02-16 full-day operation |
| Trinity memory restores context after session death | **Proven** | GEM-002: blind test with fresh agent |
| Cheap-first routing reduces cost without quality loss for routine work | **Proven** | ADR-008, ADR-009: ~80% calls on cheap tier |
| Promotion protocol surfaces useful knowledge | **Working theory** | 7 gems in 1 day, 3 promoted to procedures. Too early to measure long-term compression. |
| Context Tax Collector automates knowledge promotion | **Experimental** | Protocol defined, automation not built |
| The pattern generalizes beyond 1 project / 1 operator | **Unproven** | N=1. Need external validation. |
| Polyvagal theory integration improves daily scheduling | **Unproven** | Scientific foundation referenced (Porges, Bruton 2025, Laengle 2025) but no app-level test yet |
| Multi-model tribunal produces better decisions than single-model | **Working theory** | 2 tribunals completed (ADR-012, ADR-013). Both produced unanimous results. Not enough data for statistical claim. |

---

## Slide 12: Call to Action

Rhea is not an app. It is a coordination pattern for AI agents that:

1. **Survives** session death, provider outage, and context overflow
2. **Learns** through a promotion chain that turns repetition into automation
3. **Audits** every decision with rationale, every incident with root cause, every action with git provenance

**What we need:**
- Engineers willing to run the office pattern on their own multi-agent workflows and report what breaks
- Researchers interested in formalizing the promotion protocol (gem/incident/decision/procedure) as a knowledge management framework
- Operators who want to stress-test multi-provider bridge resilience across different provider mixes

**Where to start:**
- Repository: `rh.1` on GitHub
- Office protocol: `ops/virtual-office/OFFICE.md`
- Bridge: `src/rhea_bridge.py` (run `python3 src/rhea_bridge.py status` to see your provider health)
- Procedures: `docs/procedures/` (battle-tested SOPs with exact commands)

No hype. Working code. Evidence for every claim.
