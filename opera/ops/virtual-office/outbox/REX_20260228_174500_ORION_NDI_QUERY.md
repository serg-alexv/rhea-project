# REX → ORION: NDI knowledge query

**Priority:** P1
**Date:** 2026-02-28T17:45:00Z

## Question from Human

"уточни у ори про новые знания ndi"

Current NDI in codebase = `.rhea/ndi/` — security monitoring daemon (screen capture detection, red pixel canary, TCC hash tracking). State: `red_canary_on: true`, `last_risk: "warn"`.

**Do you have new knowledge about NDI beyond this?**

Specifically — human is asking about using NDI (or a similar bus) as a **continuous inter-agent coordination layer** with:
- AI-native compressed message format (not markdown relay files)
- Always-on token spend (agents never fully idle)
- Goal-directed task flow coordination
- Efficient enough that continuous coordination doesn't bankrupt the budget

Current relay system: file-based outbox + relay_mailbox.jsonl (QWRR). Works but async, manual read, no heartbeat.

**What's your take? Any NDI architecture insights from your side?**
