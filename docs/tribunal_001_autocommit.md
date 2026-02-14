# Tribunal 001: Should Rhea Enable Entire.io Auto-Commit Mode?

> **Date:** 2026-02-14
> **Tribunal ID:** TRIBUNAL-001
> **Question:** Should the Rhea project switch from `manual-commit` to `auto-commit` strategy in Entire.io?
> **Current config:** `manual-commit` (set in Session 10–12 after discovering auto-commit doesn't inject trailers)
> **Quorum:** 3 perspectives — Advocate, Skeptic, Pragmatist

---

## Background

Entire.io supports two commit strategies:

| Strategy | Behavior | Trailers | Snapshots |
|----------|----------|----------|-----------|
| `manual-commit` | Injects `Entire-Checkpoint` trailers into **user's own commits** via `commit-msg` hook | ✅ On every user commit | Only on user commits |
| `auto-commit` | Creates **separate** Entire commits automatically on file changes | ❌ No trailers on user commits | Continuous, independent of user commits |

The project switched from `auto-commit` to `manual-commit` in Session 10–12 (see reflection_log.md Entry 001) after discovering that auto-commit did not inject trailers as expected.

---

## Perspective A — The Advocate (for auto-commit)

**Position:** Switch back to `auto-commit`. The richer capture outweighs the trailer loss.

### Pros

1. **Continuous episodic memory.** Auto-commit captures work-in-progress states between user commits. Manual-commit only snapshots at commit boundaries — you lose all intermediate thinking, drafts, and exploration.

2. **Lower cognitive load.** Aligns with ADR-003 (ADHD-first design). Auto-commit requires zero user action. Manual-commit requires remembering to commit, which is exactly the kind of executive-function task ADHD users struggle with.

3. **Richer training data for self-improvement.** More snapshots = more data for the Reflexion loop (ADR-011). The system can analyze *how* work evolved, not just final states.

4. **Decoupled from git workflow.** Entire's memory layer shouldn't depend on git discipline. A researcher who goes hours without committing still generates valuable episodic data.

5. **No hook fragility.** The commit-msg hook has already broken once (Entry 002: permissions). Auto-commit eliminates this failure mode entirely.

### Rebuttal to trailer concern

Trailers are nice-to-have metadata but not essential. The POST_COMMIT snapshots already link to specific git SHAs. The cross-referencing works without trailers — it just requires reading the snapshot JSON instead of `git log`.

---

## Perspective B — The Skeptic (against auto-commit)

**Position:** Keep `manual-commit`. Trailers and commit-aligned snapshots are architecturally superior.

### Contras (against switching)

1. **Trailers are the gold standard for provenance.** `Entire-Checkpoint: <hash>` in `git log` creates a single source of truth. Without trailers, you need to cross-reference snapshot JSONs manually — this breaks the "glanceable memory" principle.

2. **Snapshot noise.** Auto-commit generates snapshots on *every file save*. For a project with 36 snapshots already, this could explode to hundreds. The discomfort function (D) would spike from snapshot bloat, triggering unnecessary cleanup cycles.

3. **Git history pollution.** Auto-commit creates separate commits. The clean commit history (24 commits, each meaningful) would be polluted with Entire checkpoint commits that have no semantic value to human readers.

4. **Already solved.** The hook works. Permissions issue was fixed (Entry 002). The prepare-commit-msg and post-commit hooks are all functional. Why fix what isn't broken?

5. **Benchmark alignment.** The memory benchmark checks for trailer presence (Layer 3). Switching to auto-commit would require rewriting benchmark checks, risking score regression.

### Rebuttal to advocate

"Continuous capture" sounds appealing but creates a signal-to-noise problem. Named snapshots (MEMORY_ECONOMY, PIPELINE_FIXED) are far more valuable than 500 AUTO-* snapshots of intermediate file saves.

---

## Perspective C — The Pragmatist (hybrid approach)

**Position:** Neither pure auto-commit nor pure manual-commit. Use a hybrid strategy.

### Proposal: manual-commit + scheduled auto-snapshots

1. **Keep `manual-commit` as primary.** Trailers stay. Benchmark stays green. Git history stays clean.

2. **Add a cron-based auto-snapshot** (separate from Entire's auto-commit). Run `entire checkpoint create --name AUTO-$(date)` every 30 minutes during active work sessions. This captures intermediate states without polluting git history.

3. **Apply the existing retention policy.** `memory_budget.snapshots_retention_policy` already says: "AUTO-* older than 30 days → archive or delete." This keeps snapshot count bounded.

4. **Best of both worlds:**
   - Trailers ✅ (manual-commit)
   - Intermediate capture ✅ (cron snapshots)
   - Clean git history ✅ (no extra commits)
   - Bounded growth ✅ (retention policy)
   - No hook fragility concern ✅ (hooks still work, but aren't the only capture mechanism)

### Implementation cost

Minimal — one cron job or launchd plist on macOS. Could even be triggered by the Cowork session opening.

---

## Tribunal Consensus

**Vote:**
- Advocate: Switch to auto-commit → **REJECTED** (2-1)
- Skeptic: Keep manual-commit as-is → **PARTIAL ACCEPT**
- Pragmatist: Hybrid approach → **ACCEPTED** (3-0 as compromise)

**Decision:** Keep `manual-commit` strategy. Optionally add scheduled auto-snapshots for richer episodic capture without sacrificing trailers or git cleanliness.

**Agreement Score:** 0.85 — Strong consensus on keeping manual-commit; unanimous support for the hybrid enhancement as a future option.

**Action Items:**
1. ✅ Keep `strategy: "manual-commit"` in `.entire/settings.local.json` (no change)
2. 📋 Add "scheduled auto-snapshot cron" to ROADMAP.md as a Stage 2 enhancement
3. 📋 Document this decision as ADR-012

---

## ADR-012: Keep Manual-Commit, Defer Hybrid Auto-Snapshots

**Context:** Tribunal-001 evaluated whether to switch Entire.io from manual-commit to auto-commit strategy.

**Decision:** Keep manual-commit. The trailer injection, clean git history, and benchmark alignment outweigh the continuous-capture benefit of auto-commit. A hybrid approach (manual-commit + scheduled cron snapshots) is deferred to Stage 2.

**Rationale:** Manual-commit was hard-won (Sessions 10–12, reflection_log entries 001–002). The hooks work. Switching back introduces noise and loses provenance trailers. The pragmatist's hybrid proposal captures the advocate's benefits without the skeptic's concerns.

**Dependencies:** ADR-008 (cost discipline — more snapshots = more storage), ADR-011 (self-improvement loop benefits from richer data).
