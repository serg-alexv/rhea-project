---
sidebar_position: 4
---

# Sessions API

Two session systems exist: the **Rust session server** (Axum, port 3000) for lightweight Lamport-clocked sessions, and the **Tribunal API's session management** (FastAPI, port 8400) for SQL-persisted history.

## Rust Session Server (port 3000)

### POST /sessions

Create a new session with a character archetype.

#### Request

```json
{
  "character": "Protos"
}
```

Valid characters: `Protos`, `Zerg`, `Terran`, `Aeon` (see [Characters](/docs/concepts/characters)).

#### Response (201 Created)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "character": "PROTOS",
  "title": "Session ⚙️",
  "message_count": 0,
  "lamport_clock": 0,
  "created_at": "2025-01-15T10:30:00Z"
}
```

#### curl Example

```bash
curl -X POST http://127.0.0.1:3000/sessions \
  -H "Content-Type: application/json" \
  -d '{"character": "Zerg"}'
```

---

### GET /sessions

List all sessions.

#### Response

```json
[
  {
    "id": "550e8400-...",
    "character": "PROTOS",
    "title": "Session ⚙️",
    "message_count": 5,
    "lamport_clock": 5,
    "created_at": "2025-01-15T10:30:00Z"
  }
]
```

---

### GET /sessions/:id

Get a session with all messages.

#### Response

```json
{
  "session": {
    "id": "550e8400-...",
    "character": "PROTOS",
    "title": "Session ⚙️",
    "message_count": 2,
    "lamport_clock": 2,
    "created_at": "2025-01-15T10:30:00Z"
  },
  "messages": [
    {
      "id": "...",
      "session_id": "550e8400-...",
      "role": "user",
      "content": "What is HRV?",
      "created_at": 1705312200,
      "device_id": "laptop",
      "lamport_clock": 1
    },
    {
      "id": "...",
      "session_id": "550e8400-...",
      "role": "assistant",
      "content": "Heart rate variability is...",
      "created_at": 1705312201,
      "device_id": "server",
      "lamport_clock": 2
    }
  ]
}
```

Returns **404** if the session ID is not found.

---

### POST /sessions/:id/messages

Add a message to a session. Lamport clock is automatically incremented.

#### Request

```json
{
  "role": "user",
  "content": "Tell me about circadian rhythms",
  "device_id": "iphone-14-pro"
}
```

#### Response

```json
{
  "id": "message-uuid",
  "created_at": 1705312300,
  "lamport_clock": 3,
  "content": "Tell me about circadian rhythms",
  "device_id": "iphone-14-pro"
}
```

#### curl Example

```bash
curl -X POST http://127.0.0.1:3000/sessions/550e8400-.../messages \
  -H "Content-Type: application/json" \
  -d '{
    "role": "user",
    "content": "How does melatonin affect sleep?",
    "device_id": "laptop"
  }'
```

---

## Tribunal API Session History (port 8400)

The Tribunal API maintains its own session history in SQLite:

### SQL Schema

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    agent TEXT,
    mode TEXT
);

CREATE TABLE history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    step INTEGER NOT NULL,
    type TEXT NOT NULL,           -- tribunal, tribunal_ice, sceptic, etc.
    prompt TEXT NOT NULL,
    response TEXT,
    agreement_score REAL,
    confidence REAL,
    models TEXT,
    tier TEXT,
    created_at TEXT NOT NULL,
    metadata TEXT                 -- JSON: ontology, endpoint, etc.
);
```

Session history is write-through: every tribunal call persists its result immediately.

### Session Rewind

The API supports rewinding to a previous step in the history:

```json
POST /session/rewind
{
  "step": 3
}
```

This truncates history after the specified step, enabling "undo" for exploration.

---

## Keystroke Events

The session server tracks fine-grained keystroke events for input analysis:

```rust
pub struct KeystrokeEvent {
    pub id: String,
    pub session_id: Uuid,
    pub device_id: String,
    pub key: String,
    pub timestamp: i64,
}
```

**Status:** Struct defined, collection not yet implemented in HTTP endpoints.
