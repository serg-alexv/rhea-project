# Message API Reference

Messages are immutable events in a session. Each message is assigned a Lamport clock by the server to ensure deterministic ordering across all devices.

## Overview

```
Message = {
  id: UUID,                     // Unique forever
  session_id: UUID,             // Parent session
  role: "user" | "assistant",   // Who said it
  content: String,              // What was said
  lamport_clock: u64,           // Causal order (assigned by server)
  device_id: String,            // Which device created it
  created_at: i64,              // Wall-clock timestamp (advisory only)
}
```

**Key principle**: `lamport_clock` is the source of truth for ordering. `created_at` is purely advisory and can be ignored.

## Add Message

Add a message to a session.

**Endpoint**:
```
POST /sessions/{session_id}/messages
```

**Request**:
```json
{
  "role": "user",
  "content": "What's the weather?",
  "device_id": "my-device-id"
}
```

**Response** (200 OK):
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440002",
  "lamport_clock": 7,
  "created_at": 1740000042,
  "content": "What's the weather?",
  "device_id": "my-device-id"
}
```

**Key observation**: Server returns `lamport_clock=7`. This is assigned sequentially by the server, independent of device clocks.

**Example** (Rust):
```rust
let response = client.add_message(&session_id, "user", "Hello!").await?;
println!("Message added with LC: {}", response.lamport_clock);
```

---

## Get Messages

Retrieve all messages in a session (ordered by Lamport clock).

**Endpoint**:
```
GET /sessions/{session_id}/messages
```

**Response** (200 OK):
```json
[
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
  },
  {
    "id": "850e8400-e29b-41d4-a716-446655440003",
    "role": "user",
    "content": "How are you?",
    "lamport_clock": 3,
    "device_id": "device-2",
    "created_at": 1740000005
  }
]
```

**Messages are sorted by `lamport_clock`**, not `created_at`. Notice device-2's message (created_at=1740000005) appears after device-1's messages because its lamport_clock is higher.

**Example** (Rust):
```rust
let messages = client.get_local_messages(&session_id).await?;
for (id, role, content, lc) in messages {
    println!("[LC:{}] {}: {}", lc, role, content);
}
// Output:
// [LC:1] user: Hello, Rhea!
// [LC:2] assistant: Hi there!
// [LC:3] user: How are you?
```

---

## Message Properties

### Lamport Clock (LC)

The `lamport_clock` field is the **only source of truth for ordering**.

- **Assigned by server**: Monotonically increasing (1, 2, 3, ...)
- **Never changes**: Once assigned, LC is immutable
- **Independent of time**: Devices with wrong clocks still converge
- **Example scenario**:
  - Device A (clock is 2 hours slow) adds message → Server assigns LC=5
  - Device B (clock is 1 hour fast) adds message → Server assigns LC=6
  - Result: Both devices see the same order (5, then 6), despite clock differences

### Device ID

The `device_id` field identifies which device created the message:
- Used for offline handling (when device is disconnected)
- Used for conflict detection (rarely needed with Lamport clocks)
- Visible for audit trails

### UUID Uniqueness

Each message has a unique UUID. Adding the same message twice is idempotent:
```rust
// Add message A
let msg_a = client.add_message(&session, "user", "Hello").await?;

// Network glitch, retry with same message
// Client re-sends with same UUID
let msg_a2 = client.add_message(&session, "user", "Hello").await?;

// Result: Message appears once, not twice (idempotent)
// Both calls return same lamport_clock
assert_eq!(msg_a.lamport_clock, msg_a2.lamport_clock);
```

### Created At (Wall-Clock)

The `created_at` field is a wall-clock timestamp, for display purposes only. It should be **ignored for ordering**.

Why? Clocks can be:
- **Wrong**: Device hasn't synced with NTP
- **Skewed**: Different devices have different times
- **Non-monotonic**: DST, user changes time backwards

Use `lamport_clock` for ordering instead.

---

## Roles

Standard roles for messages:

| Role | Use |
|------|-----|
| `user` | User input or prompt |
| `assistant` | AI response or system output |

Add any role you want, but stick to these conventions for interoperability.

---

## Errors

| Status | Error | Meaning |
|--------|-------|---------|
| 200 | (none) | Message added successfully |
| 404 | `NotFound` | Session ID doesn't exist |
| 400 | `BadRequest` | Missing required field (role, content, device_id) |
| 500 | `ServerError` | Internal server error |

---

## Offline Handling

When a device is offline:

1. **Client queues messages locally** (in LocalTruth SQLite database)
2. **Messages are temporarily assigned local LC** (1, 2, 3...)
3. **When device reconnects**, server reassigns LC sequentially
4. **All devices converge** on the same final LC order

See [Offline Operation](../guides/offline.md) for details.

---

## See Also

- [Session API](./sessions.md) — Create and manage sessions
- [Cross-Device Sync](../guides/cross-device-sync.md) — Keep multiple devices in sync
- [DTS: Deterministic Time System](../architecture/dts.md) — Why Lamport clocks matter
