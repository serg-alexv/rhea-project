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
echo ""
echo "=== MEMORY FEED [compact] (auto-generated) ==="
# Regenerate feed fresh on every boot — 1 second, ~1200 tokens, all memory deduped
python3 src/memory_feed.py 2>/dev/null || echo "(feed generation failed — read opera/memory/FEED.compact if exists)"
echo "=== END BOOT CONTEXT ==="
