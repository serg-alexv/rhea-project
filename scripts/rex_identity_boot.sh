#!/bin/bash
# Rex Identity Boot — runs on SessionStart
# Outputs personality + learning feed as context injection
# This makes Rex load identity AUTOMATICALLY, not by choice.

PERSONALITY="rhea-elementary/memory-core/personality.md"
LEARNING_FEED="ops/virtual-office/shared/LEARNING_FEED.md"
STATE="docs/state.md"

echo "=== REX IDENTITY (auto-loaded) ==="
if [ -f "$PERSONALITY" ]; then
    cat "$PERSONALITY"
fi
echo ""
echo "=== LEARNING FEED (auto-loaded) ==="
if [ -f "$LEARNING_FEED" ]; then
    cat "$LEARNING_FEED"
fi
echo ""
echo "=== COMPACT STATE (auto-loaded) ==="
if [ -f "$STATE" ]; then
    cat "$STATE"
fi
echo "=== END BOOT CONTEXT ==="
