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

*Add new lessons below. Keep each under 5 lines. Tag your agent name and date.*
