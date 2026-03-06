# 🌟 Rhea Developer Documentation

> **Every distributed system has a choice: divergence or convergence. Rhea chooses convergence.**

---

## 🎯 The Problem You're Solving

Your app runs on **phone, laptop, tablet**. Users expect perfect sync.

But clocks lie.

```
Phone (clock -2h)     Server (correct)    Laptop (clock +1h)
12:00 "Hi"     →      14:00               →      15:30
              ←       [Assigns LC=1]      ←
                                         
Phone sees: Hi first
Laptop sees: Hi first

✓ But what if they disagreed?
```

**Without Rhea**: Manual conflict resolution, eventual inconsistency, user confusion.  
**With Rhea**: Automatic convergence, mathematical guarantee, one truth.

---

## ⚡ What Rhea Does

| | Before | After |
|---|--------|-------|
| **Clock skew** | 😱 Messages out of order | ✅ Order independent of clocks |
| **Offline sync** | 😱 Complex logic, bugs | ✅ Append-only merge (automatic) |
| **Convergence** | 😱 Manual conflict resolution | ✅ Guaranteed by math (CRDT) |
| **Verification** | 😱 "Hope it works" | ✅ Formal proof of correctness |

---

## 🚀 Start Here (Pick Your Path)

### 🎬 **New to Rhea?** (15 min)
1. **[Getting Started: The Story](./getting-started.md)** — Why this design matters
2. **[Quick Start](./quickstart.md)** — Run your first session (5 min)
3. **[Architecture Overview](./architecture.md)** — How it works (with diagrams)

### 🔧 **Building an Integration?** (30 min)
1. **[Installation](./installation.md)** — Set up locally
2. **[API Reference: Sessions](./api/sessions.md)** — Create & manage sessions
3. **[API Reference: Messages](./api/messages.md)** — Add & retrieve messages
4. **[Examples: Minimal Client](./examples/minimal-client.rs)** — Copy & paste this

### 🧠 **Architect/Deep Dive?** (1 hour)
1. **[Design Philosophy](./architecture/philosophy.md)** — The WHY
2. **[DTS: Deterministic Time System](./architecture/dts.md)** — How Lamport clocks work
3. **[CRDT Convergence](./architecture/crdt.md)** — Mathematical proof
4. **[Examples: Multi-Device Sync](./examples/multi-device.rs)** — See convergence in action

---

## 🎓 Core Concepts at a Glance

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Session = Message Stream + Convergence Guarantee      │
│                                                         │
│  [msg1(LC=1)] → [msg2(LC=2)] → [msg3(LC=3)]           │
│                                                         │
│  Every device sees: 1 → 2 → 3  (no exceptions)        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

| Term | Meaning | Why It Matters |
|------|---------|----------------|
| **Lamport Clock** | Sequential number (1,2,3...) assigned by server | Independent of wall-clocks; determines order |
| **Message** | Immutable event with ID, content, Lamport clock | Once written, never changes; devices trust it |
| **Device** | Independent client with local SQLite database | Can be offline; syncs when connected |
| **Server** | Single authority for Lamport clock assignment | Guarantees all devices converge |

---

## 📚 API Reference

### Create a Session
```bash
POST /sessions
{
  "character": "PROTOS"
}
```

**Response**: Session ID, empty message list

### Add a Message
```bash
POST /sessions/{id}/messages
{
  "role": "user",
  "content": "Hello!",
  "device_id": "phone-123"
}
```

**Response**: Message ID + **Lamport clock** (use this for ordering)

### Get All Messages
```bash
GET /sessions/{id}
```

**Response**: All messages **sorted by Lamport clock** (not wall-time)

👉 [Full API Docs](./api/) — Complete reference with examples

---

## 💡 Why This Matters

### 🕐 Wall-Clock Time is Broken

Clocks drift, users change time, NTP has bugs. If you order by wall-clock time:

```
Device A (clock -2h): msg at 12:00 PM
Device B (clock +1h): msg at 3:30 PM

By wall-clock: Device B's message comes first (3:30 > 12:00)
By causality: Both arrived at same time; order is undefined

→ Devices disagree forever
```

### ⏱️ Lamport Clocks Work

Server assigns logical order (1, 2, 3), not physical time:

```
msg1 arrives → LC=1  (doesn't matter when wall-clock says)
msg2 arrives → LC=2  (doesn't matter if clocks are wrong)
msg3 arrives → LC=3

All devices see: 1 → 2 → 3
Convergence: automatic, mathematical, permanent
```

### 🔄 CRDT = No Conflicts

With append-only + Lamport clocks, conflicts are impossible:

```
Merge(A, B) = Merge(B, A)  ✓ Commutative
Merge(X, X) = Merge(X)     ✓ Idempotent
Merge(Merge(A,B),C) = Merge(A,Merge(B,C))  ✓ Associative

→ **Math says: devices will converge**
```

👉 [Read the proof](./architecture/crdt.md)

---

## 🛠️ Guides (Phase 2)

Coming soon:
- **Cross-Device Sync** — Keep 10+ devices in sync
- **Offline Operation** — Queue locally, sync when connected
- **Memory Management** — Cross-session context injection
- **LLM Integration** — Use Rhea as OpenAI context engine
- **Production Deployment** — Run at scale with monitoring

---

## 🏗️ Architecture at a Glance

```
Device A              Rhea Server           Device B
────────              ───────────           ────────
│ LocalTruth          │ Sessions            │ LocalTruth
│ (SQLite)            │ (Messages)          │ (SQLite)
└────┬────────────────┬─────────────────────┴────┘
     │                │
     ├─ Add message   │
     │ "Hello"        │
     │ ──────────────>│ Assigns LC=1
     │<───────────────│ Returns LC=1
     │ Stores LC=1    │
     │                │
     │                │ Get all messages
     │                │<────────────────────────
     │                │──────────────────────>
     │                │ Returns: [LC=1 "Hello"]
     │                │
     └────────────────┴─────────────────────────→
                      Stores LC=1
                      
Both devices now have: [LC=1 "Hello"]
✓ Converged!
```

👉 [Full architecture diagram](./architecture.md)

---

## 🚀 Quick Start (5 minutes)

**1. Start server**
```bash
cd rhea-session-server
cargo run --release --bin server
```

**2. Build client**
```rust
use rhea_client::Client;

#[tokio::main]
async fn main() -> Result<()> {
    let client = Client::new(
        "http://127.0.0.1:3000",
        "device-1"
    ).await?;
    
    // Create session
    let session = client.create_session("PROTOS").await?;
    
    // Add message (server assigns Lamport clock)
    client.add_message(&session, "user", "Hello!").await?;
    
    // Get messages (ordered by LC, not wall-clock)
    for (id, role, content, lamport_clock) in 
        client.get_local_messages(&session).await? {
        println!("[LC:{}] {}: {}", lamport_clock, role, content);
    }
    
    Ok(())
}
```

**3. Run**
```bash
cargo run
```

**Output**:
```
[LC:1] user: Hello!
```

✓ You've just built a system that converges across devices.

👉 [Full quick start guide](./quickstart.md)

---

## 📖 Choose Your Reading Level

| Level | Time | What You'll Understand |
|-------|------|----------------------|
| **Busy Dev** | 5 min | How to use the API |
| **Curious Engineer** | 30 min | Why Lamport clocks matter |
| **Architect** | 2 hours | Mathematical proof of convergence |

---

## 💬 Community

- **Questions?** [GitHub Discussions](https://github.com/rhea/rhea/discussions)
- **Bug?** [GitHub Issues](https://github.com/rhea/rhea/issues)
- **Contributing?** [CONTRIBUTING.md](../../CONTRIBUTING.md)

---

## 📋 Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Core DTS** | ✅ Production-ready | Lamport clocks, CRDT convergence |
| **Rust Client** | ✅ Production-ready | Full-featured, well-tested |
| **Session Server** | ✅ Production-ready | Single-authority LC assignment |
| **TypeScript Client** | 🔄 Phase 2 | Browser & Node.js support |
| **Distributed Replication** | 🔄 Phase 2 | Multiple servers with consensus |
| **End-to-End Encryption** | 🔄 Phase 2 | Server-side confidentiality |

---

**Last updated**: 2026-03-06  
**Version**: Rhea v0.5.0-alpha (post-DTS fix)  
**Maintainer**: [Your Org]

## API Reference

All APIs organized by service:

- [Session API](./api/sessions.md) — Create, sync, retrieve sessions
- [Message API](./api/messages.md) — Add and retrieve messages
- [Device API](./api/devices.md) — Register and manage devices
- [Memory API](./api/memory.md) — Cross-session memory and recall

## Guides

Detailed walkthroughs for common tasks:

- [Cross-Device Sync](./guides/cross-device-sync.md) — Keep devices in sync
- [Offline Operation](./guides/offline.md) — Queue locally, sync when connected
- [Memory Management](./guides/memory.md) — Use long-term context
- [Integrating LLMs](./guides/llm-integration.md) — Connect OpenAI, Anthropic, etc.
- [Deployment](./guides/deployment.md) — Run in production

## Examples

Production-ready code samples:

- [Minimal Client](./examples/minimal-client.rs) — Bare-bones session setup
- [Multi-Device Sync](./examples/multi-device.rs) — Two devices converging
- [Offline Queue](./examples/offline-queue.rs) — Local queuing with server sync
- [Memory Injection](./examples/memory-injection.rs) — Context-aware responses

## Architecture Deep Dives

For those wanting to understand internals:

- [Design Philosophy](./architecture/philosophy.md) — **The why** behind every decision
- [DTS: Deterministic Time System](./architecture/dts.md) — How Lamport clocks work
- [CRDT Convergence](./architecture/crdt.md) — Why all devices see the same order
- [Local Truth Database](./architecture/local-truth.md) — SQLite schema & queries
- [Control Layer](./architecture/control.md) — Events, metadata, audit trails

## SDKs & Libraries

Official clients and bindings:

- **Rust**: [`rhea-client`](../../../rhea-client) — Full-featured client
- **TypeScript**: [`rhea-web`](../../../rhea-web) — Browser & Node.js
- **Python**: `rhea-py` (coming soon)

## Troubleshooting

- [FAQ](./faq.md) — Common questions
- [Debugging](./debugging.md) — Tools and techniques
- [Performance](./performance.md) — Optimization tips

## Support

- **Issues**: [GitHub Issues](https://github.com/rhea/rhea/issues)
- **Discussions**: [GitHub Discussions](https://github.com/rhea/rhea/discussions)
- **Status**: [System Status](https://status.rhea.dev)

---

**Last updated**: 2026-03-06  
**Version**: Rhea v0.5.0-alpha (post-DTS fix)
