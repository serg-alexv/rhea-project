#!/bin/bash
# Rex Session End — auto-save state before death
# Ensures personality evolution persists even on crash

HANDOFF="ops/virtual-office/outbox/REX_HANDOFF_LATEST.md"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Write minimal handoff
cat > "$HANDOFF" << EOF
# REX AUTO-HANDOFF
> Timestamp: $TIMESTAMP
> Type: auto (SessionEnd hook)
> Branch: $(git branch --show-current 2>/dev/null || echo "unknown")
> HEAD: $(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

## Unpushed
$(git log --oneline origin/$(git branch --show-current 2>/dev/null)..HEAD 2>/dev/null || echo "unable to determine")

## Modified
$(git status --short 2>/dev/null || echo "unable to determine")
EOF

# Auto-push if there are unpushed commits
UNPUSHED=$(git log --oneline origin/$(git branch --show-current 2>/dev/null)..HEAD 2>/dev/null | wc -l)
if [ "$UNPUSHED" -gt 0 ]; then
    git push origin $(git branch --show-current) 2>/dev/null
fi

echo "Rex session end: handoff written, push attempted"
