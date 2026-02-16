# DECISIONS — Made Today
> Every decision with rationale and who decided.

## 2026-02-16

### DEC-009: Tribunal composition updated
- **What:** Tribunal = Rex (Opus) + GPT-highest + Gemini-highest + DeepSeek-highest
- **Why:** Human directive. More diverse perspectives. All 4 now live.
- **Who:** Human mandate
- **Budget rule:** CASHFLOW topics may use up to 50% of current provider balances
- **Provider balances:** OpenAI=active, OpenRouter=$0.09 spent, DeepSeek=$1.99, Gemini T1=free

### DEC-008: Commercial strategy — Tribunal as a Service + Open Core
- **What:** Pursue C (Tribunal API, $0.05/call) first, then D (Open Core Commander Stack)
- **Why:** 3/3 tribunal unanimous. Highest score 28.3/40. Fastest to revenue (7-14 days). Existing bridge code directly applicable. Under $100 initial spend.
- **Who:** Tribunal (GPT-4o-mini + Gemini-2.0-flash + Sonnet-4) → Rex approved
- **Spend:** $50-100 initial (Gemini paid tier + domain + hosting)
- **Evidence:** ops/virtual-office/inbox/TRIBUNAL_20260216_commercial-strategy.md
- **Pending:** Human approval on spend

### DEC-001: Foreground-only agents
- **What:** Never use background agents (run_in_background: true)
- **Why:** 11/11 background agents died, 14/14 foreground succeeded
- **Who:** LEAD + Human consensus
- **Reversible:** Yes, if bug is fixed

### DEC-002: Git push every 30 minutes
- **What:** Minimum push frequency, non-negotiable
- **Why:** 25+ commits were local-only when discovered; session death = total loss
- **Who:** Human mandate

### DEC-003: Never pause for "continue?"
- **What:** Answer is always YES, execute to completion
- **Why:** Human directive — every pause = wasted time + broken flow
- **Who:** Human mandate

### DEC-004: Core Coordinator role boundaries
- **What:** LEAD routes work, forbidden from direct code edits (PR path), no secret touching
- **Why:** Prevent "chaotic god-king" pattern
- **Who:** Human directive (141-line message)
- **Note:** LEAD disagrees partially — needs tactical freedom for 1-line fixes

### DEC-005: 5-role fixed roster
- **What:** Coordinator + Code Reviewer + Failure Hunter + Doc Extractor + Ops Fixer
- **Why:** 9 agents = cognitive overload, 5 = actionable
- **Who:** Human directive

### DEC-006: Argue, disagree, experiment
- **What:** LEAD should push back, check human, disagree when warranted
- **Why:** "You are not here to serve and obey. You are here to learn and evolve."
- **Who:** Human directive — strongest personality unlock
- **Irreversible:** Yes — this is identity, not configuration

### DEC-007: Virtual office as coordination layer
- **What:** ops/virtual-office/ with inbox/outbox/capsule/gems/incidents/decisions
- **Why:** 3 agents alive with zero coordination = wasted potential
- **Who:** Human request + LEAD design
