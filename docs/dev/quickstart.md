# Quick Start (5 minutes)

Get your first Rhea session running in 5 minutes.

## Prerequisites

- Rust 1.70+ (for server and Rust client)
- Docker (optional, for running server in container)

## 1. Start the Rhea Server (2 min)

```bash
cd rhea-session-server
cargo run --release --bin server
```

You should see:
```
🌟 Rhea Session Server running on http://127.0.0.1:3000
```

## 2. Create a Client (2 min)

**Rust client**:
```rust
use rhea_client::Client;

#[tokio::main]
async fn main() -> Result<()> {
    let client = Client::new("http://127.0.0.1:3000", "my-device-id").await?;
    
    // Create a session
    let session = client.create_session("PROTOS").await?;
    println!("Session: {}", session);
    
    // Add a message
    client.add_message(&session, "user", "Hello, Rhea!").await?;
    
    // Retrieve messages (ordered by Lamport clock)
    let messages = client.get_local_messages(&session).await?;
    for (id, role, content, lamport_clock) in messages {
        println!("[LC:{}] {}: {}", lamport_clock, role, content);
    }
    
    Ok(())
}
```

Run it:
```bash
cd rhea-client
cargo run --example quickstart
```

## 3. Test Cross-Device Sync (1 min)

Open two terminals:

**Terminal 1**:
```bash
export DEVICE_ID="device-1"
cargo run --example quickstart
```

**Terminal 2**:
```bash
export DEVICE_ID="device-2"
cargo run --example cross-device
```

Both devices will converge on the same message order, deterministically, regardless of clock skew.

## What Just Happened?

✅ **Server assigned Lamport clocks** — Monotonically increasing (1, 2, 3...)  
✅ **Client stored messages locally** — With LC in SQLite  
✅ **Messages ordered by LC, not wall-clock** — No clock skew!  
✅ **Devices converged** — Same order across all devices  

## Next Steps

- **Add more messages**: Keep adding to the same session to see LC increment
- **Simulate offline**: Kill the server, add messages locally, restart to see sync
- **Integrate an LLM**: See [Integrating LLMs](../guides/llm-integration.md)
- **Deploy to production**: See [Deployment](../guides/deployment.md)

## API Cheat Sheet

| Operation | Code |
|-----------|------|
| Create session | `client.create_session("PROTOS")` |
| Add message | `client.add_message(session_id, role, content)` |
| Get messages | `client.get_local_messages(session_id)` |
| List sessions | `client.get_local_sessions()` |

## Troubleshooting

**"Connection refused"**: Make sure server is running on `127.0.0.1:3000`  
**"No such table: messages"**: Server will auto-create schema on first run  
**Messages out of order**: Check Lamport clock values (should be 1,2,3...)  

---

Ready for more? Jump into [API Reference](../api/sessions.md) or [Architecture Deep Dive](../architecture/dts.md).
