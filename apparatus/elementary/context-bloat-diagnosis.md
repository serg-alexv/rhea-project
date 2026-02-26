# Claude.ai Context Bloat: Diagnosis & Fix

## The Problem
Claude.ai conversations hit context limits or feel slow even with short prompts.

## Root Cause
Server-side MCP connectors (Settings > Connectors) inject tool definitions into EVERY conversation:
- Each connector adds 5-50 tool definitions
- Each tool definition is ~100-300 tokens
- 25 connectors = ~25,000-75,000 tokens of invisible overhead
- Affects ALL platforms: web, desktop app, iOS, Claude Code (shared account config)

## Diagnosis Checklist
1. Check `claude.ai/settings/connectors` — count "Configure" and "Connected" items
2. In Claude Code, look for `mcp__claude_ai_*` in the deferred tools list in system prompt
3. Symptoms:
   - "context too long" errors
   - Slow responses on short conversations
   - Truncated/compressed conversations earlier than expected
   - Claude Code sessions feeling heavy from the start

## Fix
1. Remove all connectors at `claude.ai/settings/connectors`
2. For each: click `...` > Remove > Disconnect (confirm dialog)
3. Or automate via Chrome JS (see chrome-automation.md)
4. Re-add selectively only when needed for a specific task

## Connector Types
- **Sync services** (Gmail, Google Calendar, GitHub, Google Drive): "Connected" status, managed via sync/settings API
- **MCP servers** (Ahrefs, Slack, Linear, Figma, etc.): "Configure" status, ~250+ tool definitions injected as deferred tools
- **OAuth integrations** (Chrome extension, Claude Code): separate token-based system

## Prevention
- Don't "Browse connectors" and enable everything that looks interesting
- Each connector has a real token cost on every conversation
- Audit connectors quarterly
