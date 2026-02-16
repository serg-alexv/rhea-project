#!/usr/bin/env bash
# rhea — CLI dispatcher for scripts/rhea/*.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

sub="${1:-help}"
shift 2>/dev/null || true

case "$sub" in
  bootstrap) bash scripts/rhea/bootstrap.sh "$@" ;;
  check)     bash scripts/rhea/check.sh "$@" ;;
  memory)    bash scripts/rhea/memory.sh "$@" ;;
  help|--help|-h)
    echo "Usage: rhea <command> [args]"
    echo ""
    echo "Commands:"
    echo "  bootstrap [--dry-run] [--no-import] [--keep-nested]"
    echo "  check                 Verify repo invariants"
    echo "  memory snapshot|log   Manage snapshots and event logs"
    echo ""
    echo "See also:"
    echo "  scripts/rhea_autosave.sh   Auto-save daemon"
    echo "  scripts/rhea_commit.sh     Git commit with Entire lifecycle"
    echo "  scripts/rhea_orchestrate.py  Multi-agent orchestration"
    ;;
  *)
    echo "Unknown command: $sub" >&2
    echo "Run 'rhea help' for usage." >&2
    exit 1
    ;;
esac
