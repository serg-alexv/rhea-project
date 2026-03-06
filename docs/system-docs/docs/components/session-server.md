---
sidebar_position: 3
---

# Session Server

A Rust HTTP server built with [Axum](https://github.com/tokio-rs/axum) that provides session management with Lamport clocks and the character archetype system.

## Overview

The session server is a lightweight, independent service that manages conversation sessions. It stores sessions in memory (no database) and provides a deterministic tribunal dialog endpoint.

**Port:** 3000

## Type System

### Character

Four archetypes, each with a symbol and name:

```rust
pub enum Character {
    Protos,  // ⚙️ — systematic, analytical
    Zerg,    // 🧬 — adaptive, biological
    Terran,  // 🔧 — practical, engineering
    Aeon,    // ✨ — philosophical, temporal
}
```

### Session

```rust
pub struct Session {
    pub id: Uuid,
    pub character: Character,
    pub title: String,              // e.g., "Session ⚙️"
    pub messages: Vec<Message>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub client_id: Option<String>,  // for multi-client CRDT sync (future)
}
```

### Message

Every message carries a Lamport clock and device identifier:

```rust
pub struct Message {
    pub id: Uuid,
    pub session_id: Uuid,
    pub role: String,
    pub content: String,
    pub created_at: i64,        // Unix timestamp
    pub device_id: String,
    pub lamport_clock: u64,     // monotonically increasing per session
}
```

### Tribunal Types

The server includes tribunal request/response types with an **adversarial check** layer:

```rust
pub struct TribunalResponse {
    pub reply: String,
    pub agreement_score: f64,
    pub models_responded: usize,
    pub elapsed_s: f64,
    pub adversarial_note: String,       // devil's-advocate counter-argument
    pub confidence_adjusted: f64,       // original confidence × 0.85
}
```

The adversarial layer categorizes agreement:
- **Above 80%** — warns of potential groupthink
- **Below 50%** — acknowledges genuine ambiguity
- **50–80%** — recommends further evidence

A **15% skepticism discount** is always applied: `confidence_adjusted = agreement_score × 0.85`.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/sessions` | Create a new session (requires `character`) |
| GET | `/sessions` | List all sessions |
| GET | `/sessions/:id` | Get session with all messages |
| POST | `/sessions/:id/messages` | Add a message (auto-increments Lamport clock) |
| POST | `/dialog` | Tribunal dialog (deterministic heuristic, no real LLM) |

## Storage

Sessions are stored in-memory as `Arc<RwLock<Vec<Session>>>`. This means:
- ✅ Fast, lock-free reads
- ✅ No database setup required
- ❌ Data lost on restart
- ❌ Single-node only

This is by design — the session server is intended as a fast local cache with eventual CRDT sync to persistent storage.

## Building and Running

```bash
cd rhea-session-server
cargo build --release
./target/release/server
# 🌟 Rhea Session Server running on http://127.0.0.1:3000
```

## Dependencies

```toml
[dependencies]
axum = "0.7"
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
uuid = { version = "1", features = ["v4", "serde"] }
chrono = { version = "0.4", features = ["serde"] }
sha2 = "0.10"
```

## Future Plans

- **CRDT merge** — use `client_id` + `lamport_clock` for conflict-free multi-device sync
- **Persistence** — optional SQLite or CockroachDB backend
- **Keystroke tracking** — `KeystrokeEvent` struct exists, endpoint not yet wired
