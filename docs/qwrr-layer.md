# Rhea — Quota Walls, Relays, and Resurrection
*Extended “fancy-bonused” spec for surviving provider caps without replacing a Claude-shaped brain.*

> Situation: Rex (Claude-shaped routing judgment) can become unavailable behind provider quota walls.  
> Goal: Keep the office moving with **guaranteed delivery, no loss, no duplicates, no zombie side-effects**, and clean resumption when Rex wakes.

---

## 0) Executive Summary (for people who hate reading)
- **Do not “replace Rex’s brain”** with a different model and pretend it’s equivalent.
- **Do build a persistent relay + resurrection timer** that buffers messages, guarantees delivery, and drains in-order when Rex returns.
- Make relay bank-grade by adding: **seq ordering**, **idempotency keys**, **lease/fencing gates**, **TTL/deadline**, **staleness checks**, and **receipts**.

---

## 1) Why the “brain on different hardware” shortcut fails
**Truth:** model behavior is part of the agent’s identity.  
Routing judgment is **Claude-shaped**. A Gemini proxy won’t route the same way, even if you paste “persona”.

### What *can* be portable
- **State packs** (what is true)
- **Policy packs** (what is allowed)
- **Tool packs** (what can be executed)
- **Transport mechanics** (how messages get delivered)

### What is not portable without changing the agent
- “judgment style” / routing heuristics / refusal boundaries / latent preferences

> Bonus: Stop thinking of “agent identity” as a prompt. Treat it as `State + Policy + Tools + (Model-specific cognition)`.

---

## 2) The right “different angle”: Relay + Resurrection Timer
### Design intent
- Rex is down → messages accumulate safely (durable mailbox)
- Rex wakes → messages are delivered exactly once in-order
- Side-effects occur only under valid lease/fencing token (“STOP means STOP”)

### Minimum components
1) **Mailbox Store** (durable, ordered)
2) **Delivery Worker** (retries + acks)
3) **Resurrection Timer** (availability watcher)
4) **Rex boot protocol** (catch-up → drain mailbox → gated effects)
5) **Receipts + incidents** (proof of termination and accountability)

---

## 3) Bank-grade invariants (falsifiable)
These must be testable under chaos (kill -9, reconnects, duplicates).

### I1 — No message loss
Every outbound command to Rex becomes a mailbox record first.

### I2 — In-order delivery per runpoint
Messages have `seq` monotonic per `runpoint_id` (or a robust cursor scheme).

### I3 — Exactly-once *processing* (or exactly-once effects)
At minimum, processing is at-least-once but **idempotent**.
For side-effects: exactly-once via **intent + receipt**.

### I4 — STOP semantics survive downtime
If STOP is issued while Rex is down, Rex cannot “catch up and execute” old effects blindly.

### I5 — No zombie effects
Old Rex instance must not be able to push commits/write critical state after lease revocation.

---

## 4) Message Envelope (required fields)
Every mailbox message MUST include an envelope that supports:
- idempotency
- ordering
- schema evolution
- gating by lease token
- auditability

### Envelope v1
```json
{
  "id": "uuidv7",
  "runpoint_id": "rp_...",
  "seq": 12345,
  "type": "msg.send | task.create | decision.record | effect.request | ...",
  "timestamp": "2026-02-17T12:00:00Z",
  "source": "Argos|B2|GPT|LEAD|Human",
  "target": "Rex",
  "version": 1,
  "lease_token_required": 991, 
  "idempotency_key": "string",
  "ttl_s": 86400,
  "payload": { "..." }
}

Rules:
	•	seq is monotonic within runpoint_id
	•	idempotency_key is stable across retries
	•	ttl_s + timestamp define expiry
	•	lease_token_required must match current lease token for any dangerous operation

Bonus: include prev_hash/hash for tamper-evidence if you treat mailbox as part of your audit trail.

⸻

5) Firestore-backed Relay Layout (Google-scope friendly)

Collections (recommended)
	•	runpoints/{runpoint_id}/mailbox/{agent_id}/messages/{message_id}
	•	runpoints/{runpoint_id}/acks/{agent_id}/{message_id}
	•	runpoints/{runpoint_id}/leases/{agent_id}
	•	runpoints/{runpoint_id}/snapshots/{agent_id}
	•	runpoints/{runpoint_id}/incidents/{incident_id}
	•	runpoints/{runpoint_id}/effect_intents/{intent_id}

Indexing must support:
	•	fetch messages ordered by seq
	•	fetch undelivered messages where status != acked (or missing ack)
	•	query by time window for expiry cleanup

Note: Firestore listeners are a convenience. Catch-up must work by querying seq > last_seq_applied.

⸻

6) Delivery worker (relay daemon) — deterministic algorithm

Enqueue (producer side)
	1.	Validate envelope (no secrets, schema ok)
	2.	Write message to mailbox (durable)
	3.	Optionally emit an EVENT_ENQUEUED event for observability

Deliver (consumer side)

For each runpoint/agent:
	1.	Read last_seq_acked (or reconstruct from acks)
	2.	Fetch mailbox messages seq > last_seq_acked ordered, limited batch
	3.	For each message:
	•	if expired → mark expired, emit incident, continue
	•	attempt delivery to target agent’s inbox endpoint
	•	on success → write ack doc (idempotent upsert)
	•	on failure → retry with exponential backoff + jitter
	4.	Periodically garbage-collect old acked messages

Ack semantics (idempotent)

Ack doc write must be safe to repeat:
	•	acks/{message_id} is created once; further writes are no-ops.

Bonus: If you store the delivery_attempts counter and last_error, you get debugging for free.

⸻

7) Resurrection Timer — dumb by design

Timer does not route, reason, or “help”. It only:
	•	checks whether Rex is reachable/alive
	•	triggers the relay to drain mailbox when Rex returns

Availability check
	•	heartbeat events or a simple health endpoint
	•	or Firestore presence document updated by Rex

Wake sequence
	•	“Rex is alive” → relay switches from “queue-only” to “drain mode”

⸻

8) Rex boot protocol (the crucial “no loss, no staleness” sequence)

When Rex starts (or restarts):
	1.	Acquire lease (monotonic lease_token)
	2.	Load snapshot (last_seq_applied, state_hash, capsule)
	3.	Catch up by querying events/messages with seq > last_seq_applied to latest
	4.	Only after catch-up: drain mailbox in-order
	5.	Before any side-effect:
	•	verify lease token still current
	•	enforce TTL/staleness policy
	•	convert to effect intent if needed (outbox pattern)
	6.	Commit new snapshot and update heartbeat

Staleness policy (must exist):
	•	task.create can be executed after delay
	•	effect.request may require re-confirmation if age > threshold
	•	push now must expire or require “fresh approve” event

Bonus: This makes your system safe under long downtimes instead of “execute everything when back online”.

⸻

9) Side-effects: effect intents + receipts (no double pushes)

Never let mailbox messages directly do “dangerous” actions.
They should create effect intents.

Effect intent record

{
  "intent_id": "uuidv7",
  "runpoint_id": "rp_...",
  "kind": "git_commit|git_push|firestore_write|http_call",
  "idempotency_key": "same-as-message-or-derived",
  "lease_token": 991,
  "payload": { "..." },
  "status": "planned|sent|committed|failed",
  "receipt": { "commit_sha": "...", "response_hash": "..."},
  "created_at": "...",
  "updated_at": "..."
}

Executor rules:
	•	reject intents with stale lease_token
	•	dedupe on idempotency_key
	•	write receipts

Bonus: This is where you get “termination proof artifacts”.

⸻

10) Fancy bonuses (worth selling, worth community hype)

B1 — “Quota wall immunity”

Provider caps stop being outages; they become a logged degraded mode:
	•	system keeps queuing work and resumes safely

B2 — “Time travel”

Because everything is sequenced and replayable:
	•	you can replay the last week/month for debugging
	•	compare “what Rex would have done” vs “what proxy did”

B3 — “Transparent accountability”

Community gets:
	•	receipts for outcomes
	•	incident reports when things expire or get stuck
	•	audit trail for decisions

B4 — “Human-free mediation”

You’re no longer the courier between AIs:
	•	everyone writes to the same relay bus
	•	Rex drains when available

B5 — “Safe multi-runpoint expansion”

Same relay pattern supports:
	•	multiple personal runpoints
	•	strict isolation by runpoint_id

B6 — “Policy-driven staleness”

You can define:
	•	which messages may execute late
	•	which require re-approval
This avoids “surprise execution after downtime”.

B7 — “Commercial leverage”

You can sell this as:
	•	“resilient agent ops”
	•	“audit-grade multi-model office”
	•	“recoverable research pipelines”

⸻

11) Acceptance tests (must pass)

T1 — Rex down 12h
	•	messages queued
	•	no loss
	•	on wake: delivered once in order

T2 — Duplicate delivery attempts
	•	retries happen
	•	only one ack exists
	•	processing idempotent, no duplicated side-effects

T3 — STOP issued during downtime
	•	STOP event prevents dangerous intents post-wake
	•	lease token gating blocks stale execution

T4 — Split-brain (two Rex processes)
	•	only current lease token can commit intents
	•	stale Rex cannot push anything

T5 — Expiry/staleness
	•	late “push now” expires and logs incident
	•	late “task.create” still executes (if allowed)

⸻

12) Implementation roadmap (minimal pain)

Phase 0 (today)
	•	define envelope v1
	•	implement mailbox writes + ack docs
	•	implement drain logic by seq

Phase 1 (this week)
	•	leases + fencing token
	•	staleness/TTL policy
	•	incidents for expired/stuck messages

Phase 2
	•	effect intents + receipts executor
	•	deterministic snapshots + state_hash
	•	chaos tests

Phase 3
	•	fancy cockpit UI for relay state
	•	replay tooling + analytics

⸻

13) Don’t do these (common self-owns)
	•	Do not store “truth” in browser extension localStorage
	•	Do not rely on Firestore listener as the only mechanism (catch-up must exist)
	•	Do not allow mailbox messages to directly perform side-effects
	•	Do not skip lease/fencing (zombie worker will bite you)

⸻

14) Resulting posture

With relay + resurrection + leases + intents:
	•	quota walls become a delay, not a system failure
	•	restarting agents is safe and routine
	•	humans stop being couriers between models
	•	you get auditability and proof artifacts worthy of “bank-grade”

If you want an even more “product-grade” version, I can generate a companion `relay_api.md` that lists exact endpoints/tools for Office and for a future MCP gateway (inputs/outputs/error codes) — but this file above already captures the operational backbone and the sellable “bonuses.”