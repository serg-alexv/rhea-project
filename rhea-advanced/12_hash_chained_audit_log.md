# Hash-Chained Audit Log (Advanced)

SYSTEM:
You are an infosec engineer. Assume adversaries. Design tamper-evidence, not vibes.

USER:
Specify a tamper-evident audit log for agent operations.
Requirements:
- each event has: prev_hash, event_hash, canonical_json, timestamp, actor, signature(optional)
- canonicalization rules (stable JSON encoding)
- verification procedure (how to detect tampering)
- storage strategy (local file + remote mirror)
- threat model: replay, truncation, reordering
End with: "minimum viable hash chain" in 15 lines of pseudo-format.
