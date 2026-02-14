# Fix Audit Failures Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all 5 failures identified in the Integrations Audit: 2 script failures + 3 memory benchmark failures.

**Architecture:** Three independent fixes: (1) trim `state.md` under 2KB, (2) create `rhea` CLI wrapper, (3) update `memory_benchmark.sh` to match current ADR-014 strategy (auto-commit, not manual-commit). Each fix is isolated and can be committed separately.

**Tech Stack:** Bash scripts, markdown, git

---

### Task 1: Trim state.md Under 2KB Limit

**Files:**
- Modify: `docs/state.md` (currently 2,270 bytes, limit is 2,048)

**Context:** `scripts/rhea/check.sh` enforces a 2KB hard limit on `docs/state.md` (line 34-37). The file is currently 222 bytes over. The constraint exists because state.md is the compact working memory — it should link to deeper docs, not contain detail.

**Step 1: Identify trimmable content**

The current file has 42 lines. These sections can be compressed:
- "## 3-Product Architecture" — can be one line referencing `docs/architecture.md`
- "## Entire.io Integration" — 6 lines of detail that belongs in `docs/decisions.md` or `docs/state_full.md`
- "## Next" — 6 items can be trimmed to top 3

**Step 2: Write the trimmed state.md**

Replace the full content with this compressed version (target: ~1,800 bytes to leave headroom):

```markdown
# Rhea — compact state

## Mission
Mind Blueprint factory: generate, evaluate, iterate on daily structure models using scientific rhythms, multi-model tribunal, and closed-loop planner.

## Architecture
3-product: Rhea Core (toolset/memory/engine) → iOS App (SwiftUI+HealthKit) → Commander (React/TUI, deferred). See docs/architecture.md.

## Status
- Architecture: v3, 8 agents, Chronos Protocol, 3-product layered design
- Bridge (rhea_bridge.py): live — 6 providers, all keys verified, first tribunal completed
- Docs: normalized, user guide updated, upgrade_plan_suggestions.md created
- Ops: scripts/rhea/ CLI + .entire snapshots/logs + per-query persistence (ADR-014)
- Memory economy: D=63.4, T1=150, T2=300 — ADR-010
- Git: PR#2 merged, main current, 14 ADRs, 2 Tribunals
- Entire.io: auto-commit (ADR-014) via scripts/rhea_commit.sh (ADR-013)

## Next
1. Install Entire GitHub App → checkpoints visible at entire.io dashboard
2. Define minimal user loop → 5-min interaction design before code
3. iOS MVP → SwiftUI + HealthKit, ONE agent, ONE intervention

## Refs
- Full state: docs/state_full.md
- Upgrade plan: docs/upgrade_plan_suggestions.md
- Decisions: docs/decisions.md (14 ADRs)
- Architecture: docs/architecture.md
```

**Step 3: Verify byte count**

Run: `wc -c docs/state.md`
Expected: under 2048 bytes

**Step 4: Run check.sh to verify it passes**

Run: `bash scripts/rhea/check.sh`
Expected: `OK: checks passed`

**Step 5: Commit**

```bash
git add docs/state.md
git commit -m "fix: trim state.md under 2KB limit (HC check)"
```

---

### Task 2: Create `rhea` CLI Wrapper

**Files:**
- Create: `scripts/rhea.sh` (the wrapper)

**Context:** Scripts under `scripts/rhea/` (bootstrap, check, memory) are meant to be invoked as `rhea bootstrap`, `rhea check`, etc. But there's no `rhea` command in PATH. Creating a simple dispatcher script that can be symlinked or aliased solves this.

**Step 1: Write the wrapper script**

Create `scripts/rhea.sh`:

```bash
#!/usr/bin/env bash
# rhea — CLI dispatcher for scripts/rhea/*.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

sub="${1:-help}"
shift 2>/dev/null || true

case "$sub" in
  bootstrap) bash scripts/rhea/bootstrap.sh "$@" ;;
  check)     bash scripts/rhea/check.sh "$@" ;;
  memory)    bash scripts/rhea/memory.sh "$@" ;;
  help|--help|-h)
    echo "Usage: rhea <command> [args]"
    echo ""
    echo "Commands:"
    echo "  bootstrap [--dry-run] [--no-import] [--keep-nested]"
    echo "  check                 Verify repo invariants"
    echo "  memory snapshot|log   Manage snapshots and event logs"
    echo ""
    echo "See also:"
    echo "  scripts/rhea_autosave.sh   Auto-save daemon"
    echo "  scripts/rhea_commit.sh     Git commit with Entire lifecycle"
    echo "  scripts/rhea_orchestrate.py  Multi-agent orchestration"
    ;;
  *)
    echo "Unknown command: $sub" >&2
    echo "Run 'rhea help' for usage." >&2
    exit 1
    ;;
esac
```

**Step 2: Make it executable**

Run: `chmod +x scripts/rhea.sh`

**Step 3: Test the wrapper**

Run: `bash scripts/rhea.sh help`
Expected: Usage output with commands list

Run: `bash scripts/rhea.sh bootstrap --dry-run`
Expected: DRY-RUN output, ends with `OK: bootstrap done`

**Step 4: Symlink into PATH (user action)**

Run: `ln -sf "$(pwd)/scripts/rhea.sh" /usr/local/bin/rhea`

Note: This step requires user confirmation since it modifies a system directory.

**Step 5: Verify `rhea` is in PATH**

Run: `which rhea`
Expected: `/usr/local/bin/rhea`

Run: `rhea help`
Expected: Usage output

**Step 6: Commit**

```bash
git add scripts/rhea.sh
git commit -m "feat: add rhea CLI dispatcher (scripts/rhea.sh)"
```

---

### Task 3: Fix memory_benchmark.sh Strategy Expectations

**Files:**
- Modify: `scripts/memory_benchmark.sh:170-171,220-224`

**Context:** The benchmark expects `manual-commit` strategy in both `docs/state.md` and `.entire/settings.local.json`. But ADR-014 changed the strategy to `auto-commit`. The benchmark is outdated — the 3 failures are false positives. The fix is to update the benchmark to expect the current correct strategy.

**Step 1: Update state.md content checks (lines 170-171)**

In `scripts/memory_benchmark.sh`, find:
```bash
check_file_contains "docs/state.md" "manual-commit" "state.md has manual-commit strategy"
```

Replace with:
```bash
check_file_contains "docs/state.md" "auto-commit" "state.md has auto-commit strategy (ADR-014)"
```

Find:
```bash
check_file_contains "docs/state_full.md" "manual-commit" "state_full.md has manual-commit"
```

Replace with:
```bash
check_file_contains "docs/state_full.md" "auto-commit" "state_full.md has auto-commit (ADR-014)"
```

**Step 2: Update strategy validation (lines 220-223)**

Find:
```bash
  if [ "$STRATEGY" = "manual-commit" ]; then
    pass "Strategy is manual-commit (correct for trailer injection)"
  else
    fail "Strategy is '$STRATEGY' — should be 'manual-commit'"
```

Replace with:
```bash
  if [ "$STRATEGY" = "auto-commit" ]; then
    pass "Strategy is auto-commit (ADR-014)"
  else
    fail "Strategy is '$STRATEGY' — should be 'auto-commit' (ADR-014)"
```

**Step 3: Verify state_full.md contains "auto-commit"**

Run: `grep -c "auto-commit" docs/state_full.md`
Expected: at least 1 match (ADR-014 is recorded there)

If not found, this will still fail. Check and add a reference if needed.

**Step 4: Run the full benchmark**

Run: `bash scripts/memory_benchmark.sh`
Expected: `70/73` or better (the 3 false positives should now pass)

**Step 5: Commit**

```bash
git add scripts/memory_benchmark.sh
git commit -m "fix: update memory_benchmark to expect auto-commit (ADR-014)"
```

---

### Task 4: Update Integrations Audit with Fixed Status

**Files:**
- Modify: `docs/INTEGRATIONS_AUDIT.md`

**Step 1: Update the summary counts**

Change failing count from 2 to 0 and passing from 83 to 85.

**Step 2: Update check.sh row status from FAIL to PASS**

**Step 3: Update rhea CLI row status from FAIL to PASS**

**Step 4: Update Known Issues section**

Remove the 3 items under "### Failures" that are now fixed. Replace with note that all failures have been resolved.

**Step 5: Commit**

```bash
git add docs/INTEGRATIONS_AUDIT.md
git commit -m "docs: update integrations audit — all failures resolved"
```

---

### Task 5: Final Verification

**Step 1: Run check.sh**

Run: `bash scripts/rhea/check.sh`
Expected: `OK: checks passed`

**Step 2: Run memory benchmark**

Run: `bash scripts/memory_benchmark.sh 2>&1 | tail -5`
Expected: 0 failures (or only unrelated pre-existing ones)

**Step 3: Test rhea CLI**

Run: `bash scripts/rhea.sh check`
Expected: `OK: checks passed` (or the state.md check passes)

**Step 4: Verify integrations audit is consistent**

Run: `grep "Failing:" docs/INTEGRATIONS_AUDIT.md`
Expected: `Failing: 0`
