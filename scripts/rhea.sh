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
  
  # Ops — full control plane
  ops)       python3 src/rhea_ops.py "$@" ;;
  org)       python3 src/rhea_ops.py org "$@" ;;
  fly)       python3 src/rhea_ops.py fly "$@" ;;
  api)       python3 src/rhea_ops.py api "$@" ;;
  monitor)   python3 src/rhea_ops.py monitor "$@" ;;

  # Audit & Safety
  audit)
             log_info "Verifying Audit Ledger..."
             python3 ops/rex_pager.py verify
             log_info "Recent Audit Reports:"
             ls -lt docs/audit/ | head -n 3
             ;;
    # Safety
    mode)
               m="${1:-show}"
               if [ "$m" = "developer" ]; then
                   log_info "Mode: DEVELOPER (4-layer Holography Active)."
               elif [ "$m" = "user" ]; then
                   log_info "Mode: USER (Space Odyssey Active)."
               else
                   log_info "Usage: rhea mode [developer|user]"
               fi
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
    echo "rhea — unified control plane (v3.0)"
    echo "Usage: rhea <command> [args]"
    echo ""
    echo "Control Plane (rhea-ops):"
    echo "  ops [subcommand]      Full CLI (run 'rhea ops --help' for all)"
    echo "  org status            All repos with licenses, topics, stars"
    echo "  org license [--fix]   Audit/fix MIT license across org"
    echo "  org create NAME       Create new repo in org"
    echo "  org topics REPO [t…]  View/set repo topics"
    echo "  fly status            Fly.io machine status"
    echo "  fly deploy            Deploy to Fly.io"
    echo "  fly secrets           List/set/unset secrets"
    echo "  fly logs              Tail cloud logs"
    echo "  fly ssh [cmd]         SSH into Fly machine"
    echo "  api health            Health check (local + cloud)"
    echo "  api tribunal CLAIM    Submit claim for verification"
    echo "  api history [-n 20]   Query session history"
    echo "  api radio [-n 30]     Query radio feed"
    echo "  api agents            Agent roster and status"
    echo "  api office [-n 20]    Office messages"
    echo "  api governor          Token budgets and spending"
    echo "  monitor [--interval]  Live terminal dashboard"
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
    echo "  commit MSG            Quick commit + push"
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
