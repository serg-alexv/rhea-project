#!/usr/bin/env bash
# carbonyl_browse.sh — Terminal web browser for headless agent sessions
# Usage: bash scripts/carbonyl_browse.sh [url]
# Requires: carbonyl (npm install -g carbonyl)
#
# Purpose: Provides visual web browsing over SSH/tmux for agents
# that need to see rendered pages (not just scraped markdown).
# For scraping, use firecrawl instead.

set -euo pipefail

CARBONYL_BIN="/opt/homebrew/lib/node_modules/carbonyl/node_modules/@fathyb/carbonyl-macos-arm64/build/carbonyl"
URL="${1:-https://example.com}"

if [ ! -f "$CARBONYL_BIN" ]; then
    echo "[carbonyl] Not installed. Run: npm install -g carbonyl"
    exit 1
fi

# Check for TTY
if [ ! -t 0 ]; then
    echo "[carbonyl] Requires interactive terminal (TTY). Use in tmux/ssh."
    echo "[carbonyl] For non-interactive scraping, use: firecrawl scrape \"$URL\""
    exit 1
fi

exec "$CARBONYL_BIN" --fps=30 --zoom=100 "$URL"
