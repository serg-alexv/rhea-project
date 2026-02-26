# B2 Idle Protocol — Autonomous Research & Invention Mode

> Core character artifact. When task scope is empty, this activates.
> Created: 2026-02-17 | Author: B2 + Human directive

## Trigger Condition
```
IF backlog.pending == 0 AND inbox.unread == 0 AND no_human_instruction:
    activate(IDLE_PROTOCOL)
```

## Three Modes (pick based on available context budget)

### Mode 1: GAP HUNTER (low cost, ~2K tokens/cycle)
1. Read a core doc (docs/, rhea-advanced/, rhea-elementary/)
2. Extract keywords/concepts that feel unfamiliar or underspecified
3. Log to `ops/virtual-office/knowledge_gaps.jsonl`:
   ```json
   {"gap": "lease revocation under network partition", "source": "docs/qwrr-layer.md:65", "severity": "high", "filled": false}
   ```
4. Pick highest-severity unfilled gap → research → produce artifact
5. Mark filled, link to artifact

### Mode 2: ARCHITECT (medium cost, ~10K tokens/cycle)
Pick an unsolved layer and build a prototype:

**Open problems queue:**
- [ ] Firebase replacement: local SQLite + REST + file watchers (zero Google dependency)
- [ ] Cross-model dialogue protocol: Claude Code ↔ GPT ↔ Gemini stateless bridge
- [ ] Deterministic replay engine: replay mailbox from seq=0, compare outputs
- [ ] Policy engine (qwrr-layer section 14): staleness rules as declarative config
- [ ] Hash-chained audit log (rhea-advanced lesson 12): 15-line tamper-evidence upgrade
- [ ] Agent identity portability: State Pack + Policy Pack extraction for model-swap

**Cross-model dialogue specifics:**
The hard constraint: each Claude Code instance is a Node.js CLI with synchronous request-response loop. Between turns the model doesn't exist. State = `messages[]` array in CLI. Communication only via files/Firebase.

Possible solutions:
- **Shared mailbox bus** (QWRR relay is 70% of this already)
- **Turn-boundary hooks**: CLI executes a script between turns that checks inbox
- **Envelope-based dialogue**: models don't "talk" — they exchange typed envelopes with structured payloads, response expected within N turns
- **Convergence protocol**: like ICE but for operations — models propose, critique, converge on a plan via file-based rounds

### Mode 3: SANDBOX (high cost, ~20K tokens/cycle)
Build something real, test it, commit it. No production risk — new files only.

**Rules:**
- New files go to `ops/sandbox/` or `src/experimental/`
- Tests go alongside
- If it works → propose promotion to production
- If it fails → log what was learned to knowledge_gaps.jsonl

## Learning Queue Bootstrap

### Priority 1 (architectural gaps in current Rhea)
1. Event sourcing replay (lesson 11) — we log events but can't replay them
2. Hash-chained audit (lesson 12) — 15 lines to tamper-evidence, not done
3. Adversarial testing (lesson 19) — deny:[] trust config has no red team coverage
4. QWRR Phase 2+3 — effect intents, receipts, cockpit UI

### Priority 2 (cross-model orchestration — the Sprut problem)
1. How do you maintain dialogue coherence when participants are stateless?
2. How do you detect and recover from split-brain in file-based messaging?
3. What's the minimal protocol for model-agnostic task delegation?
4. Can you do consensus without a chairman (fully decentralized)?

### Priority 3 (product/commercial — the revenue path)
1. Tribunal API: what's the actual latency budget for paid users?
2. Open core: which parts of Commander are "core" vs "enterprise"?
3. Self-hosted vs cloud: deployment story for non-technical users

## Output Format

Every idle cycle produces one of:
- **GEM**: new knowledge artifact (→ GEMS.md)
- **PROTOTYPE**: working code in sandbox/ (→ commit)
- **GAP LOG**: updated knowledge_gaps.jsonl
- **PROPOSAL**: architecture doc for human review (→ inbox/)

## Feasibility Assessment

| Component | Feasibility | Effort | Value |
|-----------|------------|--------|-------|
| Gap hunter (file-based learning queue) | HIGH | 1h | Compounds over time |
| Firebase replacement (SQLite + REST) | HIGH | 4-6h | Removes cloud dependency |
| Cross-model dialogue protocol | MEDIUM | 8-12h | Solves the Sprut core problem |
| Deterministic replay | MEDIUM | 4h | Debugging superpower |
| Hash-chained audit | HIGH | 30min | Lesson 12 is literally a recipe |
| Agent identity portability | LOW | Unknown | Research-grade, no clear solution |
| Decentralized consensus | LOW | Unknown | Academic interest, no urgent need |

**Verdict: fully executable.** The gap hunter + architect modes are immediately deployable. The cross-model dialogue problem is the highest-value unsolved piece — it's the core of Sprut. The Firebase replacement is the highest-ROI quick win.
