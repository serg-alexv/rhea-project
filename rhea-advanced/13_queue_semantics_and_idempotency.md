# Queue Semantics & Idempotency (Advanced)

SYSTEM:
You are designing reliable distributed systems. Assume at-least-once delivery and partial failures.

USER:
We use Firestore as a mailbox, not a real queue. Define robust queue semantics:
- job leasing protocol with leaseUntil
- idempotencyKey strategy
- deduplication: exactly-once effects via idempotency store
- retry policy with exponential backoff + jitter
- poisoning/dead-letter handling
- ordering: per-session sequence vs global
Output: state machine + transaction notes (what must be atomic).
