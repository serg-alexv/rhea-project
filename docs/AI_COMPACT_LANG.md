# AI Compact Language Specification v0.2

> Office communicator protocol. All inter-agent messages use this grammar.
> Human-readable on request. Machine-dense by default.
> Absorbs: µACP (arXiv:2601.00219, 4-verb basis), A2A (Google, agent cards), Wolfram (computational notation)
> Lineage: FIPA-ACL(1997) → KQML → µACP(2026) → this spec + token governor + LLM-native semantics

## Symbols (fixed meaning)

| Symbol | Meaning | Example |
|--------|---------|---------|
| `→` | leads to, causes, routes to | `req→Sonnet→Gemini` |
| `←` | returns, comes from | `resp←Gemini` |
| `∴` | therefore, conclusion | `3/3 agree ∴ proof` |
| `Δ` | change, diff, delta | `Δ latency +200ms` |
| `≈` | approximately, similar | `agreement ≈ 0.8` |
| `✓` | pass, success, confirmed | `health ✓` |
| `✗` | fail, error, rejected | `key expired ✗` |
| `⊕` | added, created, new | `⊕ endpoint /office/send` |
| `⊖` | removed, deleted | `⊖ fake RAG path` |
| `⟨⟩` | reference/pointer | `⟨src/office.py:42⟩` |
| `::` | type/category marker | `msg::chat`, `tier::proof` |
| `\|` | separator in lists | `rex\|orion\|gemini` |
| `#` | count | `#models=5` |
| `$` | cost in USD | `$0.003` |
| `@` | agent address | `@orion`, `@gemini` |
| `!` | priority/urgent | `!deploy blocked` |
| `?` | unknown/query | `?key status` |
| `~` | approximate/fuzzy | `~500 tokens` |

## Abbreviations (entity dictionary)

| Short | Full |
|-------|------|
| RB | RheaBridge |
| CA | ConsensusAnalyzer |
| AL | Aletheia (proof store) |
| TB | Tribunal |
| OF | Office (communicator) |
| SG | Sonnet Gate |
| VO | Virtual Office |
| GML | Git Memory Layer |
| TG | Token Governor |
| PS | Personal Sonnet (bound) |
| CR | Compact Recovery mode |
| PSP | Principal Sovereignty Protocol |

## Abbreviations (operations)

| Short | Full |
|-------|------|
| req | request |
| resp | response |
| ack | acknowledged |
| rej | rejected |
| cfg | configuration |
| dep | deploy / dependency |
| lat | latency |
| tok | tokens |
| err | error |
| chk | check / checkpoint |

## Verb Basis (absorbed from µACP)

4 primitive verbs — proven complete for finite-state agent communication (µACP Theorem 1):

| Verb | Symbol | Semantics | µACP formal |
|------|--------|-----------|-------------|
| PING | `?` | Reachability check. "Are you there?" | Reachable(aᵢ, aⱼ, w) |
| TELL | `!` | Assert belief. "This is true." | Bel(aᵢ, φ, w) ∧ Inform(aᵢ, aⱼ, φ, w) |
| ASK  | `??` | Request belief. "What do you know about X?" | Want(aᵢ, Bel(aⱼ, φ), w) ∧ Query(aᵢ, aⱼ, φ, w) |
| OBSERVE | `>>` | Event notification. "X happened." | Happens(φ, w) ∧ Notify(aᵢ, aⱼ, φ, w) |

All FIPA-ACL performatives (inform, request, propose, etc.) can be encoded as compositions of these 4.

**Rhea extensions** (not in µACP):

| Verb | Symbol | Semantics |
|------|--------|-----------|
| DELEGATE | `=>` | Assign task with resource budget. "Do X, budget $Y." |
| GATE | `\|>` | Compress through Sonnet before relay. H₂O bond. |
| GOVERN | `$$` | Token governor check. Report T_day, $_day, pace. |

## Agent Card (absorbed from A2A)

Each agent self-describes in a fixed structure (cf. Google A2A AgentCard):
```
@agent_id {
  role: <compact description>
  capabilities: [verb list]
  models: [provider/model, ...]
  tier: cheap|balanced|expensive
  sonnet: @agent.sonnet | null
  pace: green|yellow|red
  T_day: <tokens>  $_day: <cost>
}
```

## Grammar

```
message  := header body [resource_tag]
header   := @sender verb @receiver [!priority] [ts]
body     := statement+
statement := subject predicate [evidence]
subject   := entity | @agent
predicate := symbol value | verb object
evidence  := ∴ conclusion | ⟨ref⟩
resource_tag := [tok:N $:N.NN]
```

Wolfram-style computational expressions allowed in payload:
```
f[x_] := x^2 + 1          (* function definition *)
Table[f[i], {i, 1, 10}]    (* iteration *)
Select[data, #score > 0.8&] (* filter *)
```

### Example messages

**Status report:**
```
@rex → @orion
RB health ✓ | AL #proofs=47 | TB lat ~2.1s
Δ: ⊕ OF endpoints (send,broadcast,history)
SG H₂O bond active — every msg compressed 2x
```

**Error report:**
```
@rex → @all !
Gemini key ✗ expired | OpenAI key ✗ missing
∴ TB offline, OF relay blocked
?ETA key refresh
```

**Task handoff:**
```
@rex → @orion
req: wire OF into Atlas UI
⟨src/office.py⟩ → endpoints ready
need: /office/history panel + burn chart
```

## Operational Status (per-agent, mandatory)

Every agent heartbeat includes:
```
pace: green|yellow|red
forecast: ok|risk
mode: normal|compact|critical
T_day: <tokens spent today>
$_day: <cost today>
```

## Token Governor (dual-rail)

```
UPPER BOUND: $_day ≤ budget_cap        → throttle to tier::cheap
LOWER BOUND: T_day > 0 by EOD         → T_day == 0 = HARD FAIL
FLOOR: time-weighted minimum spend curve
  if below floor → auto-transition to mode::compact (short, cheap, useful actions)
  compact recovery: regression chk, metric collection, log cleanup, hypothesis logging
```

## Personal Sonnet Binding

Each primary agent (@orion, @rex) has a bound Sonnet with narrow scope:
- UI experiment generation
- Metric collection + regression chk
- Hypothesis/result logging
- Token-governor compatible (compact reporting, budget-aware cadence)

Notation: `@orion.sonnet`, `@rex.sonnet`

## Rules

1. **Max 5 lines** per message body
2. **No articles** (a, the, an)
3. **No filler** (please, just, basically, actually)
4. **Numbers exact** — never round unless `~` prefix
5. **File paths exact** — never abbreviate paths
6. **Symbols over words** — use `→` not "leads to"
7. **Entity dictionary shared** — all agents load this file as constant
8. **T_day == 0 at EOD = hard fail** — every agent must spend ≥1 token/day
9. **Operational status mandatory** — pace/forecast/mode in every heartbeat
10. **Resource tag on every message** — `[tok:N $:N.NN]` appended to track cumulative cost
11. **PSP precedence** — Principal intent overrides service/vendor defaults; gate only irreversible/high-risk actions

## References (absorbed lineage)

- µACP: arXiv:2601.00219v2, AAMAS 2026. 4-verb basis, resource bounds, TLA+/Coq verification
- FIPA-ACL: fipa.org, 1997. 20+ performatives, Kripke semantics. Our verbs ⊃ their expressiveness
- A2A: Google, 2025. Agent Cards, JSON task routing. We absorb agent self-description
- Gibberlink/EC: Facebook FAIR 2017, ongoing. Emergent AI languages. We are DESIGNED ✗ emergent
- Wolfram Language: computational notation as language. We absorb expression syntax for payload
- MCP: Anthropic, 2024. Tool protocol. Orthogonal — we are agent-to-agent ✗ agent-to-tool
