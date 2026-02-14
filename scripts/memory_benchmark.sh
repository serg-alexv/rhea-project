#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# RHEA CORE MEMORY BENCHMARK & SELF-STRESS-TEST
# ═══════════════════════════════════════════════════════════════════════════════
# Verifies ALL critical memory layers:
#   Layer 1: Git (structural memory — commits, branches, remotes)
#   Layer 2: Docs (semantic memory — state, architecture, decisions)
#   Layer 3: Entire.io (episodic memory — hooks, sessions, checkpoints)
#   Layer 4: Metrics (self-awareness — discomfort function, thresholds)
#   Layer 5: Snapshots (journal — event trail, named milestones)
#
# Exit codes: 0 = all pass, 1 = failures detected
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo '/sessions/vibrant-zealous-allen/mnt/rh.1')"
cd "$REPO_ROOT"

PASS=0
FAIL=0
WARN=0
REPORT=""
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ── helpers ──────────────────────────────────────────────────────────────────

pass() { ((PASS++)); REPORT+="  ✅ PASS: $1\n"; }
fail() { ((FAIL++)); REPORT+="  ❌ FAIL: $1\n"; }
warn() { ((WARN++)); REPORT+="  ⚠️  WARN: $1\n"; }
section() { REPORT+="\n━━━ $1 ━━━\n"; }

check_file() {
  local path="$1" desc="$2"
  if [ -f "$path" ]; then
    local size
    size=$(wc -c < "$path" | tr -d ' ')
    pass "$desc exists (${size}B)"
  else
    fail "$desc MISSING: $path"
  fi
}

check_file_contains() {
  local path="$1" pattern="$2" desc="$3"
  if [ -f "$path" ] && grep -q "$pattern" "$path" 2>/dev/null; then
    pass "$desc — contains '$pattern'"
  else
    fail "$desc — pattern '$pattern' NOT FOUND in $path"
  fi
}

check_executable() {
  local path="$1" desc="$2"
  if [ -x "$path" ]; then
    pass "$desc is executable"
  else
    fail "$desc NOT executable: $path"
  fi
}

json_field() {
  # Extract a simple JSON field value (no jq dependency)
  local file="$1" field="$2"
  grep -o "\"$field\"[[:space:]]*:[[:space:]]*[^,}]*" "$file" 2>/dev/null | head -1 | sed 's/.*:[[:space:]]*//' | tr -d '"' | tr -d ' '
}

# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 1: GIT — STRUCTURAL MEMORY
# ═══════════════════════════════════════════════════════════════════════════════

section "LAYER 1: GIT — STRUCTURAL MEMORY"

# 1.1 Repository health
if git status --porcelain >/dev/null 2>&1; then
  pass "Git repository valid"
else
  fail "Git repository BROKEN"
fi

# 1.2 Branch check
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
if [ "$CURRENT_BRANCH" = "main" ]; then
  pass "On branch main"
else
  warn "On branch '$CURRENT_BRANCH' (expected: main)"
fi

# 1.3 Checkpoint branch exists
if git rev-parse --verify entire/checkpoints/v1 >/dev/null 2>&1; then
  CKPT_COMMITS=$(git log --oneline entire/checkpoints/v1 2>/dev/null | wc -l | tr -d ' ')
  pass "entire/checkpoints/v1 branch exists ($CKPT_COMMITS commits)"
else
  fail "entire/checkpoints/v1 branch MISSING"
fi

# 1.4 Remote tracking
if git remote get-url origin >/dev/null 2>&1; then
  REMOTE_URL=$(git remote get-url origin)
  pass "Remote origin configured: $REMOTE_URL"
else
  fail "No remote 'origin' configured"
fi

# 1.5 Check for Entire-Checkpoint trailers in history
TRAILER_COUNT=$(git log --format='%B' 2>/dev/null | grep -c "Entire-Checkpoint:" || true)
if [ "$TRAILER_COUNT" -gt 0 ]; then
  pass "Found $TRAILER_COUNT commit(s) with Entire-Checkpoint trailers"
else
  fail "No commits have Entire-Checkpoint trailers"
fi

# 1.6 Commit count
COMMIT_COUNT=$(git log --oneline 2>/dev/null | wc -l | tr -d ' ')
pass "Total commits on main: $COMMIT_COUNT"

# 1.7 Dirty state check
DIRTY_COUNT=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if [ "$DIRTY_COUNT" -eq 0 ]; then
  pass "Working tree clean"
else
  warn "Working tree has $DIRTY_COUNT uncommitted changes"
fi

# 1.8 Worktree check
WT_COUNT=$(git worktree list 2>/dev/null | wc -l | tr -d ' ')
if [ "$WT_COUNT" -le 1 ]; then
  pass "No stale worktrees (count: $WT_COUNT)"
else
  warn "Multiple worktrees active ($WT_COUNT) — check for stale ones"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 2: DOCS — SEMANTIC MEMORY
# ═══════════════════════════════════════════════════════════════════════════════

section "LAYER 2: DOCS — SEMANTIC MEMORY"

# 2.1 Core docs exist
check_file "docs/state.md" "Compact state (state.md)"
check_file "docs/state_full.md" "Full state (state_full.md)"
check_file "docs/architecture.md" "Architecture doc"
check_file "docs/decisions.md" "Decision log (ADRs)"
check_file "docs/langgraph_architecture.md" "LangGraph architecture"
check_file "docs/prism_paper_outline.md" "Prism paper outline"
check_file "README.md" "README.md"

# 2.2 Core docs size budget (ADR-010: T1=200KB)
CORE_DOCS_KB=0
for f in docs/state.md docs/state_full.md docs/architecture.md docs/decisions.md docs/langgraph_architecture.md; do
  if [ -f "$f" ]; then
    SZ=$(wc -c < "$f" | tr -d ' ')
    CORE_DOCS_KB=$((CORE_DOCS_KB + SZ))
  fi
done
CORE_DOCS_KB=$((CORE_DOCS_KB / 1024))
if [ "$CORE_DOCS_KB" -lt 200 ]; then
  pass "Core docs total: ${CORE_DOCS_KB}KB (budget: <200KB T1)"
elif [ "$CORE_DOCS_KB" -lt 500 ]; then
  warn "Core docs total: ${CORE_DOCS_KB}KB — approaching T1 (200KB)"
else
  fail "Core docs total: ${CORE_DOCS_KB}KB — EXCEEDS T2 (500KB)!"
fi

# 2.3 Cross-reference consistency: state.md ↔ state_full.md ↔ architecture.md
check_file_contains "docs/state.md" "8 agents" "state.md references 8-agent system"
check_file_contains "docs/state_full.md" "8 agents" "state_full.md references 8-agent system"
check_file_contains "docs/architecture.md" "8-Agent System" "architecture.md has 8-Agent section"

check_file_contains "docs/state.md" "manual-commit" "state.md has manual-commit strategy"
check_file_contains "docs/state_full.md" "manual-commit" "state_full.md has manual-commit"

check_file_contains "docs/state.md" "rhea_bridge.py" "state.md references bridge"
check_file_contains "docs/architecture.md" "rhea_bridge.py" "architecture.md references bridge"

# 2.4 ADR count and integrity
ADR_COUNT=$(grep -c "^## ADR-" docs/decisions.md 2>/dev/null || true)
if [ "$ADR_COUNT" -ge 10 ]; then
  pass "Decision log has $ADR_COUNT ADRs (expected ≥10)"
elif [ "$ADR_COUNT" -ge 7 ]; then
  pass "Decision log has $ADR_COUNT ADRs"
else
  fail "Decision log only has $ADR_COUNT ADRs (expected ≥7)"
fi

# 2.5 ADR sequence check (no gaps)
for i in $(seq 1 "$ADR_COUNT"); do
  PADDED=$(printf "%03d" "$i")
  if grep -q "ADR-$PADDED" docs/decisions.md 2>/dev/null; then
    : # ok
  else
    warn "ADR-$PADDED missing from decision log"
  fi
done
pass "ADR sequence checked (1..$ADR_COUNT)"

# 2.6 Session log exists in state_full.md
SESSION_COUNT=$(grep -c "^### Session:" docs/state_full.md 2>/dev/null || true)
if [ "$SESSION_COUNT" -ge 2 ]; then
  pass "state_full.md has $SESSION_COUNT session log entries"
else
  warn "state_full.md has only $SESSION_COUNT session log entries"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 3: ENTIRE.IO — EPISODIC MEMORY
# ═══════════════════════════════════════════════════════════════════════════════

section "LAYER 3: ENTIRE.IO — EPISODIC MEMORY"

# 3.1 Entire enabled
if [ -f ".entire/settings.local.json" ]; then
  STRATEGY=$(json_field ".entire/settings.local.json" "strategy")
  ENABLED=$(json_field ".entire/settings.local.json" "enabled")
  if [ "$ENABLED" = "true" ]; then
    pass "Entire.io enabled (strategy: $STRATEGY)"
  else
    fail "Entire.io DISABLED in settings.local.json"
  fi
  if [ "$STRATEGY" = "manual-commit" ]; then
    pass "Strategy is manual-commit (correct for trailer injection)"
  else
    fail "Strategy is '$STRATEGY' — should be 'manual-commit'"
  fi
else
  fail ".entire/settings.local.json MISSING"
fi

# 3.2 Project settings match
if [ -f ".entire/settings.json" ]; then
  PROJ_STRATEGY=$(json_field ".entire/settings.json" "strategy")
  if [ "$PROJ_STRATEGY" = "$STRATEGY" ]; then
    pass "Project settings match local settings (both: $STRATEGY)"
  else
    warn "Project settings ($PROJ_STRATEGY) differ from local ($STRATEGY)"
  fi
fi

# 3.3 Git hooks — executable and correct content
check_executable ".git/hooks/commit-msg" "commit-msg hook"
check_executable ".git/hooks/post-commit" "post-commit hook"
check_executable ".git/hooks/pre-push" "pre-push hook"

check_file_contains ".git/hooks/commit-msg" "entire hooks git commit-msg" "commit-msg calls entire"
check_file_contains ".git/hooks/post-commit" "entire hooks git post-commit" "post-commit calls entire"
check_file_contains ".git/hooks/pre-push" "entire hooks git pre-push" "pre-push calls entire"

# 3.4 Entire.io sessions
SESSION_DIRS=$(ls -d .entire/metadata/*/ 2>/dev/null | wc -l | tr -d ' ')
if [ "$SESSION_DIRS" -ge 1 ]; then
  pass "Entire.io has $SESSION_DIRS session(s) recorded"
else
  fail "No Entire.io sessions in .entire/metadata/"
fi

# 3.5 Session transcripts exist
TRANSCRIPT_COUNT=0
for sess in .entire/metadata/*/; do
  if [ -f "${sess}full.jsonl" ]; then
    SZ=$(wc -c < "${sess}full.jsonl" | tr -d ' ')
    if [ "$SZ" -gt 100 ]; then
      ((TRANSCRIPT_COUNT++))
    fi
  fi
done
if [ "$TRANSCRIPT_COUNT" -ge 1 ]; then
  pass "$TRANSCRIPT_COUNT session(s) have non-empty transcripts (full.jsonl)"
else
  fail "No session transcripts found with meaningful content"
fi

# 3.6 Checkpoint branch data integrity
if git rev-parse --verify entire/checkpoints/v1 >/dev/null 2>&1; then
  CKPT_FILES=$(git ls-tree -r --name-only entire/checkpoints/v1 2>/dev/null | wc -l | tr -d ' ')
  CKPT_METADATA=$(git ls-tree -r --name-only entire/checkpoints/v1 2>/dev/null | grep "metadata.json" | wc -l | tr -d ' ')
  CKPT_TRANSCRIPTS=$(git ls-tree -r --name-only entire/checkpoints/v1 2>/dev/null | grep "full.jsonl" | wc -l | tr -d ' ')
  pass "Checkpoint branch has $CKPT_FILES files ($CKPT_METADATA metadata, $CKPT_TRANSCRIPTS transcripts)"

  # Check checkpoint IDs from trailers match branch content
  for CKPT_ID in $(git log --format='%B' 2>/dev/null | grep "Entire-Checkpoint:" | sed 's/.*: //'); do
    PREFIX="${CKPT_ID:0:2}"
    SUFFIX="${CKPT_ID:2}"
    if git ls-tree entire/checkpoints/v1 "$PREFIX/$SUFFIX/" >/dev/null 2>&1; then
      pass "Checkpoint $CKPT_ID has matching data on entire/checkpoints/v1"
    else
      fail "Checkpoint $CKPT_ID trailer exists but NO data on entire/checkpoints/v1"
    fi
  done
fi

# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 4: METRICS — SELF-AWARENESS
# ═══════════════════════════════════════════════════════════════════════════════

section "LAYER 4: METRICS — SELF-AWARENESS"

# 4.1 Metrics file exists
check_file "metrics/memory_metrics.json" "Memory metrics file"

if [ -f "metrics/memory_metrics.json" ]; then
  # 4.2 Discomfort function defined
  CURRENT_D=$(json_field "metrics/memory_metrics.json" "current_D")
  T1=$(json_field "metrics/memory_metrics.json" "T1_threshold")
  T2=$(json_field "metrics/memory_metrics.json" "T2_threshold")

  if [ -n "$CURRENT_D" ] && [ -n "$T1" ] && [ -n "$T2" ]; then
    pass "Discomfort function defined: D=$CURRENT_D, T1=$T1, T2=$T2"
  else
    fail "Discomfort function fields missing (D=$CURRENT_D, T1=$T1, T2=$T2)"
  fi

  # 4.3 Re-calculate D with current measurements
  ACTUAL_CORE_KB=$CORE_DOCS_KB
  ACTUAL_REPO_MB=$(du -sm . 2>/dev/null | cut -f1 || echo "35")
  ACTUAL_SNAPSHOTS=$(ls .entire/snapshots/ 2>/dev/null | wc -l | tr -d ' ')
  ACTUAL_COMMITS=$COMMIT_COUNT
  STORED_CORE_KB=$(json_field "metrics/memory_metrics.json" "core_docs_kb")
  STORED_REPO_MB=$(json_field "metrics/memory_metrics.json" "repo_size_mb")

  pass "Live measurements: core_docs=${ACTUAL_CORE_KB}KB (stored: ${STORED_CORE_KB}KB), repo=${ACTUAL_REPO_MB}MB (stored: ${STORED_REPO_MB}MB), snapshots=$ACTUAL_SNAPSHOTS, commits=$ACTUAL_COMMITS"

  # 4.4 Check if stored values are stale
  if [ "$STORED_CORE_KB" != "$ACTUAL_CORE_KB" ]; then
    warn "Stored core_docs_kb ($STORED_CORE_KB) differs from actual ($ACTUAL_CORE_KB) — metrics stale"
  else
    pass "core_docs_kb metric is current"
  fi

  # 4.5 Qualitative level
  QUAL_LEVEL=$(json_field "metrics/memory_metrics.json" "qualitative_level")
  pass "Qualitative level: $QUAL_LEVEL"

  # 4.6 Weights defined
  for w in w1 w2 w3 w4 w5; do
    WV=$(json_field "metrics/memory_metrics.json" "$w")
    if [ -n "$WV" ]; then
      : # ok
    else
      fail "Weight $w missing from discomfort function"
    fi
  done
  pass "All 5 discomfort weights (w1-w5) defined"

  # 4.7 Memory budget defined
  check_file_contains "metrics/memory_metrics.json" "core_docs_target_kb" "Memory budget has target"
  check_file_contains "metrics/memory_metrics.json" "snapshots_retention_policy" "Snapshot retention policy defined"
fi

# 4.8 Challenging tasks registry
check_file "data/challenging_tasks.yaml" "Challenging tasks registry"
if [ -f "data/challenging_tasks.yaml" ]; then
  TASK_COUNT=$(grep -c "^  - " "data/challenging_tasks.yaml" 2>/dev/null || true)
  if [ "$TASK_COUNT" -ge 3 ]; then
    pass "Challenging tasks registry has $TASK_COUNT tasks"
  else
    warn "Only $TASK_COUNT challenging tasks registered"
  fi
fi

# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 5: SNAPSHOTS — JOURNAL / EVENT TRAIL
# ═══════════════════════════════════════════════════════════════════════════════

section "LAYER 5: SNAPSHOTS — JOURNAL / EVENT TRAIL"

# 5.1 Snapshot count
SNAP_TOTAL=$(ls .entire/snapshots/*.json 2>/dev/null | wc -l | tr -d ' ')
if [ "$SNAP_TOTAL" -ge 10 ]; then
  pass "Snapshot journal has $SNAP_TOTAL entries"
elif [ "$SNAP_TOTAL" -ge 5 ]; then
  pass "Snapshot journal has $SNAP_TOTAL entries"
else
  warn "Only $SNAP_TOTAL snapshots — expected more for multi-session project"
fi

# 5.2 Named milestone snapshots
NAMED_SNAPS=0
for s in .entire/snapshots/*.json; do
  BASENAME=$(basename "$s")
  if [[ ! "$BASENAME" =~ ^(AUTO-|POST_COMMIT-) ]]; then
    ((NAMED_SNAPS++))
  fi
done
if [ "$NAMED_SNAPS" -ge 5 ]; then
  pass "$NAMED_SNAPS named milestone snapshots (non-auto)"
else
  warn "Only $NAMED_SNAPS named snapshots — consider naming more milestones"
fi

# 5.3 Key milestones present
for MILESTONE in "BOOT" "OPUS_SESSION_1" "MEMORY_ECONOMY" "ENTIRE_PIPELINE_FIX"; do
  if ls .entire/snapshots/${MILESTONE}* >/dev/null 2>&1; then
    pass "Milestone snapshot: $MILESTONE exists"
  else
    fail "Milestone snapshot: $MILESTONE MISSING"
  fi
done

# 5.4 JSON validity of latest snapshots
INVALID_JSON=0
for s in $(ls -t .entire/snapshots/*.json 2>/dev/null | head -5); do
  if python3 -c "import json; json.load(open('$s'))" 2>/dev/null; then
    : # ok
  else
    ((INVALID_JSON++))
    fail "Invalid JSON: $s"
  fi
done
if [ "$INVALID_JSON" -eq 0 ]; then
  pass "Latest 5 snapshots are valid JSON"
fi

# 5.5 Snapshot size growth trend
OLDEST_SNAP_SIZE=$(wc -c < "$(ls -t .entire/snapshots/*.json | tail -1)" 2>/dev/null | tr -d ' ')
NEWEST_SNAP_SIZE=$(wc -c < "$(ls -t .entire/snapshots/*.json | head -1)" 2>/dev/null | tr -d ' ')
pass "Snapshot size range: oldest=${OLDEST_SNAP_SIZE}B → newest=${NEWEST_SNAP_SIZE}B"

# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 6: CROSS-LAYER INTEGRATION STRESS TEST
# ═══════════════════════════════════════════════════════════════════════════════

section "LAYER 6: CROSS-LAYER INTEGRATION"

# 6.1 ADR-007 (Three-tier memory) compliance
check_file_contains "docs/decisions.md" "ADR-007" "ADR-007 (Three-tier memory) recorded"
# Check all three tiers are operational
TIER_GIT=0; TIER_ENTIRE=0; TIER_PROTOCOL=0
[ -f "docs/state.md" ] && TIER_GIT=1
[ -d ".entire/metadata" ] && [ "$SESSION_DIRS" -ge 1 ] && TIER_ENTIRE=1
[ -f "docs/state_full.md" ] && grep -q "Session Log" docs/state_full.md 2>/dev/null && TIER_PROTOCOL=1
if [ "$TIER_GIT" -eq 1 ] && [ "$TIER_ENTIRE" -eq 1 ] && [ "$TIER_PROTOCOL" -eq 1 ]; then
  pass "ADR-007: All 3 memory tiers operational (Git + Entire.io + Protocol)"
else
  fail "ADR-007: Memory tier missing (Git=$TIER_GIT, Entire=$TIER_ENTIRE, Protocol=$TIER_PROTOCOL)"
fi

# 6.2 ADR-008 (Cheap-first routing) referenced in LangGraph
check_file_contains "docs/langgraph_architecture.md" "ADR-008" "LangGraph references ADR-008"
check_file_contains "docs/langgraph_architecture.md" "cheap" "LangGraph uses cheap-first default"

# 6.3 ADR-010 (Memory budget) operational
check_file_contains "docs/decisions.md" "ADR-010" "ADR-010 (Memory Budget) recorded"
check_file_contains "docs/langgraph_architecture.md" "ADR-010" "LangGraph references ADR-010"
if [ -f "metrics/memory_metrics.json" ]; then
  pass "ADR-010: metrics/memory_metrics.json operational"
fi

# 6.4 Source code exists
check_file "src/rhea_bridge.py" "Multi-model bridge (rhea_bridge.py)"
check_file "src/__init__.py" "Python package init"
check_file "requirements.txt" "Requirements file"

# 6.5 Ops scripts
check_file "scripts/rhea_autosave.sh" "Autosave script"
if [ -f "scripts/entire_commit.sh" ]; then
  check_executable "scripts/entire_commit.sh" "entire_commit.sh"
fi

# 6.6 Archive directory ready
if [ -d "archive" ]; then
  pass "archive/ directory exists (for future compaction)"
else
  warn "archive/ directory missing — create before first Reflexive Sprint"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# REPORT
# ═══════════════════════════════════════════════════════════════════════════════

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║        RHEA CORE MEMORY BENCHMARK — SELF-STRESS-TEST REPORT         ║"
echo "╠═══════════════════════════════════════════════════════════════════════╣"
echo "║  Timestamp: $TIMESTAMP"
echo "║  Repo:      $(git remote get-url origin 2>/dev/null || echo 'local')"
echo "║  Branch:    $CURRENT_BRANCH @ $(git rev-parse --short HEAD 2>/dev/null)"
echo "║  Commit:    $(git log --oneline -1 2>/dev/null)"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "$REPORT"
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "  VERDICT:  ✅ $PASS passed  |  ❌ $FAIL failed  |  ⚠️  $WARN warnings"
echo "═══════════════════════════════════════════════════════════════════════"

TOTAL=$((PASS + FAIL + WARN))
if [ "$FAIL" -eq 0 ]; then
  echo ""
  echo "  🟢  ALL CRITICAL CHECKS PASSED — Core memory is HEALTHY"
  echo "     Score: $PASS/$TOTAL ($(( PASS * 100 / TOTAL ))%)"
  echo ""
  exit 0
else
  echo ""
  echo "  🔴  $FAIL CRITICAL FAILURE(S) DETECTED — requires attention"
  echo "     Score: $PASS/$TOTAL ($(( PASS * 100 / TOTAL ))%)"
  echo ""
  exit 1
fi
