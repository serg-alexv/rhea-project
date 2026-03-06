# Session API Reference

Sessions are the core unit in Rhea. A session is an immutable, append-only stream of messages with deterministic convergence across devices.

## Overview

```
Session = {
  id: UUID,
  character: "PROTOS" | "ZERG" | "TERRAN" | "AEON",
  messages: [Message],  // append-only, ordered by lamport_clock
  created_at: i64,      // wall-clock timestamp (advisory only)
  updated_at: i64,      // wall-clock timestamp (advisory only)
}
```

**Key property**: All devices converge on the same message order, guaranteed by Lamport clocks.

## Create Session

Create a new session with a character archetype.

**Endpoint**:
```
POST /sessions
```

**Request**:
```json
{
  "character": "PROTOS"
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "character": "PROTOS",
  "title": "PROTOS session",
  "messages": [],
  "created_at": 1740000000,
  "updated_at": 1740000000,
  "client_id": null
}
```

**Example** (Rust):
```rust
let session = client.create_session("PROTOS").await?;
```

---

## Get Session

Retrieve a session and all its messages.

**Endpoint**:
```
GET /sessions/{session_id}
```

**Response** (200 OK):
```json
{
  "session": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "character": "PROTOS",
    "title": "PROTOS session",
    "messages": [
      {
        "id": "650e8400-e29b-41d4-a716-446655440001",
        "role": "user",
        "content": "Hello, Rhea!",
        "lamport_clock": 1,
        "device_id": "device-1",
        "created_at": 1740000001
      },
      {
        "id": "750e8400-e29b-41d4-a716-446655440002",
        "role": "assistant",
        "content": "Hi there!",
        "lamport_clock": 2,
        "device_id": "device-1",
        "created_at": 1740000002
      }
    ],
    "created_at": 1740000000,
    "updated_at": 1740000002
  },
  "messages": [ /* ... same as above ... */ ]
}
```

**Messages are ordered by `lamport_clock` (not `created_at`)**.

**Example** (Rust):
```rust
let session = client.get_session(&session_id).await?;
for (id, role, content, lc) in session.messages {
    println!("[LC:{}] {}: {}", lc, role, content);
}
```

---

## List Sessions

List all sessions for a device.

**Endpoint**:
```
GET /sessions
```

**Response** (200 OK):
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "character": "PROTOS",
    "title": "PROTOS session",
    "created_at": 1740000000,
    "updated_at": 1740000002
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "character": "ZERG",
    "title": "ZERG session",
    "created_at": 1740000100,
    "updated_at": 1740000105
  }
]
```

**Example** (Rust):
```rust
let sessions = client.get_local_sessions().await?;
for (id, character, title) in sessions {
    println!("{}: {} ({})", id, character, title);
}
```

---

## Key Properties

### Lamport Clock (LC)

Every message has a `lamport_clock` (u64):
- **Assigned by server**, monotonically increasing
- **Independent of wall-clock time** (devices can have wrong clocks)
- **Globally ordered**: All devices see messages in the same LC order
- **Example**: Messages with LC=1,2,3 will have that order on all devices, even if device clocks are off by hours

### Idempotent Merge

Adding the same message twice (same UUID) is safe:
```rust
// Add message (LC = 5)
client.add_message(&session, "user", "Hello").await?;

// Network glitch, client retries
client.add_message(&session, "user", "Hello").await?;  // Same UUID

// Result: Message added once, not duplicated
```

### Append-Only

Sessions are immutable after creation:
- ✅ Add messages
- ❌ No UPDATE or DELETE
- ❌ No editing past messages

This guarantees all devices converge.

---

## Character Archetypes

Rhea supports 4 character archetypes:

| Character | Symbol | Use Case |
|-----------|--------|----------|
| PROTOS | ⚙️ | Technical, precise, systematic |
| ZERG | 🧬 | Adaptive, biological, learning-focused |
| TERRAN | 🔧 | Practical, engineering, hands-on |
| AEON | ✨ | Visionary, long-term, philosophical |

Choose based on the tone you want for the session:
```rust
client.create_session("ZERG").await?;   // Adaptive
client.create_session("AEON").await?;   // Visionary
```

---

## Errors

| Status | Error | Meaning |
|--------|-------|---------|
| 201 | (none) | Session created |
| 200 | (none) | Session retrieved |
| 404 | `NotFound` | Session ID doesn't exist |
| 500 | `ServerError` | Internal server error |

---

## See Also

- [Message API](./messages.md) — Add and retrieve individual messages
- [Cross-Device Sync](../guides/cross-device-sync.md) — Keep multiple devices in sync
- [DTS: Deterministic Time System](../architecture/dts.md) — How Lamport clocks work
