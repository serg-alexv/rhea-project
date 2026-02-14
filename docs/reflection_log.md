# Rhea — Reflection Log

> Failure memory + lessons learned. Consult before repeating similar tasks.

## Format

Each entry records: what happened, why it failed, root cause, and the fix.
This log is part of the self-improvement loop (ADR-011, technique #5: Failure Memory).

---

## Entry 001: Entire.io auto-commit strategy doesn't inject trailers (2026-02-13)

**What happened:** Entire.io was configured with `auto-commit` strategy. Expected `Entire-Checkpoint` trailers on user commits. Trailers were missing.

**Root cause:** `auto-commit` creates *separate* commits for checkpoint data. Only `manual-commit` strategy adds trailers to the user's own commits via the `commit-msg` hook.

**Fix:** Switched to `manual-commit` in `.entire/settings.local.json`. Verified trailer injection works.

**Lesson:** Read Entire.io docs carefully before assuming behavior. The strategy names are misleading — "auto" doesn't mean "automatic trailer injection."

---

## Entry 002: commit-msg hook not executable (2026-02-13)

**What happened:** `commit-msg` hook existed at `.git/hooks/commit-msg` but wasn't being invoked.

**Root cause:** File permissions were `-rw-------` (no execute bit). Git hooks require `+x`.

**Fix:** `chmod +x .git/hooks/commit-msg`

**Lesson:** Always check file permissions when hooks aren't firing. This is a common gotcha with git hooks.

---

## Entry 003: Stale metrics in memory_metrics.json (2026-02-14)

**What happened:** Memory benchmark reported `core_docs_kb` as 124 in metrics file, but actual measurement was 24KB.

**Root cause:** Metrics were recorded in Session 9 and never updated as docs were compacted/reorganized. The D calculation was inflated (91.96 vs actual 62.7).

**Fix:** Updated all fields in `metrics/memory_metrics.json` with live measurements. Added benchmark script to automatically detect stale values.

**Lesson:** Metrics must be updated after every structural change. The benchmark script now checks for staleness — run it after every session that modifies docs.

---

## Entry 004: VM cannot run macOS-only tools (2026-02-13)

**What happened:** Attempted to run `entire checkpoint create` from the Cowork VM. Command not found.

**Root cause:** Entire CLI is installed on macOS, not in the Linux VM. The VM sees the repo via FUSE mount but doesn't have macOS tools.

**Fix:** Use `osascript` via Desktop Commander to run macOS commands. Path mapping: VM `/sessions/vibrant-zealous-allen/mnt/rh.1/` → macOS `/Users/sa/rh.1/`.

**Lesson:** Any tool that must run on macOS (entire, git with hooks, SSH with keys) needs to go through osascript. Keep a clear mental model of VM vs macOS boundaries.

---

*Add new entries below. Keep chronological. Consult before similar tasks.*
