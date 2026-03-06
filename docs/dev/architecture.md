# Architecture Overview

## Design Principle

**Determinism through causality, not time.**

Rhea orders messages by logical sequence (Lamport clocks), not physical time (wall-clocks). This eliminates clock-dependent failures and guarantees all devices converge to identical message order.

## System Diagram

```
┌─────────────┐
│   Device A  │    Create session, add message
│ (Phone)     │    → Send to server
├─────────────┤    ← Get Lamport clock back
│ LocalTruth  │    Store locally (LC=1)
│ (SQLite)    │
└──────┬──────┘
       │
       │ HTTP/WebSocket
       ↓
┌─────────────────┐
│  Rhea Server    │    Receive message
│                 │    → Assign LC=1
│ - Sessions      │    → Store
│ - Messages      │    ← Return to device
│ - LC counter    │
└────────┬────────┘
       ↑
       │ HTTP/WebSocket
       │
┌──────┴──────┐
│   Device B  │    Retrieve session
│  (Laptop)   │    → Get all messages
├─────────────┤    ← Messages sorted by LC
│ LocalTruth  │    Store locally
│ (SQLite)    │    (LC=1, LC=2, LC=3...)
└─────────────┘
```

## Message Lifecycle

### 1. Client Creates Message

```rust
client.add_message(&session, "user", "Hello")
```

**Client state**: Message in-flight  
**Server state**: No change

### 2. Server Receives Message

Server receives message from Device A.

**Server logic**:
```
current_max_lc = 5
new_lc = current_max_lc + 1 = 6
Store message with LC=6
Return LC=6 to client
```

**Server state**: Message stored with LC=6  
**Client state**: Message queued for local storage

### 3. Client Stores Locally

Client receives response with LC=6.

```rust
local_truth.add_message(
    id,
    session_id,
    role,
    content,
    lamport_clock=6,  // From server
    device_id
)
```

**Client state**: Message in LocalTruth with LC=6

### 4. Device B Syncs

Device B connects and requests all messages in session.

**Server response**: All messages, sorted by LC
```json
[
  {"id": "...", "lamport_clock": 1, "content": "..."},
  {"id": "...", "lamport_clock": 2, "content": "..."},
  {"id": "...", "lamport_clock": 6, "content": "Hello"}
]
```

**Device B stores locally**, already sorted by LC.

**Result**: Both Device A and Device B have identical message order (by LC).

## Data Model

### Message Entity

```
Message {
  id: UUID                    // Unique forever
  session_id: UUID            // Parent session
  role: String                // "user" | "assistant"
  content: String             // Message text
  lamport_clock: u64          // Order (server-assigned, never changes)
  device_id: String           // Origin device
  created_at: i64             // Wall-clock (advisory only, ignore for ordering)
}
```

**Key property**: `lamport_clock` is immutable and globally unique per session.

### Session Entity

```
Session {
  id: UUID
  character: Enum             // PROTOS | ZERG | TERRAN | AEON
  title: String
  messages: Vec<Message>      // Ordered by lamport_clock
  created_at: i64
  updated_at: i64
  client_id: Option<String>
}
```

## Sync Algorithm

### Merge Messages (Idempotent)

When Device A syncs with server and receives messages from Device B:

```rust
pub fn merge_messages(&mut self, new_messages: Vec<Message>) {
    for msg in new_messages {
        // Step 1: Dedup by UUID
        if !self.messages.iter().any(|m| m.id == msg.id) {
            self.messages.push(msg);
        }
    }
    
    // Step 2: Sort by Lamport clock
    self.messages.sort_by_key(|m| m.lamport_clock);
}
```

**Properties**:
- **Idempotent**: Merging same messages twice produces same result
- **Commutative**: merge(A, B) = merge(B, A)
- **Associative**: merge(merge(A,B), C) = merge(A, merge(B,C))
- **Result**: Mathematical convergence guarantee

## Why This Works

### 1. Server is Single Authority

Only the server assigns Lamport clocks. No conflicts, no ambiguity.

```
Device A sends msg → Server assigns LC=5
Device B sends msg → Server assigns LC=6
Device C sends msg → Server assigns LC=7
```

All devices eventually learn: LC order is 5, 6, 7. Done.

### 2. Lamport Clocks are Deterministic

Same message always gets same LC. No randomness, no exceptions.

```
If Device B is offline when Device A sends a message,
the message still gets its assigned LC.
When Device B reconnects, it gets the same LC.
```

### 3. Append-Only Prevents Surprises

Messages never change. Once written, always true.

```
Device A sees: [msg1(LC=1), msg2(LC=2), msg3(LC=3)]
Device B sees: [msg1(LC=1), msg2(LC=2)]

Device B syncs with A.
Device B now sees: [msg1(LC=1), msg2(LC=2), msg3(LC=3)]

msg3 appears, but msg1 and msg2 don't change.
No surprises.
```

### 4. UUID Deduplication

Each message has a unique UUID. Sending twice = stored once.

```
Device A: send msg with UUID=abc
Server: returns LC=5

Network glitch, Device A retries with same UUID=abc
Server: recognizes UUID=abc already stored
Returns: same LC=5 (idempotent)
```

## Convergence Guarantee

**Theorem**: If all devices follow the merge algorithm and trust the server's Lamport clock assignments, all devices will converge to identical message order.

**Proof**: See [CRDT Convergence](./architecture/crdt.md)

**Time to convergence**: O(sync latency). Once all devices have synced, convergence is permanent (append-only).

## Limitations

| Limitation | Reason | Mitigation |
|-----------|--------|-----------|
| Single server | Must trust server | Run multiple servers with replication (Phase 2) |
| No Byzantine fault tolerance | Server could lie | Network security + audit logs |
| No confidentiality | All messages visible on server | End-to-end encryption (Phase 2) |
| Sequential LC assignment | Serialized bottleneck | Batch assignment or clock range allocation (Phase 2) |

## See Also

- [DTS: Deterministic Time System](./architecture/dts.md) — Lamport clock mechanics
- [CRDT Convergence](./architecture/crdt.md) — Convergence proofs
- [Design Philosophy](./architecture/philosophy.md) — Why this design

## References

- Lamport, L. (1978). "Time, Clocks, and the Ordering of Events in a Distributed System"
- Shapiro, M. et al. (2011). "Conflict-free Replicated Data Types"
