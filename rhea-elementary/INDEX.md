# Rhea Elementary — Session Knowledge Base

Extracted 2026-02-16 from a session that automated Chrome to remove 25+ claude.ai MCP connectors causing context bloat.

## Files

| File | What | When to use |
|------|------|-------------|
| [chrome-automation.md](chrome-automation.md) | AppleScript + JS patterns for controlling Chrome | Any browser automation from terminal |
| [claude-ai-api-map.md](claude-ai-api-map.md) | Claude.ai internal API endpoints | Account management, debugging, scripting |
| [context-bloat-diagnosis.md](context-bloat-diagnosis.md) | How MCP connectors eat context | Claude feels slow or hits limits |
| [spa-reverse-engineering.md](spa-reverse-engineering.md) | Generic technique to discover any webapp's API | Need to automate or script any web app |
| [react-ui-automation.md](react-ui-automation.md) | Clicking buttons in React/Radix UI apps | Automating modern web UIs |
| [industry-leader-90-days-ru.md](industry-leader-90-days-ru.md) | 25 hard tactics for AI industry leadership (RU) | When you need fire, not motivation |
| [external_qdai_assistant.md](external_qdai_assistant.md) | Q-Doc identity: short + full versions | Bootstrap any new session as Agent 1 |

## Quick Reference

```bash
# Enable Chrome JS access (one-time):
# Chrome > View > Developer > Allow JavaScript from Apple Events

# Test it works:
osascript -e 'tell application "Google Chrome" to execute front window'\''s active tab javascript "document.title"'
```

## Origin Story
Claude.ai account had 25+ MCP server connectors injecting ~250 tool definitions (~50K tokens) into every conversation. Diagnosed via system prompt inspection, fixed by automating Chrome to click through Remove > Disconnect on each connector via AppleScript-driven JavaScript execution.
