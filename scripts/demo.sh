#!/usr/bin/env bash
# demo.sh — One-command Rhea demo launcher
#
# Seeds demo data if not already present, starts the Ruliad Ontology Explorer
# (port 8420) and the Themis Console / rhead.py (port 8000), then shows URLs.
# Traps SIGINT (Ctrl-C) to cleanly kill both server processes.
#
# Usage:
#   bash scripts/demo.sh
#   bash scripts/demo.sh --clean   # wipe demo data then re-seed

set -euo pipefail

# ── Paths ──────────────────────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SEED_SCRIPT="$REPO_ROOT/scripts/seed_demo.py"
RULIAD_SERVER="$REPO_ROOT/friends/ruliad/explorer/server.py"
RHEAD_SERVER="$REPO_ROOT/src/rhead.py"
DB_PATH="$REPO_ROOT/data/proof.db"
LOGS_DIR="$REPO_ROOT/logs"

# graph.json path alignment:
#   seed_demo.py writes to: $REPO_ROOT/rhea-ontology-explorer/data/graph.json
#   server.py reads from:   $REPO_ROOT/friends/ruliad/rhea-ontology-explorer/data/graph.json
#   (server.py uses PROJECT_ROOT = parent of parent of server.py = friends/ruliad/)
SEED_GRAPH="$REPO_ROOT/rhea-ontology-explorer/data/graph.json"
SERVER_GRAPH_DIR="$REPO_ROOT/friends/ruliad/rhea-ontology-explorer/data"
SERVER_GRAPH="$SERVER_GRAPH_DIR/graph.json"

RULIAD_PORT=8420
THEMIS_PORT=8000

# ── PIDs for cleanup ───────────────────────────────────────────────────
RULIAD_PID=""
THEMIS_PID=""

cleanup() {
    echo ""
    echo "  Shutting down servers..."
    if [[ -n "$RULIAD_PID" ]] && kill -0 "$RULIAD_PID" 2>/dev/null; then
        kill "$RULIAD_PID"
        echo "  Ruliad Explorer stopped (PID $RULIAD_PID)"
    fi
    if [[ -n "$THEMIS_PID" ]] && kill -0 "$THEMIS_PID" 2>/dev/null; then
        kill "$THEMIS_PID"
        echo "  Themis Console stopped  (PID $THEMIS_PID)"
    fi
    echo "  Done."
    exit 0
}

trap cleanup SIGINT SIGTERM

# ── Ensure logs dir ────────────────────────────────────────────────────
mkdir -p "$LOGS_DIR"

# ── Banner ─────────────────────────────────────────────────────────────
echo ""
echo "  ╔════════════════════════════════════════════════════╗"
echo "  ║            RHEA DEMO LAUNCHER                      ║"
echo "  ╚════════════════════════════════════════════════════╝"
echo ""

# ── Optional --clean flag ──────────────────────────────────────────────
if [[ "${1:-}" == "--clean" ]]; then
    echo "  [clean] Wiping existing demo data..."
    python3 "$SEED_SCRIPT" --clean
    echo ""
fi

# ── Step 1: Seed demo data if not already present ─────────────────────
echo "  [1/4] Checking demo data..."

# Check for sentinel proof ID: demo_chrono_melatonin_01
DEMO_IN_DB=$(python3 -c "
import sqlite3, sys
db = sys.argv[1]
try:
    conn = sqlite3.connect(db)
    row = conn.execute(\"SELECT id FROM proofs WHERE id = 'demo_chrono_melatonin_01'\").fetchone()
    conn.close()
    print('1' if row else '0')
except Exception:
    print('0')
" "$DB_PATH" 2>/dev/null || echo "0")

if [[ "$DEMO_IN_DB" == "1" ]]; then
    echo "  [1/4] Demo data already present — skipping seed."
else
    echo "  [1/4] Seeding demo data (Aletheia + Ruliad)..."
    python3 "$SEED_SCRIPT"
fi

# ── Step 2: Sync seeded graph.json to server's expected location ───────
# seed_demo.py writes:  $REPO_ROOT/rhea-ontology-explorer/data/graph.json
# server.py expects:    $REPO_ROOT/friends/ruliad/rhea-ontology-explorer/data/graph.json
echo ""
echo "  [2/4] Syncing Ruliad graph to server path..."
if [[ -f "$SEED_GRAPH" ]]; then
    mkdir -p "$SERVER_GRAPH_DIR"
    cp "$SEED_GRAPH" "$SERVER_GRAPH"
    HYP_COUNT=$(python3 -c "
import json, sys
with open(sys.argv[1]) as f:
    g = json.load(f)
print(len(g.get('hypotheses', {})))
" "$SERVER_GRAPH")
    echo "  [2/4] graph.json synced — $HYP_COUNT hypotheses ready."
else
    echo "  [2/4] WARNING: seeded graph not found at $SEED_GRAPH"
    echo "         Ruliad Explorer will start with an empty graph."
fi

# ── Step 3: Start Ruliad Ontology Explorer ─────────────────────────────
echo ""
echo "  [3/4] Starting Ruliad Ontology Explorer on port $RULIAD_PORT..."
python3 "$RULIAD_SERVER" --port "$RULIAD_PORT" \
    >"$LOGS_DIR/ruliad.log" 2>&1 &
RULIAD_PID=$!

# Brief wait and liveness check
sleep 1
if ! kill -0 "$RULIAD_PID" 2>/dev/null; then
    echo "  ERROR: Ruliad Explorer failed to start. Tail of log:"
    tail -20 "$LOGS_DIR/ruliad.log" || true
    exit 1
fi
echo "  [3/4] Ruliad Explorer running (PID $RULIAD_PID)"

# ── Step 4: Start Themis Console (rhead.py) ────────────────────────────
echo ""
echo "  [4/4] Starting Themis Console on port $THEMIS_PORT..."

# Load .env if present (rhead.py needs API keys, DB URLs, etc.)
if [[ -f "$REPO_ROOT/.env" ]]; then
    set -o allexport
    # shellcheck source=/dev/null
    source "$REPO_ROOT/.env"
    set +o allexport
fi

python3 "$RHEAD_SERVER" \
    >"$LOGS_DIR/themis.log" 2>&1 &
THEMIS_PID=$!

sleep 2
if ! kill -0 "$THEMIS_PID" 2>/dev/null; then
    echo "  ERROR: Themis Console failed to start. Tail of log:"
    tail -20 "$LOGS_DIR/themis.log" || true
    cleanup
    exit 1
fi
echo "  [4/4] Themis Console running (PID $THEMIS_PID)"

# ── URLs ───────────────────────────────────────────────────────────────
echo ""
echo "  ╔════════════════════════════════════════════════════════╗"
echo "  ║  DEMO READY                                            ║"
echo "  ║                                                        ║"
echo "  ║  Ruliad Ontology Explorer:                             ║"
echo "  ║    http://localhost:${RULIAD_PORT}                         ║"
echo "  ║    http://localhost:${RULIAD_PORT}/api/graph  (viz JSON)   ║"
echo "  ║                                                        ║"
echo "  ║  Themis Console (Aletheia + Tribunal):                 ║"
echo "  ║    http://localhost:${THEMIS_PORT}                         ║"
echo "  ║    http://localhost:${THEMIS_PORT}/aletheia/stats           ║"
echo "  ║    http://localhost:${THEMIS_PORT}/aletheia/recent          ║"
echo "  ║                                                        ║"
echo "  ║  Logs:                                                 ║"
echo "  ║    $LOGS_DIR/ruliad.log  ║"
echo "  ║    $LOGS_DIR/themis.log  ║"
echo "  ║                                                        ║"
echo "  ║  Press Ctrl-C to stop both servers.                   ║"
echo "  ╚════════════════════════════════════════════════════════╝"
echo ""

# ── Wait until SIGINT / SIGTERM ────────────────────────────────────────
wait
