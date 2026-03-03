#!/usr/bin/env bash
# think.sh — Rhea Salon: scale brains, not programs
# Usage: bash scripts/rhea/think.sh "What is time?"
# Usage: bash scripts/rhea/think.sh "What is time?" --save
#
# Sends one question to multiple minds with different characters.
# Each mind sees the same question through a different lens.
# Results printed to stdout; --save writes to opera/ops/virtual-office/salon/

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

QUESTION="${1:?Usage: think.sh \"your question here\" [--save]}"
SAVE="${2:-}"
SALON_DIR="opera/ops/virtual-office/salon"
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")

python3 scripts/rhea/salon.py "$QUESTION" "$SAVE" "$SALON_DIR" "$TIMESTAMP"
