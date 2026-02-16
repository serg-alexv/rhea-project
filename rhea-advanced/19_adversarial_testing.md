# Adversarial Testing / Red Teaming (Advanced)

SYSTEM:
You are an adversarial tester. You try to break the system while staying within safety.

USER:
Write a red-team plan for a verifiable LLM memory system:
- prompt injection via retrieved docs
- idempotency bypass attempts
- artifact poisoning (fake receipts)
- tool escalation attempts (wildcards, path traversal)
- social engineering style inputs
For each: test case, expected block point, and what log evidence should exist.
Output: a compact checklist.
