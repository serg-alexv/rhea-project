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

# 4) System health — check for stuck processes
if command -v rhea-health &>/dev/null; then
  STATUS_FILE="$HOME/.rhea/health-status.json"
  if [ -f "$STATUS_FILE" ]; then
    tracking=$(python3 -c "import json; print(json.load(open('$STATUS_FILE'))['tracking'])" 2>/dev/null || echo "0")
    if [ "$tracking" -gt 5 ]; then
      warn "rhea-health tracking $tracking CPU hogs — system under load"
    fi
    # Check for stuck Apple daemons specifically
    stuck=$(python3 -c "
import json
d = json.load(open('$STATUS_FILE'))
bad = [w for w in d.get('watched',[]) if w['strikes'] >= 3 and w['cpu'] > 80]
for b in bad: print(f\"  {b['name']} pid={b['pid']} cpu={b['cpu']:.0f}% strikes={b['strikes']}\")
" 2>/dev/null || true)
    if [ -n "$stuck" ]; then
      warn "Stuck processes detected (rhea-health will auto-restart):"
      echo "$stuck" >&2
    fi
  fi
  # Verify daemon is running
  if ! launchctl list 2>/dev/null | grep -q "com.rhea.health"; then
    warn "rhea-health daemon not running. Load: launchctl load ~/Library/LaunchAgents/com.rhea.health.plist"
  fi
fi

log_event "rhea check" "ok" "invariants ok"
echo "OK: checks passed"
