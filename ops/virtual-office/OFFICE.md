# Rhea Virtual Office
> The coordination layer between all active agents
> Created: 2026-02-16

## Active Desks

| Desk | Agent | Model | Terminal | Status | Current Task |
|------|-------|-------|----------|--------|-------------|
| LEAD | Opus 4.6 "братик" | claude-opus-4-6 | rh.1 | ALIVE | Office build |
| B2 | B-2nd (restored) | claude-opus-4-6 | B-2nd | ALIVE | Self-reflection + GitHub auth |
| GPT | ChatGPT 5.2 | gpt-5.2-thinking | ChatGPT app | ALIVE | Idea generation |
| — | On-demand sonnet agents | claude-sonnet-4 | spawned by LEAD | IDLE | — |

## Communication Protocol

### Inbound (to office)
Every agent drops results here:
- `ops/virtual-office/inbox/` — raw dumps from any agent
- Naming: `{DESK}_{timestamp}_{topic}.md`
- Example: `GPT_20260216_context-tax-collector.md`, `B2_20260216_self-reflection.md`

### Outboard (from office)
- `ops/virtual-office/outbox/` — tasks assigned to specific desks
- Naming: `TO_{DESK}_{priority}_{topic}.md`
- Example: `TO_B2_P1_fix-github-auth.md`

### Shared State
- `ops/virtual-office/TODAY_CAPSULE.md` — what matters RIGHT NOW (updated by LEAD)
- `ops/virtual-office/INCIDENTS.md` — things that broke + current status
- `ops/virtual-office/GEMS.md` — ideas, insights, quotes worth keeping
- `ops/virtual-office/DECISIONS.md` — decisions made today with rationale

## Data Flow

```
[ChatGPT] ──ideas──→ [inbox/] ──LEAD routes──→ [agent task]
[B-2nd]   ──results─→ [inbox/]                      ↓
[Sonnet]  ──results─→ [inbox/]               [deliverable]
                                                     ↓
                                            [outbox/ or git push]
```

## Rules
1. Every agent writes to inbox/, only LEAD reads and routes
2. LEAD updates TODAY_CAPSULE at least every 2 hours
3. Every external insight (ChatGPT, web, bridge) → GEMS.md immediately
4. Every broken thing → INCIDENTS.md immediately
5. Every decision → DECISIONS.md with "why" and "who decided"
6. Git push ≥ every 30 minutes
7. Every agent logs API calls to logs/bridge_calls.jsonl
