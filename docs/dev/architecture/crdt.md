# CRDT Convergence

How Rhea guarantees all devices converge on the same final state, without a central coordinator.

## The Promise

**Convergence Theorem**: Given any two devices A and B:

```
A.messages ≠ B.messages (out of sync)
     ↓
[Both devices sync]
     ↓
A.messages = B.messages (converged!)
```

This happens **automatically**, with no manual conflict resolution.

## The Math: CRDT Properties

Rhea uses a **Conflict-free Replicated Data Type (CRDT)** for sessions. A CRDT must satisfy:

1. **Commutativity**: `merge(A, B) = merge(B, A)`
2. **Idempotence**: `merge(X, X) = merge(X)`
3. **Associativity**: `merge(merge(A, B), C) = merge(A, merge(B, C))`

If these three properties hold, **convergence is mathematically guaranteed**.

## Why Rhea's Design Works

### 1. Commutativity ✓

Merge order doesn't matter:

```
Device A state: [msg1(LC=1), msg3(LC=3)]
Device B state: [msg2(LC=2)]

merge(A, B) = [msg1(LC=1), msg2(LC=2), msg3(LC=3)]
merge(B, A) = [msg1(LC=1), msg2(LC=2), msg3(LC=3)]

Same result!
```

**Why?** We order by `lamport_clock`, which is the same for all devices.

### 2. Idempotence ✓

Adding same message twice = once:

```
Initial: [msg1(LC=1)]

merge([msg1(LC=1)]) = [msg1(LC=1)]

merge(merge([msg1(LC=1)])) = [msg1(LC=1)]
```

**Why?** UUID deduplication. If `msg1.id` already exists, we skip it.

### 3. Associativity ✓

Merge order doesn't affect final state:

```
A: [msg1(LC=1), msg2(LC=2)]
B: [msg3(LC=3)]
C: [msg4(LC=4)]

merge(merge(A, B), C) = [msg1, msg2, msg3, msg4]
merge(A, merge(B, C)) = [msg1, msg2, msg3, msg4]

Same result!
```

**Why?** Lamport clocks provide total order. No matter what order you merge in, the final sort is deterministic.

## Example: Three Devices Syncing

```
Device A (offline)     Device B (online)       Device C (online)
msg1(LC=1) "Hi"
msg2(LC=2) "Hello"
                       msg3(LC=3) "Hey"
                                              msg4(LC=4) "Howdy"
[A reconnects]
sync(A ← B)
sync(A ← C)
```

**After sync, A has**: [msg1, msg2, msg3, msg4] (sorted by LC)

```
A sends to B:
B merges: merge(existing, [msg1, msg2, msg4])
         = [msg1, msg2, msg3, msg4]

B sends to C:
C merges: merge(existing, [msg1, msg2, msg3])
         = [msg1, msg2, msg3, msg4]
```

**All devices converged** to the same state: `[msg1, msg2, msg3, msg4]`

## Why Lamport Clocks Enable CRDT

**Without Lamport clocks** (using wall-clock time):

```
Device A: msg1(created_at=12:00)
Device B: msg1(created_at=14:00)

Which msg1 is "real"? Ambiguous!
Devices may disagree on order.
```

**With Lamport clocks**:

```
Device A: msg1(LC=1)
Device B: msg1(LC=1)

Same LC, so same position.
Total order is deterministic.
Convergence guaranteed.
```

## Implementation: Merge Algorithm

```rust
pub fn merge_messages(&mut self, new_messages: Vec<Message>) {
    for msg in new_messages {
        // Step 1: Dedup by UUID
        if !self.messages.iter().any(|m| m.id == msg.id) {
            self.messages.push(msg);
        }
    }
    
    // Step 2: Re-sort by Lamport clock (commutativity)
    self.messages.sort_by_key(|m| m.lamport_clock);
}
```

**Key insight**: We don't need complex merge logic. Just:
1. Add new messages (skip if UUID exists)
2. Sort by LC
3. Done! Convergence guaranteed.

## Proof of Convergence

**Theorem**: If all devices follow the merge algorithm above, they will converge to the same state.

**Proof**:
1. Each device has a superset of all messages sent to it
2. All devices sort by the same key (`lamport_clock`)
3. Sorting is deterministic (same LC always produces same order)
4. Therefore, all devices will have the same sorted order
5. QED

## Conflict Resolution

With Lamport clocks, there are almost **no conflicts**:

```
User sends "A" from Device 1  → LC = 1
User sends "B" from Device 2  → LC = 2
```

Clear order: A first, then B. No conflict.

**The only way to conflict** is if two devices somehow get the same LC (which we prevent with `UNIQUE(session_id, lamport_clock)`).

### Rare Case: UUID Collision

Two messages with same UUID (astronomically unlikely with UUID v4):

```
Device A: msg(id=abc, LC=1)
Device B: msg(id=abc, LC=2)

Problem: Same message, different LC?
```

**Solution**: Client always trusts server's LC. If there's a collision, the server-assigned LC is the truth.

## Eventual Consistency

Rhea provides **strong eventual consistency**:

- **Eventual**: Given time and no new messages, all devices converge
- **Strong**: Once converged, devices stay converged (no surprises)

This is stronger than causal consistency but weaker than linearizability (which is impossible in distributed systems without a global clock).

## When Convergence Breaks

Convergence is **guaranteed only if**:

1. ✅ All devices use the same server (single authority for LC)
2. ✅ Servers are stateful (don't lose LC counter)
3. ✅ Messages are append-only (no DELETE/UPDATE)
4. ✅ Devices sync eventually (no partitioning forever)

If any of these break, convergence may not hold.

## See Also

- [DTS: Deterministic Time System](./dts.md) — How Lamport clocks work
- [Local Truth Database](./local-truth.md) — Schema for idempotent merge
- [Cross-Device Sync](../guides/cross-device-sync.md) — How devices sync in practice
