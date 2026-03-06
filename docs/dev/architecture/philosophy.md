# Architecture: Design Philosophy

This document explains the **why** behind Rhea's architecture, not just the how.

## The Core Tension

You build a system for devices. Devices have **clocks**. Clocks are **liars**.

A device says "it's 3 PM." Is it? Maybe. Or maybe it synced with NTP last week, and someone changed it, and the battery died, and... it's a mess.

**The problem**: If you trust clocks, you build a lie factory. Two devices will see the same session in different orders. One device says message A came before B. The other says B before A. Both are "right" according to their clocks. Both are wrong.

The system is **dead**: no convergence, no truth, just divergence.

## The Insight

**Stop trusting clocks.**

Instead, trust **signals**. Arrival order. The order messages hit the server. That's real. That happened.

One message arrived first. Another arrived second. That's fact, not opinion.

**Lamport clocks** encode this: not "what time did it happen" but "in what sequence did things happen."

This is **alive** because it's based on causality, not fantasy.

## Why Wall-Clock Time Dies

Wall-clock time is beautiful for humans ("meet at 3 PM"), but it **kills distributed systems**.

Three problems:

### 1. Clocks Drift

Your device's clock is wrong. Not dramatically, but wrong. Maybe +2 minutes. Maybe -4 seconds. Add 10 devices together, and you have a spread of ±30 seconds. Now order messages by wall-clock: chaos.

### 2. Clocks Aren't Monotonic

Someone changes the system time. DST happens. NTP corrects backwards. Your clock *goes backwards*. Messages created "after" other messages have earlier timestamps.

### 3. No Enforcement

There's no law that says "your clock must be accurate." A buggy firmware, a user prank, a timezone misconfiguration—and your causality is scrambled. The system doesn't know it's broken until devices diverge.

## How Lamport Clocks Live

**A Lamport clock is a counter.**

```
Message 1 arrives → Counter = 1
Message 2 arrives → Counter = 2
Message 3 arrives → Counter = 3
```

Simple. Dumb. Perfect.

It doesn't care about time. It only knows: "this came after that." That's **causality**, and causality is the *only* thing that matters for ordering.

### Why This Works

1. **It's mechanical**: No magic, no assumptions, just increment.
2. **It's deterministic**: Same messages, same order, every time.
3. **It's decoupled from reality**: A device's clock can be 10 years off. Doesn't matter.
4. **It's convergent**: All devices automatically sort the same way.

## The Philosophy: Causality Over Time

Rhea makes a bet:

> "Causality is more real than time."

Causality = "this caused that"  
Time = "this happened at 3:14 PM"

In distributed systems, **causality is verifiable**. Time is a guess.

A message caused a response. The response can only come *after* the message. That's a law of physics. No device can violate it.

So we build on causality, not time.

## The Control Through Observability Pattern

You can't **control** a distributed system perfectly. Too many moving parts, too much uncertainty.

But you can **observe** it completely. Every message, every arrival, every order: visible, logged, auditable.

**Control isn't perfect sync. Control is complete visibility.**

The server sees everything. The devices see what the server sees. When something goes wrong, you have a complete audit trail of what happened.

This is the **ADK model** (Google's session architecture):
- **Events** = what actually happened (immutable log)
- **State** = temporary working data (derived from events)
- **Metadata** = why it happened (audit trail, reasoning)

Events are truth. State is opinion. Metadata is explanation.

## Why Append-Only

You can't update or delete messages because **mutations are lies**.

If I send "Hello," and you change it to "Goodbye," which version is real? Both devices will be confused. One has "Hello," the other has "Goodbye," and they disagree on what I said.

Append-only means: **what you write is forever.** No surprises. No rewriting history. Devices can trust the log.

This is boring, but it's *correct*.

## Why CRDT

A CRDT (Conflict-free Replicated Data Type) is not magic. It's just:

1. Add messages (no overwrites)
2. Sort by Lamport clock
3. Done

The "conflict-free" part is: **there's no way to conflict** if you follow these rules. The math is on your side.

## The Feeling

If you read Rhea's architecture and think "this is obvious," good. It should be.

If you read it and think "why is everyone *not* doing this?", also good.

The power is in simplicity. No consensus algorithms. No leader election. No Byzantine generals. Just: server assigns order, clients trust it, devices converge.

It *feels* right because it *is* right.

## See Also

- [DTS: Deterministic Time System](./dts.md) — The mechanics
- [CRDT Convergence](./crdt.md) — The math
- [Control Architecture](./control.md) — Observability = control
