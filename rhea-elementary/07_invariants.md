07_invariants.md
# Core Invariants (Elementary)

SYSTEM:
Output only invariants + rationale + how to test them.

USER:
Write 10 invariants for a verifiable LLM memory system.
Examples to include:
- "No memory write without explicit STORE op + reason"
- "No cross-domain recall unless allowed + justified"
- "No Fact without receipts"
- "Append-only event log"
- "Idempotent workers"
For each invariant: why it exists + how to test/monitor it.