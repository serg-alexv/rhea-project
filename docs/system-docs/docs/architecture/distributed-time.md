---
sidebar_position: 3
---

# Distributed Time

> *"Time has no meaning. Signals are everything."*

Rhea does not rely on synchronized wall clocks. Instead, it uses **Lamport clocks** and **causal ordering** to establish event sequences across devices.

## Why Not Wall Clocks?

In a system spanning phones, laptops, and cloud servers across timezones:
- NTP drift can reach seconds on mobile devices
- Users travel across timezones
- Offline periods create gaps in wall-clock sequences
- "What happened first?" is a causal question, not a clock question

## Lamport Clocks in Sessions

Every message in a session carries a `lamport_clock` value:

```rust
pub struct Message {
    pub id: Uuid,
    pub session_id: Uuid,
    pub role: String,
    pub content: String,
    pub created_at: i64,        // wall-clock timestamp (informational only)
    pub device_id: String,      // which device sent this
    pub lamport_clock: u64,     // causal ordering
}
```

### Increment Rule

When adding a message to a session, the Lamport clock is computed as:

```rust
let lc = self.messages.last()
    .map(|m| m.lamport_clock)
    .unwrap_or(0) + 1;
```

Each new message gets `max(local_clock, last_seen_clock) + 1`. In the current implementation, this simplifies to `last_message_clock + 1` since messages are appended sequentially within a session.

## Hash-Chain Ordering in 0.log

The [event bus](/docs/architecture/event-bus) provides a second form of causal ordering: each frame's `prev_hash` links it to its predecessor. This creates a **tamper-evident total order** of all local events, regardless of wall-clock accuracy.

```
Frame₁ ─hash→ Frame₂ ─hash→ Frame₃ ─hash→ ...
```

Even if timestamps are wrong, the hash chain proves ordering.

## Device Identification

Every message and event carries a `device_id`, enabling conflict resolution when the same session is accessed from multiple devices:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "...",
  "role": "user",
  "content": "What about melatonin timing?",
  "device_id": "iphone-14-pro",
  "lamport_clock": 42
}
```

## Future: CRDT Sync

The session server's `Session` struct is designed for eventual CRDT-based sync:
- `client_id: Option<String>` field on sessions for multi-client tracking
- `KeystrokeEvent` struct with `device_id` for fine-grained input tracking
- Messages are append-only within a session — a natural fit for grow-only sets (G-Sets)

**Status:** Lamport clocks are implemented and active. Full CRDT merge is planned but not yet implemented.

## DTS in Practice

The Distributed Time System (DTS) philosophy permeates the design:

| Component | Time Mechanism |
|-----------|---------------|
| Session messages | Lamport clocks |
| 0.log frames | Hash-chain (causal linking) |
| Tribunal responses | `elapsed_s` relative timing |
| Office messages | ISO 8601 timestamps (informational) |
| Bridge call logs | Wall-clock + `latency_s` (performance measurement) |

Wall-clock timestamps are stored for human readability, but **ordering decisions always use causal mechanisms** (Lamport clocks or hash chains).
