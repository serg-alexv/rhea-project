#!/bin/bash
# Entire checkpoint commit — uses Claude Code CLI to trigger Entire session detection
# Usage: ./scripts/entire_commit.sh "commit message"

set -e
cd "$(git rev-parse --show-toplevel)"

MSG="${1:-chore: checkpoint update}"

# Use Claude Code to make the commit — Entire detects the session
claude -p \
  --dangerously-skip-permissions \
  --allowedTools "Bash(git:*)" \
  --model sonnet \
  --no-session-persistence \
  "Run exactly this git commit command, do not change the message: git commit -m \"$MSG\""
