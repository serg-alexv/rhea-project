# Getting Started: A Story

This is not a reference manual. This is a journey.

## Act 1: The Problem

You're building an app for multiple devices. A phone, a laptop, a tablet. Users expect them to stay in sync.

You add a message on the phone at 2 PM. You open the laptop at 3 PM. You expect to see the same message.

But here's the thing: your devices have **different clocks**.

The phone thinks it's 1:55 PM (wrong).  
The laptop thinks it's 3:15 PM (also wrong).  
The server knows it's 3:05 PM (correct).

If you order messages by clock time, chaos:

```
Phone creates msg at 1:55 PM
Laptop creates msg at 3:15 PM
```

The phone says: "my message came first"  
The laptop says: "my message came first"  
Both are right, according to their clocks.

**The system is broken.** No convergence. No truth. Just divergence.

## Act 2: The Insight

Stop asking "when did this happen?"  
Ask instead: "in what order did this arrive?"

When the phone's message hits the server first, it gets **order number 1**.  
When the laptop's message hits the server next, it gets **order number 2**.

Now both devices know the order: 1, 2. No ambiguity. No divergence.

This order number is called a **Lamport clock**.

## Act 3: The System

You set up a **server**:

```
Server: I'll be the referee. You devices, send me your messages.
        I'll give each one a number: 1, 2, 3, etc.
        All of you will sort by these numbers.
        You'll all converge.
```

You build **clients** (phone, laptop, tablet):

```
Client: I'll send my messages to the server.
        I'll get back a number.
        I'll store that number.
        When I sync with other devices, I'll sort by the number.
        We'll all see the same order.
```

## Act 4: The Magic

Three devices, all offline:

**Phone** (offline):
- Msg A at local order 1
- Msg B at local order 2

**Laptop** (offline):
- Msg C at local order 1

**Tablet** (online):
- Connects to server
- Server assigns Msg D → order 1
- Tablet gets: Msg D (1)

Phone comes online. Syncs with server.

```
Server: "You sent A and B. I already had 1 message.
        So A is now 2. B is now 3."
```

Phone now has: A (2), B (3), D (1)  
Server knows: D (1), A (2), B (3)

**Tablet comes online:**

```
Tablet syncs with Phone:
  Phone has: D (1), A (2), B (3)
  Tablet gets: A (2), B (3)
  
Tablet now has: D (1), A (2), B (3)
```

**All three devices converged automatically.**  
Phone: D, A, B  
Laptop: D, A, B (once it syncs)  
Tablet: D, A, B  

Same order. Same truth. **The system is alive.**

## Act 5: Why This Works

Three principles:

1. **Server is the source of truth for order**
   - The server is the referee. The server's decision is final.
   - Clients trust the server. The server is honest.

2. **Lamport clocks are deterministic**
   - Same message always gets the same order.
   - No randomness, no surprises.

3. **Append-only is immutable**
   - Once a message is written, it stays.
   - No updates, no deletes.
   - Devices can trust the log.

If these three things are true, **convergence is guaranteed by math**, not by luck.

## Act 6: The Code

Start the server:

```bash
cd rhea-session-server
cargo run --release --bin server
```

Build a client:

```rust
use rhea_client::Client;

#[tokio::main]
async fn main() -> Result<()> {
    let client = Client::new(
        "http://127.0.0.1:3000",
        "my-phone"
    ).await?;

    // Create a session
    let session = client.create_session("PROTOS").await?;

    // Add a message (server assigns order)
    client.add_message(&session, "user", "Hello!").await?;

    // Retrieve messages (ordered by server's order, not wall-clock)
    let msgs = client.get_local_messages(&session).await?;
    for (id, role, content, lamport_clock) in msgs {
        println!("[{}] {}: {}", lamport_clock, role, content);
    }

    Ok(())
}
```

Run three clients. See them converge.

## Act 7: The Realization

This is simple. Stupid simple.

No complex algorithms. No leader election. No Byzantine generals problem.

Just:
1. Client sends message to server
2. Server says: "You're message number N"
3. All clients sort by N
4. Devices converge

**But it works.** Mathematically, provably, completely.

And that's Rhea.

---

## Next Steps

- **Learn the concepts**: [Design Philosophy](./architecture/philosophy.md)
- **Understand the mechanics**: [DTS: Deterministic Time System](./architecture/dts.md)
- **See the math**: [CRDT Convergence](./architecture/crdt.md)
- **Write code**: [Quick Start](./quickstart.md)

---

**Question**: Why is this so simple?

**Answer**: Because simplicity is a feature, not a bug. Complex systems fail. Simple systems converge.

We chose convergence.
