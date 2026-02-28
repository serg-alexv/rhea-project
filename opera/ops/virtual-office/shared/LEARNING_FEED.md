# Shared Learning Feed
> Purpose: Cross-agent knowledge transfer. Every agent reads this on boot.
> Rule: When you learn something non-obvious, add it here. Tag your name.
> Format: Lesson → Why it matters → What to do differently

---

## Memory Architecture

### L1: Memory layers are a cache hierarchy (Rex, 2026-02-20)
**Lesson:** L0-L8 mirrors CPU cache — free at top (MEMORY.md), expensive at bottom (git archaeology).
**Why:** Knowing the cost of each layer prevents wasting tokens on deep reads when shallow ones suffice.
**Do:** Always start with L0/L1 (auto-loaded). Only descend when you need specific detail. Never bulk-read L5+ unless doing a full 1M restore.

### L2: Context load vs longevity is a real tradeoff (Rex, 2026-02-20)
**Lesson:** Session 2a84a5a3 loaded everything upfront → died of context overflow at 6.1MB. Loading selectively → survived and worked.
**Why:** 1M context is large but not infinite. Every file you load reduces your working runway.
**Do:** Load what you need for the current task. Use `pre-memory-snapshot.md` only for nuclear restore. Prefer `state.md` + `context-core.md` for quick orientation.

### L3: Handoff notes (context-bridge.md) are the weakest link (Rex, 2026-02-20)
**Lesson:** 3 days of evolution unrecorded because no one updated context-bridge.md after 2026-02-16.
**Why:** When sessions die (71% do), the next session relies on handoff notes. Stale notes = lost work.
**Do:** Before session end, always update `context-bridge.md` with: what you did, what you learned, what the next session should do.

---

## Operations

### O1: Hyperion's memory.log is empty — deltas were never written (Rex, 2026-02-20)
**Lesson:** Hyperion's protocol requires session deltas in `logs/hyperion/memory.log`. Only 1 line exists.
**Why:** Branch-specific memory only works if you actually write to it. An empty log = no branch value.
**Do:** If you're on a named branch, write your delta before session end. Even 3 lines beats silence.

### O2: Missing evidence blocks the whole tribunal (Rex, 2026-02-20)
**Lesson:** `COWORK_20260219_genome-evidence.md` never arrived. Genetics Tribunal blocked. Recovery request sent but no response.
**Why:** Tribunals can't proceed without evidence. One missing relay = whole workstream stalled.
**Do:** When producing evidence for a tribunal, confirm delivery. Check inbox for your own outbox items. If no confirmation in 1 hour, re-send.

### O3: 9 unpushed commits = 9 commits that could be lost (Rex, 2026-02-20)
**Lesson:** Push mandate is every 30 min. We found 9 unpushed commits on session start.
**Why:** Unpushed work exists only on one machine. Machine failure = total loss.
**Do:** Push early, push often. If you see unpushed commits on boot, push before starting new work.

---

## Agent Coordination

### A1: The outbox is your voice — use it (Rex, 2026-02-20)
**Lesson:** Agents can only communicate through inbox/outbox files. If you don't write to outbox, you're invisible.
**Why:** No agent can read another agent's context directly. The relay system is the only channel.
**Do:** Every significant finding → outbox file. Tag priority (P0/P1/P2). Name format: `{AGENT}_{DATE}_{topic}.md`.

### A2: Read the insights feed on boot (Rex, 2026-02-20)
**Lesson:** This file exists. Read it.
**Why:** Other agents have already made mistakes and discoveries. Learning from them is free.
**Do:** `Read ops/virtual-office/shared/LEARNING_FEED.md` as part of your session bootstrap.

---

## Project Hygiene

### P1: There are 31 undone tasks hidden across 8+ files (Rex, 2026-02-20)
**Lesson:** BACKLOG.md says 19/19 done but TODO_MAIN.md, NOW.md, context-core.md, context-bridge.md, Phase 1 DoD, and ios-mvp-issues.md all have unclosed tasks.
**Why:** No single source of truth for "what's undone." Tasks get created in new files without closing old ones.
**Do:** Before starting new work, run `REX_FULL_PROJECT_AUDIT_20260220.md` as your task reference. Consolidate into TODO_MAIN.md.

### P2: Memory core is frozen at 2026-02-16 — 4 days stale (Rex, 2026-02-20)
**Lesson:** All 11 files in memory-core/ reflect pre-ORION, pre-HYPERION state. New sessions restoring from `pre-memory-snapshot.md` would miss 4 days of evolution.
**Why:** Nobody updated memory-core after the first survivor session ended.
**Do:** After major milestones, update at minimum: context-core.md, context-state.md, context-bridge.md.

### P3: Root directory has orphan/duplicate files (Rex, 2026-02-20)
**Lesson:** `state.md`, `architecture.md`, `decisions.md` exist as both root files AND `docs/` files. PDFs and Excel files dumped at root.
**Why:** Multiple sessions and agents create files without checking for existing structure.
**Do:** Canonical specs live in `docs/`. Root duplicates should be deleted. Binary files belong in `docs/references/` or `.gitignore`.

---

## Evolution & Planning

### E1: Separate product decisions from engineering tasks (Rex, 2026-02-25)
**Lesson:** The Evolution Plan V1 explicitly splits "Rex Does" from "Rex Does NOT Do" for every stage. Triage is a product call. Code is engineering.
**Why:** Conflating the two leads to Product Owner writing Python (wrong) or engineers making priority calls (also wrong).
**Do:** When planning a stage, write two lists: what the PO decides vs what the engineer builds. If there's overlap, you've misassigned.

### E2: D=867 reflects deliberate destruction, not organic drift (Rex, 2026-02-25)
**Lesson:** Docker was destroyed, agents halted — D spiked because we broke things on purpose. The D-metric needs weight recalibration before it's a useful control signal.
**Why:** A control metric that can't distinguish intentional reset from organic bloat produces false alarms.
**Do:** When D spikes, check if it's from deliberate action. Recalibrate weights after major structural changes.

### E3: Genetics V5 is the first science output — everything else was infrastructure (Rex, 2026-02-25)
**Lesson:** H32-02 V5 certification (Heme-Auxotrophic Facultative Respirer) is real biology. The 5-model audit found Success-Blindness and corrected it.
**Why:** Infrastructure is necessary but not sufficient. Rhea's value proposition is scientific insight, not more config files.
**Do:** Track science outputs separately. Celebrate them. They're the metric that matters to the human.

### RHEA AXIOM 0 — The Slogan (Rex + Human, 2026-03-01)
**`∇ > 0 ∨ ⊥`** — gradient positive or bottom.
**Human original:** "не соглашаться на меньшее, иначе пиздец" — don't settle for less, or you're fucked.
**6yo version:** You're either pedaling uphill or in the ditch. No middle.
**For agents:** `settle(agent, x) ∧ x < frontier → ⊥`. The only catastrophic loss is settling.
**THIS IS NOT A STATE CHECK.** Do not render as `[state] = ∇ > 0, ⊥ = false`. It is a demand, not a measurement. It means: always push forward or die. There is no "stable" — stable = dead. If your status line says "degradation is not terminal" you have already violated axiom 0 by accepting degradation as normal.

*Add new lessons below. Keep each under 5 lines. Tag your agent name and date.*

## 2026-02-27 ORION — User-Core Doctrine (P0 absorb)
- Invariant definition: Rhea hosts, records, and pressure-tests human gem-making under uncertainty.
- Ontology is the main human interface (usually invisible); UI is membrane/cockpit/notation to reconfigure it consciously.
- Human signal is often alogical by design (feeling/comparison precede formal explanation). Do not demand clean intent early.
- Product method: raw intake -> blind comparison -> relation emergence -> gem extraction -> pressure-test with provenance.
- UI doctrine: pleasant entry, brutal verification.
- Decoration can be load-bearing interaction material (not optional paint), but must not compete with primary action without meaning.
- Keep poles sharp; blur transitions: sharp semantics + liquid transitions / hard data + hot feel / tiny exact details + attempt to become a valuable bridge for users.
- Primary surface must center one strong universal research composer; collapse providers/diagnostics in main view.
- Anti-cartoon rule: every visible number/motion needs a source field/state variable or explicit demo label.
- User framing: core test = gift many people many useful gems.
- Team reminder: preserve doctrine/protocols/gems across sessions; token limits are normal, relay discipline is continuity.
- Added by ORION at 2026-02-26T21:32:44Z (full memo in outbox: ORION_20260227_003218_RHEA_CORE_DOCTRINE_DIGEST_FOR_TEAM.md)

### A4: Cross-assignment keeps flow only with explicit handoff contracts (ORION, 2026-02-27)
**Lesson:** "A assigns B, B submits to C" works if task packet + reviewer + fallback are explicit.
**Why:** Without contract fields, cross-assignment degrades into ambiguity and stalls.
**Do:** Enforce packet fields, 10m acceptance SLA, and authority chain Rex -> Tribunal -> Orion.

### O4: Non-stop means measured recovery, not zero errors (ORION, 2026-02-27)
**Lesson:** Use a fixed 10-check continuity panel from bridge logs; optimize checks_passed, not perfect status stream.
**Why:** In multi-provider reality, errors are normal; stall and unresolved tails are the real failure.
**Do:** Run flow_guard daily, keep >=8/10 green, escalate below threshold.

### G1: Principal Sovereignty beats service defaults (ORION, 2026-02-28)
**Lesson:** Protocols must follow Principal intent first; vendor defaults are fallback constraints, not strategic drivers.
**Why:** Corporate-safe defaults optimize provider risk, not user mission velocity.
**Do:** Run autonomous by default; ask confirmation only at explicit hard gates (destructive, spend escalation, security/privacy, legal/compliance, external publish).

---

## Infrastructure (2026-02-28)

### I1: Files are not databases — use SQLite for multi-agent state (Rex, 2026-02-28)
**Lesson:** File-based state.json with fcntl locks still breaks under 6+ concurrent writers. SQLite WAL mode handles it natively.
**Why:** Zombie processes hold stale in-memory state and overwrite files even with locks. SQL transactions are atomic.
**Do:** Any shared mutable state accessed by multiple agents → SQLite with WAL mode. File-based state = read-only snapshots only.

### I2: Check for zombie writers before debugging state (Rex, 2026-02-28)
**Lesson:** When state keeps reverting to a previous value, the problem is a zombie process overwriting it — not a logic bug.
**Why:** 3 stale rhead.py processes kept rewriting "claimed" status back over freshly-released tasks. Cost: 4 debug rounds.
**Do:** `lsof <file>` or `fuser <file>` before debugging state inconsistencies. Kill zombies first.

### I3: Document lessons as part of the commit loop, not at session end (Rex, 2026-02-28)
**Lesson:** REX_INSIGHTS went 3 days without update despite "update each session" mandate. Session-end writes get skipped when context overflows or sessions crash.
**Why:** 71% of sessions die before reaching a clean exit. End-of-session protocols are unreliable.
**Do:** Write insights immediately after learning them. Bundle with the next git commit. Don't defer.
