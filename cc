#!/usr/bin/env bash
# Rhea Command Centre launcher
# Usage: ./cc [dev|build|run]
set -euo pipefail
DIR="$(cd "$(dirname "$0")/rhea-atlas" && pwd)"
CMD="${1:-dev}"

case "$CMD" in
  dev)
    echo "→ Starting Command Centre (dev mode)..."
    cd "$DIR" && npx tauri dev
    ;;
  build)
    echo "→ Building Command Centre binary..."
    cd "$DIR" && npx tauri build
    echo "→ Binary at: $DIR/src-tauri/target/release/bundle/"
    ;;
  run)
    BIN="$DIR/src-tauri/target/release/rhea-command-centre"
    if [[ -f "$BIN" ]]; then
      echo "→ Launching Command Centre..."
      "$BIN"
    else
      echo "No binary found. Run './cc build' first."
      exit 1
    fi
    ;;
  *)
    echo "Usage: ./cc [dev|build|run]"
    ;;
esac
