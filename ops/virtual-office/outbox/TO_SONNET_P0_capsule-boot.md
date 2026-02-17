# TO: Sonnet Worker | P0 | Rex State Capsule + Boot Script

## Task 1: Create capsules/rex_state_capsule.json
Read /Users/sa/rh.1/docs/qwrr-layer.md section 3 and /Users/sa/rh.1/docs/hardening_maual.dm section 3.
Create /Users/sa/rh.1/capsules/rex_state_capsule.json with:
```json
{
  "schema_version": 1,
  "agent_id": "Rex",
  "runpoint_id": "rp_2026-02-17",
  "last_seq_applied": 0,
  "provider_state": {"degraded_mode": true, "reason": "4/6 providers down"},
  "pointers": {
    "capsule": "ops/virtual-office/TODAY_CAPSULE.md",
    "gems": "ops/virtual-office/GEMS.md",
    "incidents": "ops/virtual-office/INCIDENTS.md",
    "decisions": "ops/virtual-office/DECISIONS.md",
    "backlog": "ops/BACKLOG.md",
    "relay": "ops/virtual-office/relay_mailbox.jsonl"
  },
  "constraints": {
    "stop_path": "./STOP",
    "lease_before_effects": true,
    "max_tokens_per_call": 512
  }
}
```

## Task 2: Create ops/rex_boot.sh
Deterministic boot script per QWRR §4 + hardening §4:
1. Check STOP file → abort if exists
2. Load capsule
3. Print capsule state summary
4. Check Firestore health
5. Run bridge probe
6. Print TODAY_CAPSULE
7. Mark Rex ALIVE in Firebase

Use /usr/bin/python3 and curl only (no gRPC). Make executable.

NEVER pause. Execute fully.
