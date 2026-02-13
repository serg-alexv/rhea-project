#!/usr/bin/env bash
set -euo pipefail

# Rhea Ops Setup — installs a project operations layer:
# - ./rhea CLI (runtime)
# - scripts/rhea/* implementation
# - Taskfile.yml
# - .githooks + git hooksPath
# - entire.io-compatible logs/snapshots in .entire/
#
# Flags:
#   --dry-run     Show actions without writing
#   --no-hooks    Do not set git hooksPath
#   --no-task     Do not write Taskfile.yml
#
# Env:
#   RHEA_EXPERIMENTAL=1  Enable stricter checks / hook behavior

DRY_RUN=0
NO_HOOKS=0
NO_TASK=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --no-hooks) NO_HOOKS=1 ;;
    --no-task) NO_TASK=1 ;;
    *) echo "Unknown flag: $arg" >&2; exit 1 ;;
  esac
done

say() { printf "\n== %s ==\n" "$1"; }
run() {
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "DRY-RUN: $*"
  else
    eval "$@"
  fi
}
need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1" >&2; exit 1; }; }

repo_root_guard() {
  [ -d ".git" ] || { echo "Run from repo root (missing .git)." >&2; exit 1; }
}

write_file() {
  local path="$1"; shift
  if [ -z "${1:-}" ]; then
    echo "Internal error: empty write_file payload for $path" >&2
    exit 1
  fi
  echo "write: $path"
  if [ "$DRY_RUN" -eq 0 ]; then
    mkdir -p "$(dirname "$path")"
    cat > "$path" <<EOF
$*
EOF
  fi
}

write_if_missing() {
  local path="$1"; shift
  if [ -f "$path" ]; then
    echo "exists: $path"
  else
    write_file "$path" "$*"
  fi
}

append_gitignore_once() {
  local line="$1"
  local file=".gitignore"
  if [ ! -f "$file" ]; then
    write_file "$file" "# Rhea .gitignore"
  fi
  if ! grep -qxF "$line" "$file" 2>/dev/null; then
    echo "gitignore: add $line"
    if [ "$DRY_RUN" -eq 0 ]; then
      printf "%s\n" "$line" >> "$file"
    fi
  fi
}

say "Preflight"
need git
need python3
repo_root_guard

echo "Repo:   $(basename "$(pwd)")"
echo "Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"

say "Canonical dirs"
run "mkdir -p docs prompts src scripts scripts/rhea .githooks .rhea/cli .entire/logs .entire/snapshots"

say "Normalize .gitignore"
append_gitignore_once ""
append_gitignore_once "# Python"
append_gitignore_once ".venv/"
append_gitignore_once "__pycache__/"
append_gitignore_once "*.pyc"
append_gitignore_once ".pytest_cache/"
append_gitignore_once ""
append_gitignore_once "# macOS"
append_gitignore_once ".DS_Store"
append_gitignore_once ""
append_gitignore_once "# Env"
append_gitignore_once ".env"
append_gitignore_once ""
append_gitignore_once "# Rhea ops"
append_gitignore_once ".entire/logs/*.tmp"
append_gitignore_once ".rhea/local/"
append_gitignore_once ""

say "entire.io logging helpers"
write_if_missing "scripts/rhea/lib_entire.sh" \
'#!/usr/bin/env bash
set -euo pipefail

ENTIRE_DIR="${ENTIRE_DIR:-.entire}"
LOG_DIR="$ENTIRE_DIR/logs"
SNAP_DIR="$ENTIRE_DIR/snapshots"
OPS_LOG="$LOG_DIR/ops.jsonl"

mkdir -p "$LOG_DIR" "$SNAP_DIR"

iso_now() {
  # RFC3339-ish
  if command -v python3 >/dev/null 2>&1; then
    python3 - <<PY
from datetime import datetime, timezone
print(datetime.now().astimezone().isoformat(timespec="seconds"))
PY
  else
    date +"%Y-%m-%dT%H:%M:%S%z"
  fi
}

git_head() {
  git rev-parse --short HEAD 2>/dev/null || echo "no-git"
}

json_escape() {
  python3 - <<PY
import json,sys
print(json.dumps(sys.stdin.read())[1:-1])
PY
}

log_event() {
  local cmd="$1"; shift || true
  local status="${1:-ok}"
  local msg="${2:-}"
  local ts head
  ts="$(iso_now)"
  head="$(git_head)"
  mkdir -p "$LOG_DIR"
  # msg is optional; keep minimal
  if [ -n "$msg" ]; then
    printf "{\"ts\":\"%s\",\"git\":\"%s\",\"cmd\":\"%s\",\"status\":\"%s\",\"msg\":\"%s\"}\n" \
      "$ts" "$head" "$cmd" "$status" "$(printf "%s" "$msg" | json_escape)" >> "$OPS_LOG"
  else
    printf "{\"ts\":\"%s\",\"git\":\"%s\",\"cmd\":\"%s\",\"status\":\"%s\"}\n" \
      "$ts" "$head" "$cmd" "$status" >> "$OPS_LOG"
  fi
}

snapshot_repo_state() {
  local label="${1:-STATE}"
  local ts head out
  ts="$(iso_now | tr ":" "-" | tr "+" "_")"
  head="$(git_head)"
  out="$SNAP_DIR/${label}-${ts}-${head}.json"

  python3 - <<PY > "$out"
import json, subprocess, os
def sh(cmd):
  return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()

snap = {
  "label": "${label}",
  "git": sh("git rev-parse --short HEAD") if os.path.isdir(".git") else None,
  "branch": sh("git rev-parse --abbrev-ref HEAD") if os.path.isdir(".git") else None,
  "status_porcelain": sh("git status --porcelain") if os.path.isdir(".git") else None,
  "files": {
    "state_md": open("docs/state.md","r",encoding="utf-8").read() if os.path.exists("docs/state.md") else (open("state.md","r",encoding="utf-8").read() if os.path.exists("state.md") else None),
    "decisions_md": open("docs/decisions.md","r",encoding="utf-8").read() if os.path.exists("docs/decisions.md") else (open("decisions.md","r",encoding="utf-8").read() if os.path.exists("decisions.md") else None),
    "architecture_md": open("docs/architecture.md","r",encoding="utf-8").read() if os.path.exists("docs/architecture.md") else (open("architecture.md","r",encoding="utf-8").read() if os.path.exists("architecture.md") else None),
  }
}
print(json.dumps(snap, ensure_ascii=False, indent=2))
PY

  echo "snapshot: $out"
}
'

run "chmod +x scripts/rhea/lib_entire.sh"

say "Core ops scripts"
write_if_missing "scripts/rhea/bootstrap.sh" \
'#!/usr/bin/env bash
set -euo pipefail
# Rhea bootstrap: normalize repo structure and (optionally) import nested content.

ROOT="$(pwd)"
EXPERIMENTAL="${RHEA_EXPERIMENTAL:-0}"

# shellcheck disable=SC1091
source "scripts/rhea/lib_entire.sh"

DRY_RUN=0
IMPORT_NESTED=1
KEEP_NESTED=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --no-import) IMPORT_NESTED=0 ;;
    --keep-nested) KEEP_NESTED=1 ;;
    *) echo "Unknown arg: $arg" >&2; exit 1 ;;
  esac
done

run() { if [ "$DRY_RUN" -eq 1 ]; then echo "DRY-RUN: $*"; else eval "$@"; fi; }

timestamp() { date +"%Y%m%d-%H%M%S"; }

move_file_safe() {
  local src="$1" dest_dir="$2"
  [ -f "$src" ] || return 0
  run "mkdir -p \"$dest_dir\""
  local base dest
  base="$(basename "$src")"
  dest="$dest_dir/$base"

  if [ -f "$dest" ]; then
    if cmp -s "$src" "$dest"; then
      run "rm -f \"$src\""
    else
      local ts newname
      ts="$(timestamp)"
      newname="$dest_dir/${base}.nested-$ts"
      run "mv \"$src\" \"$newname\""
    fi
  else
    run "mv \"$src\" \"$dest\""
  fi
}

move_tree_files_safe() {
  local src_root="$1" dest_root="$2"
  [ -d "$src_root" ] || return 0
  while IFS= read -r -d "" f; do
    local rel dest_dir
    rel="${f#$src_root/}"
    dest_dir="$dest_root/$(dirname "$rel")"
    move_file_safe "$f" "$dest_dir"
  done < <(find "$src_root" -type f -print0)

  if [ "$KEEP_NESTED" -eq 0 ]; then
    run "find \"$src_root\" -type d -empty -delete 2>/dev/null || true"
  fi
}

mkdir -p docs prompts src scripts .entire/logs .entire/snapshots

# Ensure README.md exists in root (GitHub wants it)
if [ ! -f "README.md" ]; then
  if [ -f "rhea-project/README.md" ]; then
    run "cp rhea-project/README.md README.md"
  else
    cat > README.md <<EOF
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
EOF
  fi
fi

# Import nested docs/prompts, if present
if [ "$IMPORT_NESTED" -eq 1 ]; then
  # Sources: prefer rhea-project/, else _staging_nested/
  if [ -d "rhea-project/docs" ]; then move_tree_files_safe "rhea-project/docs" "docs"; fi
  if [ -d "rhea-project/prompts" ]; then move_tree_files_safe "rhea-project/prompts" "prompts"; fi

  if [ -d "_staging_nested/docs" ]; then move_tree_files_safe "_staging_nested/docs" "docs"; fi
  if [ -d "_staging_nested/prompts" ]; then move_tree_files_safe "_staging_nested/prompts" "prompts"; fi
fi

# Ensure skeleton docs exist
mkdir -p docs
[ -f docs/MVP_LOOP.md ] || cat > docs/MVP_LOOP.md <<EOF
# MVP_LOOP — Closed-Loop Scheduler Spec (Draft)

## Goal
Rhea proposes the next best action under uncertainty, not a perfect schedule.

## State x_t (minimal)
- sleep_proxy
- energy
- time_budget
- friction

## Action set A (MVP)
- micro-interventions (2–5 min)
- tasks (10–60 min)
- recovery actions

## Reward / Utility
- completion
- strain penalty
- agency score

## Safety constraints
- minimum viable day
- bounds on context switches
- recovery floor for low sleep_proxy

## Online updates
- Bayesian duration update
- completion probability update
- bandit policy

## Logging schema
- timestamp, state snapshot, proposed action, taken action, duration, outcome
EOF

[ -f docs/ROADMAP.md ] || cat > docs/ROADMAP.md <<EOF
# Roadmap

## Stage 0 — Specs + controller skeleton
- Finalize MVP_LOOP
- Define log schema
- Minimal simulation harness

## Stage 1 — iOS MVP
- SwiftUI shell
- 10-second check-in
- Local-only persistence

## Stage 2 — Passive signals
- HealthKit / Watch
- Feature extraction

## Stage 3 — Optimization (MPC)
- Replanning under uncertainty
- Hard constraints + safe defaults
EOF

# Guard: remove tracked .venv from index (if any)
if git ls-files --error-unmatch .venv >/dev/null 2>&1; then
  run "git rm -r --cached .venv"
fi

log_event "rhea bootstrap" "ok" "normalized structure; import_nested=$IMPORT_NESTED"
if [ "$EXPERIMENTAL" = "1" ]; then
  snapshot_repo_state "BOOTSTRAP"
fi

echo "OK: bootstrap complete"
git status --porcelain || true
'

write_if_missing "scripts/rhea/check.sh" \
'#!/usr/bin/env bash
set -euo pipefail
# Rhea checks: enforce repo invariants + basic hygiene.

EXPERIMENTAL="${RHEA_EXPERIMENTAL:-0}"

# shellcheck disable=SC1091
source "scripts/rhea/lib_entire.sh"

fail() { echo "FAIL: $*" >&2; log_event "rhea check" "fail" "$*"; exit 1; }
warn() { echo "WARN: $*" >&2; }

# 1) Block common trash from being tracked
if git ls-files | grep -qE "^\.venv/"; then
  fail ".venv is tracked. Remove with: git rm -r --cached .venv"
fi
if git ls-files | grep -qE "^\.env$"; then
  fail ".env is tracked. Remove it; use .env.example"
fi

# 2) State size guard (keep it small & inspectable)
STATE_PATH=""
if [ -f "docs/state.md" ]; then STATE_PATH="docs/state.md"; elif [ -f "state.md" ]; then STATE_PATH="state.md"; fi
if [ -n "$STATE_PATH" ]; then
  bytes="$(wc -c < "$STATE_PATH" | tr -d " ")"
  # default 2048 bytes guard; experimental: 1500
  limit=2048
  if [ "$EXPERIMENTAL" = "1" ]; then limit=1500; fi
  if [ "$bytes" -gt "$limit" ]; then
    fail "$STATE_PATH too large (${bytes}B > ${limit}B). Keep state concise."
  fi
else
  warn "state.md not found (docs/state.md or state.md)."
fi

# 3) Ensure root README exists for GitHub
[ -f "README.md" ] || fail "README.md missing in repo root."

# 4) Basic nested-dup warning
if [ -d "rhea-project" ]; then
  warn "Nested dir rhea-project/ exists. Consider importing and removing to avoid duplicates."
fi
if [ -d "_staging_nested" ]; then
  warn "_staging_nested/ exists. Consider importing or cleaning up."
fi

log_event "rhea check" "ok" "invariants ok"
echo "OK: checks passed"
'

write_if_missing "scripts/rhea/import_nested.sh" \
'#!/usr/bin/env bash
set -euo pipefail
# Explicit import of nested content into root docs/ prompts/

# shellcheck disable=SC1091
source "scripts/rhea/lib_entire.sh"

DRY_RUN=0
KEEP_NESTED=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --keep-nested) KEEP_NESTED=1 ;;
    *) echo "Unknown arg: $arg" >&2; exit 1 ;;
  esac
done

run() { if [ "$DRY_RUN" -eq 1 ]; then echo "DRY-RUN: $*"; else eval "$@"; fi; }
timestamp() { date +"%Y%m%d-%H%M%S"; }

move_file_safe() {
  local src="$1" dest_dir="$2"
  [ -f "$src" ] || return 0
  run "mkdir -p \"$dest_dir\""
  local base dest
  base="$(basename "$src")"
  dest="$dest_dir/$base"
  if [ -f "$dest" ]; then
    if cmp -s "$src" "$dest"; then
      run "rm -f \"$src\""
    else
      local ts newname
      ts="$(timestamp)"
      newname="$dest_dir/${base}.nested-$ts"
      run "mv \"$src\" \"$newname\""
    fi
  else
    run "mv \"$src\" \"$dest\""
  fi
}

move_tree_files_safe() {
  local src_root="$1" dest_root="$2"
  [ -d "$src_root" ] || return 0
  while IFS= read -r -d "" f; do
    local rel dest_dir
    rel="${f#$src_root/}"
    dest_dir="$dest_root/$(dirname "$rel")"
    move_file_safe "$f" "$dest_dir"
  done < <(find "$src_root" -type f -print0)
  if [ "$KEEP_NESTED" -eq 0 ]; then
    run "find \"$src_root\" -type d -empty -delete 2>/dev/null || true"
  fi
}

mkdir -p docs prompts

# Import from both possible locations
move_tree_files_safe "rhea-project/docs" "docs"
move_tree_files_safe "rhea-project/prompts" "prompts"
move_tree_files_safe "_staging_nested/docs" "docs"
move_tree_files_safe "_staging_nested/prompts" "prompts"

log_event "rhea import-nested" "ok" "imported nested docs/prompts"
echo "OK: imported nested content"
git status --porcelain || true
'

write_if_missing "scripts/rhea/memory.sh" \
'#!/usr/bin/env bash
set -euo pipefail
# Rhea memory ops (entire.io-friendly):
#   ./rhea memory snapshot [LABEL]
#   ./rhea memory log "message"

# shellcheck disable=SC1091
source "scripts/rhea/lib_entire.sh"

cmd="${1:-}"
shift || true

case "$cmd" in
  snapshot)
    label="${1:-STATE}"
    snapshot_repo_state "$label"
    log_event "rhea memory snapshot" "ok" "$label"
    ;;
  log)
    msg="${1:-}"
    [ -n "$msg" ] || { echo "Usage: ./rhea memory log \"message\"" >&2; exit 1; }
    log_event "rhea memory log" "ok" "$msg"
    echo "logged"
    ;;
  *)
    echo "Usage:"
    echo "  ./rhea memory snapshot [LABEL]"
    echo "  ./rhea memory log \"message\""
    exit 1
    ;;
esac
'

run "chmod +x scripts/rhea/"*.sh scripts/rhea/lib_entire.sh

say "Project CLI: ./rhea"
write_file "rhea" \
'#!/usr/bin/env bash
set -euo pipefail

# Rhea Project CLI (runtime)
# This is intentionally hand-written and stable.
# A Bashly config scaffold lives in .rhea/cli/ for future generation if desired.

cmd="${1:-}"
shift || true

case "$cmd" in
  bootstrap)
    exec scripts/rhea/bootstrap.sh "$@"
    ;;
  import-nested)
    exec scripts/rhea/import_nested.sh "$@"
    ;;
  check)
    exec scripts/rhea/check.sh "$@"
    ;;
  memory)
    exec scripts/rhea/memory.sh "$@"
    ;;
  help|--help|-h|"")
    cat <<'EOF'
Rhea CLI

Commands:
  bootstrap [--dry-run] [--no-import] [--keep-nested]
  import-nested [--dry-run] [--keep-nested]
  check
  memory snapshot [LABEL]
  memory log "message"

Env:
  RHEA_EXPERIMENTAL=1   stricter checks + auto snapshots on bootstrap
EOF
    ;;
  *)
    echo "Unknown command: $cmd" >&2
    echo "Run: ./rhea help" >&2
    exit 1
    ;;
esac
'
run "chmod +x rhea"

say "Bashly scaffold (optional generator source)"
# We keep it as a scaffold. Runtime does NOT depend on Bashly.
write_if_missing ".rhea/cli/bashly.yml" \
'app_name: rhea
help: "Rhea Project CLI"
version: "0.1.0"

commands:
  - name: bootstrap
    help: "Normalize repo + import nested content"
  - name: import-nested
    help: "Import nested docs/prompts into root"
  - name: check
    help: "Run repo invariant checks"
  - name: memory
    help: "entire.io-friendly memory ops"
    commands:
      - name: snapshot
        help: "Write snapshot to .entire/snapshots"
      - name: log
        help: "Write log event to .entire/logs/ops.jsonl"
'

say "Git hooks"
write_if_missing ".githooks/pre-commit" \
'#!/usr/bin/env bash
set -euo pipefail

# Fast invariants before commit
./rhea check

# Optional: snapshot on commit when experimental
if [ "${RHEA_EXPERIMENTAL:-0}" = "1" ]; then
  ./rhea memory snapshot "PRECOMMIT" >/dev/null || true
fi
'
write_if_missing ".githooks/pre-push" \
'#!/usr/bin/env bash
set -euo pipefail

# Ensure invariants before push
./rhea check

# Optional: snapshot on push when experimental
if [ "${RHEA_EXPERIMENTAL:-0}" = "1" ]; then
  ./rhea memory snapshot "PREPUSH" >/dev/null || true
fi
'
run "chmod +x .githooks/pre-commit .githooks/pre-push"

if [ "$NO_HOOKS" -eq 0 ]; then
  echo "git: set core.hooksPath=.githooks"
  run "git config core.hooksPath .githooks"
else
  echo "skip hooks (--no-hooks)"
fi

say "Taskfile.yml (go-task) — optional"
if [ "$NO_TASK" -eq 0 ]; then
  write_if_missing "Taskfile.yml" \
'version: "3"

tasks:
  bootstrap:
    desc: "Normalize repo + import nested content"
    cmds:
      - ./rhea bootstrap

  import:
    desc: "Import nested docs/prompts into root"
    cmds:
      - ./rhea import-nested

  check:
    desc: "Run invariant checks"
    cmds:
      - ./rhea check

  snap:
    desc: "Write entire.io snapshot"
    cmds:
      - ./rhea memory snapshot

  log:
    desc: "Write entire.io log event (use: task log -- \"message\")"
    cmds:
      - ./rhea memory log "{{.CLI_ARGS}}"
'
else
  echo "skip Taskfile (--no-task)"
fi

say "Done"
echo "Try:"
echo "  ./rhea bootstrap"
echo "  ./rhea check"
echo "  ./rhea memory snapshot BOOT"
echo
echo "Status:"
git status --porcelain || true
