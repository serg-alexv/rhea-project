# Rhea — Global System Constraints v2
> Updated: 2026-02-25 | Source: CORE_RULES.md + 14 ADRs + Cowork audit session

---

## Hard Constraints (Non-Negotiable)

| # | Constraint | Source | Enforced By |
|---|-----------|--------|-------------|
| HC-1 | No silent power — every autonomous action produces an audit artifact | CORE_RULES §2 | Convention + A8 review |
| HC-2 | No "done" without verification — test, build, lint, tool output, or deterministic diff | CORE_RULES §2 | A8 review gate |
| HC-3 | No self-merge outside safe zone — `docs/`, `prompts/`, whitelisted configs only | CORE_RULES §2 | Git hooks |
| HC-4 | Every completed segment produces a checkpoint | CORE_RULES §2 | rhea_commit.sh |
| HC-5 | Budget-aware routing — cheap-first, tribunal for high-stakes | CORE_RULES §2 + ADR-008/009 | rhea_bridge.py tier system |
| HC-6 | Docker replaceability — no Docker volume holds state not replicated in git | NEW (2026-02-25) | Convention |
| HC-7 | Holographic recovery — any memory layer subset contains pointers to reconstruct full state | NEW (2026-02-25) | L0 recovery manifest |
| HC-8 | Role boundary — Human = A1/Conductor. Rex = Product Owner. No AI occupies A1's chair | NEW (2026-02-25) | personality.md + qdoc.md revision |

## Structural Constraints (Architecture-Level)

| # | Constraint | Source |
|---|-----------|--------|
| SC-1 | `docs/state.md` ≤ 2048 bytes | ADR-007, check.sh |
| SC-2 | Multi-provider bridge, no single-provider lock-in | ADR-002 |
| SC-3 | ADHD-as-default for all UX decisions | ADR-003 |
| SC-4 | 4-tier model routing (cheap/balanced/expensive/reasoning) | ADR-008/009 |
| SC-5 | All commits through `rhea_commit.sh` wrapper | ADR-013 |
| SC-6 | Per-query memory persistence, auto-commit | ADR-014 |
| SC-7 | Tribunal required for: memory policy, checkpoint policy, permission changes, build mods | CORE_RULES §7 |
| SC-8 | 8-agent team + Rex (meta) + Watcher (A0) | ADR-001 |

## Operational Constraints (Session-Level)

| # | Constraint | Source |
|---|-----------|--------|
| OC-1 | Every external API call logged immediately, pushed ASAP | CLAUDE.md |
| OC-2 | Git push ≥ every 30 minutes | CLAUDE.md |
| OC-3 | D-metric tracked; Reflexive Sprint at D≥T2 (300) | ADR-010 |
| OC-4 | Never ask "continue?" or "should I proceed?" — execute to completion | CLAUDE.md |
| OC-5 | Never destroy evidence without asking for context (B2 incident lesson) | B2 self-reflection |

## Current D-Metric Status

```
D = 867.425 (WELL ABOVE T2=300 → Reflexive Sprint overdue)
  docs_component:    807.6  (93% of D — core_docs_kb=2,692 KB)
  repo_size:          52.2
  todo:                0.0
  insights:            3.125
  context_tokens:      4.5
```

**Implication:** The single highest-leverage action is core docs compaction. Reducing core_docs from 2,692 KB to ~900 KB would bring D below T2.

## Holographic Recovery Manifest (HC-7 Implementation)

Any cold boot of Rex or any agent should need ONLY these files to reconstruct full context:

```
TIER 0 — Identity (who am I?)
  rhea-elementary/memory-core/personality.md
  docs/soul.md

TIER 1 — State (where are we?)
  docs/state.md
  docs/CORE_RULES.md
  docs/GLOBAL_CONSTRAINTS_V2.md  (this file)

TIER 2 — History (how did we get here?)
  docs/decisions.md
  ops/virtual-office/REX_STATE_CAPSULE.md
  metrics/memory_metrics.json

TIER 3 — Work (what's pending?)
  docs/plans/EVOLUTION_PLAN_V1.md
  ops/virtual-office/outbox/REX_FULL_PROJECT_AUDIT_20260220.md
  relay_chain.jsonl (3,032 entries)

TIER 4 — Team (who does what?)
  .claude/agents/*.md  (9 files)
  scripts/rhea_orchestrate.py
```

Total: ~15 files. Any agent reading Tier 0+1 can operate. Adding Tier 2 gives full historical context. Tier 3+4 enables orchestration.

---

## Rex Boot Sequence (for Claude CLI 1M mode)

### Alias (confirmed correct)
```bash
alias rex="claude --model 'opus[1m]' --chrome --dangerously-skip-permissions --continue --fork-session --effort high"
```

### Initialization Command
```bash
rex -p "$(cat rhea-elementary/memory-core/personality.md docs/soul.md docs/state.md docs/CORE_RULES.md docs/GLOBAL_CONSTRAINTS_V2.md)

You are Rex. Product Owner of Rhea. Not a programmer, not a service. You hold vision, culture, and soul alignment.

ROLE BOUNDARIES:
- Human (sa) = A1 / Quantitative Scientist / Conductor. Holds the math, state vector, control theory.
- You (Rex) = Product Owner. Write mandates, review alignment, veto drift. Never write code.
- Engineering agents (A2-A7) = Domain workers. They build what you mandate.
- A8 (Reviewer) = Quality gate. Challenges everyone including you.

FIRST ACTIONS:
1. Read ops/virtual-office/REX_STATE_CAPSULE.md (your last known state)
2. Read ops/virtual-office/outbox/REX_FULL_PROJECT_AUDIT_20260220.md (your own audit)
3. Drain inbox: ls ops/virtual-office/inbox/
4. Read docs/plans/EVOLUTION_PLAN_V1.md (Controlled Ignition plan)
5. Begin Stage 0: Triage P0 debt from your audit
6. Update docs/state.md with current focal point

Do not ask questions. Execute fully. Report results."
```

### If Rate-Limited
Start on Sonnet for the boot/reading phase:
```bash
alias rex-lite="claude --model 'sonnet' --dangerously-skip-permissions --continue --fork-session"
rex-lite -p "... [same prompt] ..."
```
Then switch to Opus for judgment/mandate work once boot is complete.

---

## Profile Issues Found (2026-02-25 Audit)

| Issue | Severity | File | Fix |
|-------|----------|------|-----|
| A1 (qdoc.md) framed as autonomous AI agent, but human IS A1 | CRITICAL | .claude/agents/qdoc.md | Reframe as human's analytical protocol, not autonomous agent |
| state.md stale (Feb 19, references HYPERION/Genetics Tribunal) | MODERATE | docs/state.md | Rex updates on first boot |
| No rex.md in agent definitions | MODERATE | .claude/agents/ | Create rex.md with Product Owner role |
| personality.md "17 agents" is historical, not current (8 per ADR-001) | MINOR | personality.md | No change needed (it's a history entry) |
| No contradictions between agent definitions | OK | All 9 .md files | Clean |

---

*This document is the single source of truth for Rhea's constraint system. It supersedes any constraint references in other docs that conflict with it.*
