#!/bin/bash
# Rhea Ontology Explorer — Launcher
# Usage: bash rhea-ontology-explorer/run.sh [port]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PORT="${1:-8420}"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║       RHEA ONTOLOGY EXPLORER v0.1                ║"
echo "║  Cross-Disciplinary Hypothesis Engine            ║"
echo "║                                                  ║"
echo "║  3-Layer Verification:                           ║"
echo "║    1. Multi-model consensus (Rhea Bridge)        ║"
echo "║    2. Formal proof hooks (Lean4/Z3)              ║"
echo "║    3. Red-team adversarial agents                ║"
echo "║                                                  ║"
echo "║  Mathematical Universes (extensible):            ║"
echo "║    • Category Theory   • Information Geometry    ║"
echo "║    • Dynamical Systems • Game Theory             ║"
echo "║    • Proof Theory      • [your plugin here]      ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

cd "$PROJECT_ROOT"

# Ensure data directory exists
mkdir -p rhea-ontology-explorer/data

# Launch server
exec python3 rhea-ontology-explorer/server.py --port "$PORT"
