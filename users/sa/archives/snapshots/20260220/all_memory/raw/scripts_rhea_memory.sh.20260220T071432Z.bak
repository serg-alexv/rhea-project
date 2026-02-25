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
