#!/usr/bin/env bash
# rhea_commit.sh — Wrapper for git commit that ensures Entire.io session lifecycle
#
# Problem: Cowork commits via osascript bypass Entire.io's agent hooks.
#          No session-start → no trailer → no checkpoint on entire.io dashboard.
#
# Solution: This script wraps git commit with explicit session hook calls:
#   1. entire hooks git session-start
#   2. git commit (with all user arguments)
#   3. entire hooks git prepare-commit-msg (trailer injection happens here)
#   4. entire hooks git post-commit (condense + checkpoint push)
#   5. entire hooks git session-stop
#
# Usage:
#   scripts/rhea_commit.sh -m "your commit message"
#   scripts/rhea_commit.sh --all -m "commit all changes"
#   scripts/rhea_commit.sh  (opens editor for commit message)
#
# ADR-013 (Tribunal-002 decision, 2026-02-14)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[rhea-commit]${NC} $*"; }
warn() { echo -e "${YELLOW}[rhea-commit]${NC} $*"; }
err() { echo -e "${RED}[rhea-commit]${NC} $*" >&2; }

# Check if entire CLI is available
if ! command -v entire &>/dev/null; then
    err "entire CLI not found. Install from https://entire.io"
    err "Falling back to plain git commit..."
    git commit "$@"
    exit $?
fi

# Step 1: Start Entire.io session
log "Starting Entire.io session..."
if entire hooks git session-start 2>/dev/null; then
    SESSION_STARTED=true
    log "Session started"
else
    warn "session-start failed (non-fatal) — continuing"
    SESSION_STARTED=false
fi

# Step 2: Run git commit with all user arguments
# The commit-msg hook will inject trailers if session is active
log "Running git commit..."
COMMIT_EXIT=0
git commit "$@" || COMMIT_EXIT=$?

if [ $COMMIT_EXIT -ne 0 ]; then
    err "git commit failed (exit $COMMIT_EXIT)"
    # Still try to stop session cleanly
    if [ "$SESSION_STARTED" = true ]; then
        entire hooks git session-stop 2>/dev/null || true
    fi
    exit $COMMIT_EXIT
fi

log "Commit successful"

# Step 3: Trigger post-commit (checkpoint condensation + push)
# Note: post-commit hook should already run automatically,
# but we call it explicitly to ensure it fires in all contexts
log "Triggering post-commit checkpoint..."
entire hooks git post-commit 2>/dev/null || warn "post-commit hook returned non-zero (non-fatal)"

# Step 4: Stop session
if [ "$SESSION_STARTED" = true ]; then
    log "Stopping Entire.io session..."
    entire hooks git session-stop 2>/dev/null || warn "session-stop failed (non-fatal)"
fi

# Step 5: Run Rhea autosave snapshot
if [ -x "$REPO_ROOT/scripts/rhea_autosave.sh" ]; then
    log "Creating Rhea snapshot..."
    "$REPO_ROOT/scripts/rhea_autosave.sh" snapshot "RHEA_COMMIT" 2>/dev/null || true
fi

COMMIT_SHA=$(git rev-parse --short HEAD)
log "Done! Commit ${COMMIT_SHA} with Entire.io checkpoint pipeline"
