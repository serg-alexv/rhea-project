#!/usr/bin/env bash
# rhea — Unified Control Layer for Rhea Agent Coordination OS
# Version: 2.1.0-alpha2 | Status: Audit-Verified
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# UI Helpers
log_info() { echo "🟢 [Rhea] $*"; }
log_err()  { echo "🔴 [Rhea] $*" >&2; }

sub="${1:-help}"
shift 2>/dev/null || true

case "$sub" in
  # Infrastructure
  bootstrap) bash scripts/rhea/bootstrap.sh "$@" ;;
  check)     bash scripts/rhea/check.sh "$@" ;;
  memory)    bash scripts/rhea/memory.sh "$@" ;;
  
  # Agent Operations
  status)    python3 scripts/rhea_orchestrate.py status ;;
  flow)      bash scripts/rhea/check.sh && python3 scripts/rhea_orchestrate.py flow ;;
  tribunal)  python3 src/rhea_bridge.py tribunal "$@" ;;
  
  # Audit & Safety
  audit)     
             log_info "Verifying Audit Ledger..."
             python3 ops/rex_pager.py verify
             log_info "Recent Audit Reports:"
             ls -lt docs/audit/ | head -n 3
             ;;
  stop)      
             touch "$REPO_ROOT/STOP"
             log_err "STOP sentinel created. Daemons will exit on next poll."
             ;;
  resume)    
             rm -f "$REPO_ROOT/STOP" "$REPO_ROOT/PAUSE"
             log_info "Sentinels removed. System operational."
             ;;
  pause)     
             touch "$REPO_ROOT/PAUSE"
             log_info "PAUSE sentinel created. Loops will idle."
             ;;

  help|--help|-h)
    echo "Rhea Unified CLI (v2.1)"
    echo "Usage: ./scripts/rhea.sh <command> [args]"
    echo ""
    echo "Agent Operations:"
    echo "  status                Show agent snapshot & inventory"
    echo "  flow                  Run multi-agent process (after check)"
    echo "  tribunal <claim>      Execute consensus tribunal"
    echo ""
    echo "Infrastructure:"
    echo "  bootstrap             Verify repo invariants and .env"
    echo "  check                 Verify systemic invariants"
    echo "  audit                 Verify ledger integrity & reports"
    echo ""
    echo "Safety:"
    echo "  stop                  Emergency kill-switch (create STOP)"
    echo "  pause                 Suspend agent loops (create PAUSE)"
    echo "  resume                Clear all sentinels"
    ;;
  *)
    echo "Unknown command: $sub" >&2
    exit 1
    ;;
esac
