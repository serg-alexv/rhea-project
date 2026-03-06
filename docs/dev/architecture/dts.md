# DTS: Deterministic Time System

Rhea's DTS solves the fundamental problem: **How do devices with different clocks agree on message order?**

## The Problem

Without DTS, you have chaos:

```
Device A (clock 2 hours slow):
  12:00 - Add message "Hello"
  12:01 - Add message "World"

Device B (clock correct):
  14:00 - Add message "Hello"
  14:01 - Add message "World"
```

If you order by wall-clock `created_at`:
- Device A sees: Hello (12:00), World (12:01)
- Device B sees: Hello (14:00), World (14:01)
- **Problem**: Same session, different order!

Devices never converge. The session is broken.

## The Solution: Lamport Clocks

**Lamport clocks** are logical timestamps that guarantee deterministic ordering, independent of physical time.

### How It Works

**Server assigns Lamport clocks sequentially**:

```
Message 1: "Hello"       → LC = 1
Message 2: "World"       → LC = 2
Message 3: "How are you" → LC = 3
```

**All devices order by LC, not wall-clock time**:

Device A: 1, 2, 3 ✓  
Device B: 1, 2, 3 ✓  
Device C: 1, 2, 3 ✓  

**All converge automatically.**

### The Formula

Server maintains: `current_max_lamport_clock`

When a message arrives:

```
new_lamport_clock = current_max_lamport_clock + 1
```

That's it. No complex logic needed.

### Why It Works

1. **Monotonic**: Each LC is strictly higher than the previous
2. **Deterministic**: No randomness, same message always gets same LC
3. **Independent of time**: Doesn't care about wall-clocks
4. **Conflict-free**: No two messages can have the same LC (enforced by UNIQUE constraint)

## Example: Clock Skew

Two devices, different clocks:

```
Device A          Device B
(clock -2 hours)  (clock +1 hour)

12:00 "Hi"   -->  Server LC=1
         14:30 "Hey" --> Server LC=2
13:00 "OK"   -->  Server LC=3
```

**All devices converge**:
- Order: 1 (Hi), 2 (Hey), 3 (OK)
- Wall-clock times: 12:00, 14:30, 13:00
- **Order is NOT by wall-clock**, it's by LC

## Example: Offline Device

Device A goes offline, Device B stays online:

```
Device A (offline)        Device B (online)
12:00 "Hello" (local LC=1)   
12:01 "World" (local LC=2)
                             14:00 "Hi" --> Server LC=1
                             14:01 "Hey" --> Server LC=2
[reconnect]
Server says: "Hello" LC=2, "World" LC=3, reassigns both
                             14:02 "OK" --> Server LC=4
```

**Final state (all devices)**:
1. "Hi" (from Device B)
2. "Hello" (from Device A)
3. "World" (from Device A)
4. "OK" (from Device B)

Device A converged automatically, despite being offline.

## Implementation

### Database Schema

```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    lamport_clock INTEGER NOT NULL,      -- THE KEY COLUMN
    device_id TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    UNIQUE(session_id, lamport_clock)    -- NO DUPLICATES
)
```

Key points:
- `lamport_clock INTEGER NOT NULL` — Every message must have an LC
- `UNIQUE(session_id, lamport_clock)` — No two messages in same session can have same LC

### Server Logic

```rust
pub fn add_message(&mut self, role: String, content: String, device_id: String) -> Message {
    // Find max LC in this session
    let lamport = if self.messages.is_empty() {
        1
    } else {
        self.messages.iter()
            .map(|m| m.lamport_clock)
            .max()
            .unwrap_or(0) + 1
    };

    // Create message with assigned LC
    let msg = Message::new(
        self.id,
        role,
        content,
        device_id,
        lamport,  // SERVER-ASSIGNED
    );

    self.messages.push(msg.clone());
    msg
}
```

### Client Logic

```rust
pub async fn add_message(
    &self,
    session_id: &str,
    role: &str,
    content: &str,
) -> Result<()> {
    // Send to server
    let response = self.http_client
        .post(&format!("{}/sessions/{}/messages", self.server_url, session_id))
        .json(&AddMessageRequest {
            role: role.to_string(),
            content: content.to_string(),
            device_id: self.device_id.clone(),
        })
        .send()
        .await?;

    let body = response.json::<serde_json::Value>().await?;
    
    // Extract SERVER-ASSIGNED LC
    let lamport_clock = body["lamport_clock"]
        .as_u64()
        .ok_or("No lamport_clock in response")?;

    // Store locally with LC
    self.local_truth.add_message(
        &msg_id,
        session_id,
        role,
        content,
        lamport_clock,  // USE SERVER LC
        &self.device_id,
    ).await?;

    Ok(())
}
```

### Query Logic

```rust
pub async fn get_messages(&self, session_id: &str) -> Result<Vec<Message>> {
    let rows = sqlx::query(
        "SELECT id, role, content, lamport_clock 
         FROM messages 
         WHERE session_id = ? 
         ORDER BY lamport_clock ASC"  // ORDER BY LC, NOT created_at
    )
    .bind(session_id)
    .fetch_all(&self.db)
    .await?;

    // Convert rows to Messages
    Ok(rows.iter().map(|row| {
        // ... convert
    }).collect())
}
```

## Guarantees

| Property | Guarantee |
|----------|-----------|
| **Deterministic** | Same session, same message order on all devices |
| **Convergent** | Devices automatically sync to same order |
| **Offline-safe** | Works even if devices are disconnected |
| **Clock-agnostic** | Doesn't depend on accurate clocks |
| **Idempotent** | Adding same message twice = added once |

## When NOT to Use Wall-Clock Time

❌ **Wrong**: `ORDER BY created_at`  
✅ **Right**: `ORDER BY lamport_clock`

❌ **Wrong**: `IF created_at > some_time THEN...`  
✅ **Right**: `IF lamport_clock > some_lc THEN...`

❌ **Wrong**: Using `created_at` for conflict resolution  
✅ **Right**: Using `lamport_clock + UUID` for uniqueness

## Performance Notes

- **Lamport clock assignment**: O(n) per message (find max in session)
- **Optimization**: Keep `max_lamport_clock` in session metadata (O(1) assignment)
- **Query**: O(log n) with index on `lamport_clock`

## See Also

- [CRDT Convergence](./crdt.md) — Why Lamport clocks enable CRDT
- [Local Truth Database](./local-truth.md) — Schema details
- [Message API](../api/messages.md) — How to use messages
