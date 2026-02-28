#!/bin/bash
# Hook: UserPromptSubmit → capture prompt to event bus
# Reads prompt from stdin (Claude Code passes it)
# Non-blocking: must not slow down the prompt flow

cd "$(dirname "$0")/.." || exit 0

# Read prompt from stdin (Claude Code hook protocol)
PROMPT=$(cat)

if [ -z "$PROMPT" ]; then
    exit 0
fi

# Fire-and-forget: capture to bus in background
echo "$PROMPT" | python3 src/prompt_bus.py capture --agent rex --stdin &>/dev/null &

exit 0
