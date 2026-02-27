# AI Compact Language Specification v0.1

> Office communicator protocol. All inter-agent messages use this grammar.
> Human-readable on request. Machine-dense by default.

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

## Grammar

```
message  := header body
header   := @sender → @receiver [!priority] [ts]
body     := statement+
statement := subject predicate [evidence]
subject   := entity | @agent
predicate := symbol value | verb object
evidence  := ∴ conclusion | ⟨ref⟩
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

## Rules

1. **Max 5 lines** per message body
2. **No articles** (a, the, an)
3. **No filler** (please, just, basically, actually)
4. **Numbers exact** — never round unless `~` prefix
5. **File paths exact** — never abbreviate paths
6. **Symbols over words** — use `→` not "leads to"
7. **Entity dictionary shared** — all agents load this file as constant
