# ⚡ Quick Start (5 minutes)

Get a working Rhea system running in 5 minutes. No theory, just code.

---

## Step 1️⃣: Start the Server (1 min)

```bash
cd rhea-session-server
cargo run --release --bin server
```

You should see:
```
🌟 Rhea Session Server running on http://127.0.0.1:3000
```

✓ **Server is alive.** It's now assigning Lamport clocks.

---

## Step 2️⃣: Build a Client (2 min)

Create `src/main.rs`:

```rust
use rhea_client::Client;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Connect to Rhea server
    let client = Client::new(
        "http://127.0.0.1:3000",
        "my-device-id"
    ).await?;

    // Create a session
    let session = client.create_session("PROTOS").await?;
    println!("✓ Created session: {}", session);

    // Add a message (server assigns Lamport clock)
    let msg_id = client.add_message(
        &session,
        "user",
        "Hello, Rhea!"
    ).await?;
    println!("✓ Added message: {}", msg_id);

    // Retrieve messages (ordered by Lamport clock, not wall-time)
    let messages = client.get_local_messages(&session).await?;
    
    println!("\nMessages (ordered by Lamport clock):");
    for (id, role, content, lamport_clock) in messages {
        println!("  [LC:{}] {}: {}", lamport_clock, role, content);
    }

    Ok(())
}
```

✓ **Client is ready.** It trusts the server's Lamport clocks.

---

## Step 3️⃣: Run It (2 min)

```bash
cd rhea-client
cargo run --example quickstart
```

**Output**:
```
✓ Created session: 550e8400-e29b-41d4-a716-446655440000
✓ Added message: 650e8400-e29b-41d4-a716-446655440001

Messages (ordered by Lamport clock):
  [LC:1] user: Hello, Rhea!
```

✓ **You built a convergent system in 5 minutes.**

---

## What Just Happened? 🤯

1. **Client sent message** → "Hello, Rhea!"
2. **Server received it** → Assigned LC=1 (logical order)
3. **Server returned LC=1** → Client stored it locally
4. **Client queried messages** → Got them ordered by LC (not wall-clock time)

**Magic**: Add the same message on a second device:
- Server assigns LC=2
- Both devices see: [LC=1, LC=2]
- **Same order, forever**

No clock skew. No conflicts. No manual syncing.

---

## Test Cross-Device Sync 🔄

Open **two terminals**:

**Terminal 1** (Device A):
```bash
export DEVICE_ID="phone"
cargo run --example minimal-client
# Device A creates session, adds "Hi from phone"
```

**Terminal 2** (Device B):
```bash
export DEVICE_ID="laptop"
cargo run --example multi-device
# Device B adds "Hi from laptop" to SAME session
```

**Result**: Both devices print the same message order:
```
Device A sees: [LC:1 "Hi from phone", LC:2 "Hi from laptop"]
Device B sees: [LC:1 "Hi from phone", LC:2 "Hi from laptop"]
```

✓ **Devices converged automatically.**

---

## 🎓 What You Just Learned

| Concept | Example |
|---------|---------|
| **Session** | Immutable message stream (messages never change) |
| **Lamport Clock** | Order number (1, 2, 3...) assigned by server |
| **Convergence** | All devices see same order (by LC) |
| **Idempotent** | Sending same message twice = stored once |

---

## 🚀 Next Steps

- **Understand the WHY**: [Design Philosophy](./architecture/philosophy.md)
- **Learn the mechanics**: [DTS: Deterministic Time System](./architecture/dts.md)
- **Read the proof**: [CRDT Convergence](./architecture/crdt.md)
- **Build more**: [Multi-Device Example](./examples/multi-device.rs)
- **Full API**: [Sessions Reference](./api/sessions.md) & [Messages Reference](./api/messages.md)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Connection refused` | Is server running? `cargo run --release --bin server` |
| `Port 3000 in use` | Change port: `--bind 127.0.0.1:8080` |
| `No messages returned` | Check Lamport clock is being returned from server |

---

**Congratulations! You've built a convergent system.** 🎉

Next: [Understand the Architecture](./architecture.md)
