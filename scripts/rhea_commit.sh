#!/usr/bin/env bash
# rhea_commit.sh — Wrapper for git commit with native session lifecycle
#
# Replaces Entire.io dependency with lib_rhea_hooks.sh (ADR-016).
# Backward-compatible: snapshots still go to .entire/snapshots/,
# logs still go to .entire/logs/.
#
# Usage:
#   scripts/rhea_commit.sh -m "your commit message"
#   scripts/rhea_commit.sh --all -m "commit all changes"
#   scripts/rhea_commit.sh  (opens editor for commit message)
#
# ADR-013 (Tribunal-002 decision, 2026-02-14)
# ADR-016 (Entire.io absorption, 2026-02-28)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# shellcheck disable=SC1091
source "scripts/rhea/lib_entire.sh"
# shellcheck disable=SC1091
source "scripts/rhea/lib_rhea_hooks.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[rhea-commit]${NC} $*"; }
warn() { echo -e "${YELLOW}[rhea-commit]${NC} $*"; }
err() { echo -e "${RED}[rhea-commit]${NC} $*" >&2; }

# Step 1: Start session (native hooks)
log "Starting session..."
rhea_git_session_start

# QWRR Lease Fencing (I5: No zombie effects)
if [ -n "${RHEA_AGENT_ID:-}" ] && [ -n "${RHEA_LEASE_TOKEN:-}" ]; then
    log "Verifying lease for $RHEA_AGENT_ID (token: $RHEA_LEASE_TOKEN)..."
    if ! python3 opera/ops/rex_pager.py lease "$RHEA_AGENT_ID" --verify "$RHEA_LEASE_TOKEN" >/dev/null 2>&1; then
        err "Lease verification FAILED. Fencing token stale or expired. [ZOMBIE PREVENTION]"
        exit 1
    fi
    log "Lease valid."
fi

log "Session started"

# Step 1.5: L4 Auto-Flush (Context Cache Coherency)
L4_BRIDGE="rhea-elementary/memory-core/context-bridge.md"
EXPORTER="rhea-nexus/tools/export_state.py"
OFFICE_DIR="ops/virtual-office"

if [ -f "$EXPORTER" ] && [ -d "$OFFICE_DIR" ]; then
    log "Flushing L4 Context Cache (context-bridge.md)..."
    python3 "$EXPORTER" --from "$OFFICE_DIR" --to "$L4_BRIDGE" >/dev/null 2>&1 || warn "L4 flush failed"
    git add "$L4_BRIDGE" 2>/dev/null || true
fi

# Step 2: Run git commit with all user arguments
log "Running git commit..."
COMMIT_EXIT=0
git commit "$@" || COMMIT_EXIT=$?

if [ $COMMIT_EXIT -ne 0 ]; then
    err "git commit failed (exit $COMMIT_EXIT)"
    rhea_git_session_stop
    exit $COMMIT_EXIT
fi

log "Commit successful"

# Step 3: Post-commit logging
rhea_git_post_commit

# Step 4: Stop session
log "Stopping session..."
rhea_git_session_stop

# Step 5: Run Rhea autosave snapshot
if [ -x "$REPO_ROOT/scripts/rhea_autosave.sh" ]; then
    log "Creating Rhea snapshot..."
    "$REPO_ROOT/scripts/rhea_autosave.sh" snapshot "RHEA_COMMIT" 2>/dev/null || true
fi

COMMIT_SHA=$(git rev-parse --short HEAD)
log "Done! Commit ${COMMIT_SHA} with Rhea checkpoint pipeline"

# Step 5.5: CI Enforcement — check for either trailer format
log "Running CI enforcement check..."
if git log -1 --pretty=%B | grep -qE "(Entire-Checkpoint|Rhea-Checkpoint):"; then
    log "CI enforcement: Checkpoint trailer found. [PASS]"
else
    warn "CI enforcement: Checkpoint trailer MISSING."
    warn "This is expected for the first commit after Entire.io absorption."
fi

# Step 6: D-metric check
log "Running D-metric check..."
if python3 scripts/compute_d_metric.py 2>/dev/null; then
    log "D-metric is within threshold."
else
    warn "D-metric exceeds threshold T2. [SPRINT NEEDED]"
fi

# Prune old hook logs
rhea_hooks_prune
