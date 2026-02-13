#!/usr/bin/env bash
set -euo pipefail

trap 'echo "ERROR on line $LINENO"; exit 1' ERR

DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    *) echo "Unknown flag: $arg" >&2; exit 1 ;;
  esac
done

say(){ printf "\n== %s ==\n" "$1"; }
run(){ if [ "$DRY_RUN" -eq 1 ]; then echo "DRY-RUN: $*"; else eval "$@"; fi; }

[ -d .git ] || { echo "Run from repo root (missing .git)" >&2; exit 1; }

say "Create directories"
run "mkdir -p docs prompts src scripts scripts/rhea .githooks .entire/logs .entire/snapshots .rhea/local"

say "Normalize .gitignore"
if [ ! -f .gitignore ]; then run "printf '%s\n' '# Rhea .gitignore' > .gitignore"; fi
add_ignore(){ grep -qxF "$1" .gitignore 2>/dev/null || run "printf '%s\n' '$1' >> .gitignore"; }
add_ignore ""
add_ignore "# Python"
add_ignore ".venv/"
add_ignore "__pycache__/"
add_ignore "*.pyc"
add_ignore ".pytest_cache/"
add_ignore ""
add_ignore "# macOS"
add_ignore ".DS_Store"
add_ignore ""
add_ignore "# Env"
add_ignore ".env"
add_ignore ""
add_ignore "# Rhea ops"
add_ignore ".rhea/local/"
add_ignore ".entire/logs/*.tmp"
add_ignore ""

say "Write scripts/rhea/lib_entire.sh"
cat > scripts/rhea/lib_entire.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

ENTIRE_DIR="${ENTIRE_DIR:-.entire}"
LOG_DIR="$ENTIRE_DIR/logs"
SNAP_DIR="$ENTIRE_DIR/snapshots"
OPS_LOG="$LOG_DIR/ops.jsonl"

mkdir -p "$LOG_DIR" "$SNAP_DIR"

iso_now() {
  python3 - <<PY
from datetime import datetime
print(datetime.now().astimezone().isoformat(timespec="seconds"))
PY
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

def read(p):
  return open(p,"r",encoding="utf-8").read() if os.path.exists(p) else None

snap = {
  "label": "${label}",
  "git": sh("git rev-parse --short HEAD") if os.path.isdir(".git") else None,
  "branch": sh("git rev-parse --abbrev-ref HEAD") if os.path.isdir(".git") else None,
  "status_porcelain": sh("git status --porcelain") if os.path.isdir(".git") else None,
  "files": {
    "docs_state": read("docs/state.md"),
    "root_state": read("state.md"),
    "docs_decisions": read("docs/decisions.md"),
    "root_decisions": read("decisions.md"),
    "docs_architecture": read("docs/architecture.md"),
    "root_architecture": read("architecture.md"),
  }
}
print(json.dumps(snap, ensure_ascii=False, indent=2))
PY

  echo "snapshot: $out"
}
EOF
run "chmod +x scripts/rhea/lib_entire.sh"

say "Write scripts/rhea/import_nested.sh"
cat > scripts/rhea/import_nested.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
# Import nested docs/prompts into root docs/ prompts/ safely.

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

run(){ if [ "$DRY_RUN" -eq 1 ]; then echo "DRY-RUN: $*"; else eval "$@"; fi; }
ts(){ date +"%Y%m%d-%H%M%S"; }

move_file_safe(){
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
      local new="$dest_dir/${base}.nested-$(ts)"
      run "mv \"$src\" \"$new\""
    fi
  else
    run "mv \"$src\" \"$dest\""
  fi
}

import_tree(){
  local from="$1" to="$2"
  [ -d "$from" ] || return 0
  while IFS= read -r -d '' f; do
    local rel dest_dir
    rel="${f#$from/}"
    dest_dir="$to/$(dirname "$rel")"
    move_file_safe "$f" "$dest_dir"
  done < <(find "$from" -type f -print0)

  if [ "$KEEP_NESTED" -eq 0 ]; then
    run "find \"$from\" -type d -empty -delete 2>/dev/null || true"
  fi
}

run "mkdir -p docs prompts"
import_tree "rhea-project/docs" "docs"
import_tree "rhea-project/prompts" "prompts"
import_tree "_staging_nested/docs" "docs"
import_tree "_staging_nested/prompts" "prompts"

log_event "rhea import-nested" "ok" "imported nested content"
echo "OK: imported nested content"
git status --porcelain || true
EOF
run "chmod +x scripts/rhea/import_nested.sh"

say "Write scripts/rhea/check.sh"
cat > scripts/rhea/check.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
EXPERIMENTAL="${RHEA_EXPERIMENTAL:-0}"

# shellcheck disable=SC1091
source "scripts/rhea/lib_entire.sh"

fail(){ echo "FAIL: $*" >&2; log_event "rhea check" "fail" "$*"; exit 1; }
warn(){ echo "WARN: $*" >&2; }

# Block tracked venv / env
if git ls-files | grep -qE '^\.venv/'; then fail ".venv tracked. Run: git rm -r --cached .venv"; fi
if git ls-files | grep -qE '^\.env$'; then fail ".env tracked. Use .env.example"; fi

# README must exist
[ -f "README.md" ] || warn "README.md missing in root (GitHub will show 'Add a README')."

# State size guard
STATE=""
if [ -f docs/state.md ]; then STATE="docs/state.md"; elif [ -f state.md ]; then STATE="state.md"; fi
if [ -n "$STATE" ]; then
  bytes="$(wc -c < "$STATE" | tr -d ' ')"
  limit=2048
  [ "$EXPERIMENTAL" = "1" ] && limit=1500
  [ "$bytes" -le "$limit" ] || fail "$STATE too large (${bytes}B > ${limit}B)"
else
  warn "state.md not found"
fi

log_event "rhea check" "ok" "invariants ok"
echo "OK: checks passed"
EOF
run "chmod +x scripts/rhea/check.sh"

say "Write scripts/rhea/bootstrap.sh"
cat > scripts/rhea/bootstrap.sh <<'EOF'
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

# Root README for GitHub
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

# Import nested content
if [ "$NO_IMPORT" -eq 0 ]; then
  # pass KEEP_NESTED via env var-style
  if [ "$KEEP_NESTED" -eq 1 ]; then
    run "./scripts/rhea/import_nested.sh --keep-nested"
  else
    run "./scripts/rhea/import_nested.sh"
  fi
fi

# Skeleton docs if missing
[ -f docs/MVP_LOOP.md ] || cat > docs/MVP_LOOP.md <<'M'
# MVP_LOOP — Closed-Loop Scheduler Spec (Draft)
(define: state x_t, actions A, reward, constraints, updates, logging)
M
[ -f docs/ROADMAP.md ] || cat > docs/ROADMAP.md <<'M'
# ROADMAP
(stage 0..3)
M

# Remove tracked .venv from index if present
if git ls-files --error-unmatch .venv >/dev/null 2>&1; then
  run "git rm -r --cached .venv"
fi

log_event "rhea bootstrap" "ok" "normalized + imported=$((1-NO_IMPORT))"
[ "$EXPERIMENTAL" = "1" ] && snapshot_repo_state "BOOTSTRAP"
echo "OK: bootstrap done"
git status --porcelain || true
EOF
run "chmod +x scripts/rhea/bootstrap.sh"

say "Write scripts/rhea/memory.sh"
cat > scripts/rhea/memory.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC1091
source "scripts/rhea/lib_entire.sh"

sub="${1:-}"; shift || true
case "$sub" in
  snapshot)
    snapshot_repo_state "${1:-STATE}"
    log_event "rhea memory snapshot" "ok" "${1:-STATE}"
    ;;
  log)
    msg="${1:-}"
    [ -n "$msg" ] || { echo 'Usage: ./rhea memory log "message"' >&2; exit 1; }
    log_event "rhea memory log" "ok" "$msg"
    echo "logged"
    ;;
  *)
    echo "Usage:"
    echo "  ./rhea memory snapshot [LABEL]"
    echo '  ./rhea memory log "message"'
    exit 1
    ;;
esac
EOF
run "chmod +x scripts/rhea/memory.sh"

say "Write ./rhea CLI"
cat > rhea <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

cmd="${1:-}"; shift || true
case "$cmd" in
  bootstrap) exec scripts/rhea/bootstrap.sh "$@" ;;
  import-nested) exec scripts/rhea/import_nested.sh "$@" ;;
  check) exec scripts/rhea/check.sh "$@" ;;
  memory) exec scripts/rhea/memory.sh "$@" ;;
  help|--help|-h|"")
    cat <<'H'
Rhea CLI

Commands:
  ./rhea bootstrap [--dry-run] [--no-import] [--keep-nested]
  ./rhea import-nested [--dry-run] [--keep-nested]
  ./rhea check
  ./rhea memory snapshot [LABEL]
  ./rhea memory log "message"

Env:
  RHEA_EXPERIMENTAL=1   stricter checks + snapshots on bootstrap
H
    ;;
  *) echo "Unknown command: $cmd" >&2; exit 1 ;;
esac
EOF
run "chmod +x rhea"

say "Git hooks"
cat > .githooks/pre-commit <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
./rhea check
[ "${RHEA_EXPERIMENTAL:-0}" = "1" ] && ./rhea memory snapshot "PRECOMMIT" >/dev/null || true
EOF

cat > .githooks/pre-push <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
./rhea check
[ "${RHEA_EXPERIMENTAL:-0}" = "1" ] && ./rhea memory snapshot "PREPUSH" >/dev/null || true
EOF
run "chmod +x .githooks/pre-commit .githooks/pre-push"

echo "git: set core.hooksPath=.githooks"
run "git config core.hooksPath .githooks"

say "Verification"
if [ "$DRY_RUN" -eq 0 ]; then
  ./rhea help >/dev/null
  echo "OK: ./rhea is runnable"
fi

say "Status"
git status --porcelain || true
