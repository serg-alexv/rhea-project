#!/usr/bin/env bash
set -euo pipefail

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
ts() { date +"%Y%m%d-%H%M%S"; }

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
      local new="$dest_dir/${base}.nested-$(ts)"
      run "mv \"$src\" \"$new\""
    fi
  else
    run "mv \"$src\" \"$dest\""
  fi
}

import_tree() {
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

log_event "rhea import-nested" "ok" "imported nested docs/prompts"
echo "OK: imported nested content"
git status --porcelain || true
