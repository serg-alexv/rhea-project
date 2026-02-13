#!/usr/bin/env bash
set -euo pipefail

EXPERIMENTAL="${RHEA_EXPERIMENTAL:-0}"

# shellcheck disable=SC1091
source "scripts/rhea/lib_entire.sh"

fail(){ echo "FAIL: $*" >&2; log_event "rhea check" "fail" "$*"; exit 1; }
warn(){ echo "WARN: $*" >&2; }

# 1) .venv и .env не должны быть в git
if git ls-files | grep -qE '^\.venv/'; then
  fail ".venv is tracked. Run: git rm -r --cached .venv"
fi
if git ls-files | grep -qE '^\.env$'; then
  fail ".env is tracked. Remove it; use .env.example"
fi

# 2) README
[ -f README.md ] || warn "README.md missing in root (GitHub будет показывать 'Add a README')."

# 3) размер state.md
STATE=""
if [ -f docs/state.md ]; then
  STATE="docs/state.md"
elif [ -f state.md ]; then
  STATE="state.md"
fi

if [ -n "$STATE" ]; then
  bytes="$(wc -c < "$STATE" | tr -d ' ')"
  limit=2048
  [ "$EXPERIMENTAL" = "1" ] && limit=1500
  if [ "$bytes" -gt "$limit" ]; then
    fail "$STATE too large (${bytes}B > ${limit}B)"
  fi
else
  warn "state.md not found"
fi

log_event "rhea check" "ok" "invariants ok"
echo "OK: checks passed"
