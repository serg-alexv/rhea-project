#!/usr/bin/env bash
set -euo pipefail

EXPERIMENTAL="${RHEA_EXPERIMENTAL:-0}"

# shellcheck disable=SC1091
source "scripts/rhea/lib_entire.sh"

DRY_RUN=0
NO_IMPORT=0
KEEP_NESTED=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --no-import) NO_IMPORT=1 ;;
    --keep-nested) KEEP_NESTED=1 ;;
    *) echo "Unknown arg: $arg" >&2; exit 1 ;;
  esac
done

run(){ if [ "$DRY_RUN" -eq 1 ]; then echo "DRY-RUN: $*"; else eval "$@"; fi; }

run "mkdir -p docs prompts src scripts .entire/logs .entire/snapshots"

# README в корень
if [ ! -f README.md ]; then
  if [ -f rhea-project/README.md ]; then
    run "cp rhea-project/README.md README.md"
  else
    cat > README.md <<'R'
# Rhea Project

## Start here
- docs/architecture.md
- docs/decisions.md
- docs/state.md
- docs/MVP_LOOP.md
- docs/ROADMAP.md

## Layout
- docs/     specs & notes
- prompts/  protocols & prompts
- src/      code
- scripts/  utilities
R
  fi
fi

# импорт вложенных docs/prompts
if [ "$NO_IMPORT" -eq 0 ]; then
  if [ "$KEEP_NESTED" -eq 1 ]; then
    run "./scripts/rhea/import_nested.sh --keep-nested"
  else
    run "./scripts/rhea/import_nested.sh"
  fi
fi

# каркасные docs, если отсутствуют
[ -f docs/MVP_LOOP.md ] || cat > docs/MVP_LOOP.md <<'M'
# MVP_LOOP — Closed-Loop Scheduler Spec (Draft)
(define: state x_t, actions A, reward, constraints, updates, logging)
M

[ -f docs/ROADMAP.md ] || cat > docs/ROADMAP.md <<'M'
# ROADMAP
(stage 0..3)
M

# убрать .venv из индекса, если вдруг
if git ls-files --error-unmatch .venv >/dev/null 2>&1; then
  run "git rm -r --cached .venv"
fi

log_event "rhea bootstrap" "ok" "normalized repo"
[ "$EXPERIMENTAL" = "1" ] && snapshot_repo_state "BOOTSTRAP"

echo "OK: bootstrap done"
git status --porcelain || true
