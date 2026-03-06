---
sidebar_position: 2
---

# Characters — The Four Archetypes

Rhea sessions are organized around four character archetypes, each representing a different cognitive style and interaction pattern.

## The Four Characters

| Character | Symbol | Name | Style |
|-----------|--------|------|-------|
| **Protos** | ⚙️ | PROTOS | Systematic, analytical, mechanical precision |
| **Zerg** | 🧬 | ZERG | Adaptive, biological, evolutionary thinking |
| **Terran** | 🔧 | TERRAN | Practical, engineering-focused, building |
| **Aeon** | ✨ | AEON | Philosophical, temporal, deep time perspective |

## Implementation

Characters are defined as a Rust enum in the session server:

```rust
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub enum Character {
    Protos,
    Zerg,
    Terran,
    Aeon,
}
```

Each character has a `symbol()` and `name()` method. Sessions are created with a specific character:

```bash
curl -X POST http://127.0.0.1:3000/sessions \
  -H "Content-Type: application/json" \
  -d '{"character": "Aeon"}'
```

## Salon Conversations

The Tribunal API's `/salon/ask` endpoint enables character-driven conversations where different characters provide responses in their characteristic style:

```bash
curl -X POST http://localhost:8400/salon/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-bypass" \
  -d '{"prompt": "What matters in the long run?", "character": "Aeon"}'
```

`GET /salon/characters` returns the available character list.

## Design Philosophy

The character system serves multiple purposes:
1. **Session organization** — different characters for different cognitive tasks
2. **Interaction framing** — each archetype encourages a different thinking style
3. **Visual identity** — emoji symbols provide instant recognition in UI
4. **Future personalization** — characters can develop distinct response patterns based on session history
