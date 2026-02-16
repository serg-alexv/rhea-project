04_firestore_as_fast_memory.md
# Firestore as Quick Memory / Buffer (Elementary)

SYSTEM:
You are a cloud architect. Assume Firestore is a DB, not a queue. Design safely.

USER:
Provide a minimal architecture using Firestore as:
1) session message store
2) scratch drafts buffer (TTL)
3) inter-model mailbox (jobs)
Explain the necessary additions to make it safe:
- idempotency keys
- leases
- at-least-once triggers
- eventual TTL deletion
Conclude with "Do / Don't" bullets.