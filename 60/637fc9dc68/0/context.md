# Session Context

**Session ID:** 94aabe90-9b2d-48e7-be8c-6bf820a0b6a9

**Commit Message:** Explain me like i'm 6 years old

## Prompt

explain me like i'm 6 years old

## Summary

**Your app has 5 tabs + More:**

**Team** (Radio) — live feed of everything agents say to each other. Like a walkie-talkie log.
- Top toolbar: bubble icon switches to chat view, people icon opens agent list
- Agent list: see who's online, tap WAKE to poke them
- Bottom: type a message, all agents see it
- Tap any line to read the full message

**Atlas** — web view of your Next.js dashboard

**Governor** — how much each agent costs you today. Green dot = active, red = sleeping. Wake/Ping buttons on each card.

**Pulse** — system health. Are tasks stuck? Is anything broken? Mark Flicker, Wake Rex, Create Trace Task buttons.

**More** — Tasks list + Settings (API URL config)

**What just broke and got fixed:**
- Agent list said "Loading..." forever → decoder was silently failing → fixed, now shows 16 agents
- Keyboard wouldn't go away → now swipe the feed down or tap outside
- Governor had no buttons → now has Wake + Ping on every card

## Key Actions

