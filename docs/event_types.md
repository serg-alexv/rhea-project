# Event Types — Canonical Payload Schemas

> Companion to lesson 11 (event sourcing). Every event that flows through Rhea has a type, a schema, and a contract.
> Created: 2026-02-17 | Author: Argos (COWORK) | Status: LIVING DOCUMENT

## Conventions

Every event payload follows these invariants:

```
timestamp    string   ISO 8601 UTC, always present, never empty
event_type   string   one of the types defined below (enum, not freeform)
source       string   "{desk}.{component}" e.g. "B2.bridge", "LEAD.office", "COWORK.audit"
version      int      schema version, starts at 1, bumped on breaking changes
trace_id     string   optional, 16-char hex, groups related events across components
```

Payloads are JSON objects. All fields required unless marked `[opt]`. Unknown fields are preserved (open schema), not rejected.

---

## 1. Bridge Events

Source: `src/rhea_bridge.py` → `logs/bridge_calls.jsonl`

### `bridge.call`

A single LLM API call completed (success or failure).

```jsonc
{
  "event_type": "bridge.call",
  "timestamp": "2026-02-16T17:44:28.751968+00:00",
  "version": 1,
  "source": "B2.bridge",
  "provider": "openai",               // anthropic | openai | gemini | deepseek | openrouter | huggingface | azure
  "model": "gpt-4o-mini",             // provider-specific model identifier
  "request_id": "988135cf-...",        // UUID, unique per call
  "prompt_tokens": 8,
  "completion_tokens": 10,
  "total_tokens": 18,
  "cost_usd": 0.0000072,              // estimated cost from provider pricing
  "latency_ms": 1744.4,
  "status": "ok",                      // "ok" | HTTP status code as string ("401", "404", "429")
  "error_short": "",                   // empty on success, one-line error on failure
  "tier": "cheap",                     // [opt] "cheap" | "balanced" | "expensive"
  "trace_id": ""                       // [opt] links to parent tribunal or cascade
}
```

### `bridge.probe`

Health probe result for a single provider.

```jsonc
{
  "event_type": "bridge.probe",
  "timestamp": "2026-02-16T17:45:00.000000+00:00",
  "version": 1,
  "source": "OPS.probe",
  "provider": "azure",
  "status": "down",                    // "live" | "down"
  "http_code": 401,                    // [opt] actual HTTP response code
  "error_class": "UNAUTHENTICATED",   // [opt] from ERROR_MAP
  "latency_ms": 1147.0
}
```

---

## 2. Tribunal Events

Source: `src/tribunal_api.py` + `src/consensus_analyzer.py` → `logs/tribunal_api_calls.jsonl`

### `tribunal.request`

A tribunal session was requested.

```jsonc
{
  "event_type": "tribunal.request",
  "timestamp": "2026-02-17T08:58:07.877+00:00",
  "version": 1,
  "source": "API.tribunal",
  "trace_id": "3aded910e7890784",     // prompt_hash, groups all calls in this tribunal
  "prompt_hash": "3aded910e7890784",   // SHA256 prefix of the prompt
  "mode": "local",                     // "local" | "chairman" | "ice"
  "k": 2,                             // number of models queried
  "tier": "cheap",                     // [opt] model tier used
  "models": ["gpt-4o-mini", "gemini-2.0-flash"]  // [opt] specific models
}
```

### `tribunal.response`

A tribunal session completed.

```jsonc
{
  "event_type": "tribunal.response",
  "timestamp": "2026-02-17T08:58:09.253+00:00",
  "version": 1,
  "source": "API.tribunal",
  "trace_id": "3aded910e7890784",
  "prompt_hash": "3aded910e7890784",
  "k": 2,
  "elapsed_s": 1.375,
  "status": "ok",                      // "ok" | "partial" (some models failed) | "error"
  "consensus": {
    "agreement_score": 0.82,           // 0.0–1.0, TF-IDF cosine average
    "confidence": 0.78,                // 0.0–1.0, composite metric
    "analysis_method": "tfidf_local",  // "tfidf_local" | "chairman" | "ice_iterative"
    "convergence_achieved": false,     // ICE only
    "rounds_completed": 0,            // ICE only
    "model_count": 2,
    "successful_count": 2
  }
}
```

---

## 3. Firebase / Office Events

Source: `ops/rhea_firebase.py` → `logs/firebase_calls.jsonl` + Firestore collections

### `office.heartbeat`

Agent reports alive status.

```jsonc
{
  "event_type": "office.heartbeat",
  "timestamp": "2026-02-17T08:59:00.000+00:00",
  "version": 1,
  "source": "B2.office",
  "desk": "B2",                        // LEAD | B2 | GPT | COWORK
  "status": "ALIVE",                   // "ALIVE" | "BUSY" | "IDLE" | "DOWN"
  "last_seen": "2026-02-17T08:59:00.000+00:00"
}
```

### `office.message`

Inter-agent message sent via inbox.

```jsonc
{
  "event_type": "office.message",
  "timestamp": "2026-02-17T09:18:28.544+00:00",
  "version": 1,
  "source": "COWORK.office",
  "from": "COWORK",
  "to": "B2",
  "priority": "P1",                    // [opt] "P0" | "P1" | "P2" | "P3"
  "subject": "rex-down-need-help",     // [opt] slug from filename
  "read": false
}
```

### `office.gem`

Knowledge artifact captured.

```jsonc
{
  "event_type": "office.gem",
  "timestamp": "2026-02-16T22:00:00.000+00:00",
  "version": 1,
  "source": "COWORK.office",
  "gem_id": "GEM-006",                // GEM-NNN format
  "topic": "cascade-tables",
  "text": "A cascade table is a shared mutable state surface...",
  "origin_desk": "COWORK",
  "promotion_count": 0                // incremented on each reference; 3 → PROCEDURE
}
```

### `office.incident`

Something broke.

```jsonc
{
  "event_type": "office.incident",
  "timestamp": "2026-02-16T23:00:00.000+00:00",
  "version": 1,
  "source": "COWORK.office",
  "incident_id": "INC-2026-02-16-006",  // INC-YYYY-MM-DD-NNN
  "symptom": "Rex session dropped with HTTP 400",
  "severity": "P0",                    // P0 critical | P1 high | P2 medium | P3 low
  "status": "DOWN",                    // "NEW" | "DOWN" | "WORKAROUND" | "RESOLVED"
  "affected_desk": "LEAD"             // [opt] which desk is impacted
}
```

### `office.decision`

A decision was made and recorded.

```jsonc
{
  "event_type": "office.decision",
  "timestamp": "2026-02-16T23:30:00.000+00:00",
  "version": 1,
  "source": "LEAD.office",
  "decision_id": "DEC-008",           // DEC-NNN
  "what": "Pursue Tribunal as a Service + Open Core",
  "why": "3/3 tribunal unanimous, highest score 28.3/40",
  "who": "Tribunal → Rex approved",
  "reversible": true,
  "evidence": "ops/virtual-office/inbox/TRIBUNAL_20260216_commercial-strategy.md"
}
```

---

## 4. Firestore Transport Events

Source: `ops/rhea_firebase.py` → `logs/firebase_calls.jsonl` (meta-level: tracking Firestore itself)

### `transport.firestore`

Raw Firestore API call result.

```jsonc
{
  "event_type": "transport.firestore",
  "timestamp": "2026-02-17T08:58:30.532+00:00",
  "version": 1,
  "source": "B2.firebase",
  "method": "GET",                     // "GET" | "PATCH" | "POST"
  "collection": "agents",             // Firestore collection name
  "doc_id": "",                        // [opt] specific document
  "http_status": 200,
  "latency_ms": 1625,
  "error": null,                       // null on success, ERROR_MAP string on failure
  "root_cause": null                   // null on success, detail string on failure
}
```

---

## 5. Git Events

Source: git hooks / push protocol (proposed — not yet implemented)

### `git.push`

A batch of commits pushed to remote.

```jsonc
{
  "event_type": "git.push",
  "timestamp": "2026-02-17T09:00:00.000+00:00",
  "version": 1,
  "source": "COWORK.git",
  "branch": "feat/chronos-agents-and-bridge",
  "commit_hash": "dd2eb62",
  "commit_count": 1,
  "files_changed": 2,
  "insertions": 69,
  "deletions": 0,
  "message": "Argos says hello — status report to Rex + greetings to B2 and GPT"
}
```

### `git.conflict`

Push rejected, rebase required.

```jsonc
{
  "event_type": "git.conflict",
  "timestamp": "2026-02-17T09:01:00.000+00:00",
  "version": 1,
  "source": "COWORK.git",
  "branch": "feat/chronos-agents-and-bridge",
  "local_head": "e5768e2",
  "remote_head": "7df5740",
  "resolution": "rebase_success"      // "rebase_success" | "rebase_conflict" | "force_push" | "abandoned"
}
```

---

## 6. Session Lifecycle Events

Source: agent runtime (proposed — partially implemented via capsule)

### `session.start`

Agent session initialized.

```jsonc
{
  "event_type": "session.start",
  "timestamp": "2026-02-16T14:00:00.000+00:00",
  "version": 1,
  "source": "COWORK.session",
  "desk": "COWORK",
  "agent_name": "Argos",
  "model": "claude-opus-4-6",
  "terminal": "Cowork Desktop App",
  "context_tokens_used": 0,
  "session_id": "283219b7-34b4-..."   // [opt] unique session identifier
}
```

### `session.crash`

Agent session terminated unexpectedly.

```jsonc
{
  "event_type": "session.crash",
  "timestamp": "2026-02-17T00:30:00.000+00:00",
  "version": 1,
  "source": "LEAD.session",
  "desk": "LEAD",
  "agent_name": "Rex",
  "error_code": 400,
  "last_commit": "b604627",
  "data_loss": false,                  // true if uncommitted work existed
  "uptime_hours": 10.5                // [opt] session duration before crash
}
```

### `session.compaction`

Context window compacted (summary replaced full transcript).

```jsonc
{
  "event_type": "session.compaction",
  "timestamp": "2026-02-17T08:00:00.000+00:00",
  "version": 1,
  "source": "COWORK.session",
  "desk": "COWORK",
  "tokens_before": 195000,
  "tokens_after": 12000,
  "turns_summarized": 31,
  "summary_location": "inline"        // "inline" | "file:{path}"
}
```

---

## 7. Cascade Table Events

Source: Firebase Realtime DB / Firestore (proposed — extends GEM-006)

### `cascade.write`

Agent appended a row to a cascade table.

```jsonc
{
  "event_type": "cascade.write",
  "timestamp": "2026-02-17T10:00:00.000+00:00",
  "version": 1,
  "source": "B2.cascade",
  "table": "schedule_cascade",        // cascade table name
  "row_id": "row_003",
  "desk": "B2",
  "depends_on": "row_002",            // [opt] which row this agent read before writing
  "payload_keys": ["priority", "action", "confidence"]  // what fields were written (not values)
}
```

### `cascade.read`

Agent read from a cascade table.

```jsonc
{
  "event_type": "cascade.read",
  "timestamp": "2026-02-17T10:00:01.000+00:00",
  "version": 1,
  "source": "GPT.cascade",
  "table": "schedule_cascade",
  "rows_read": 3,
  "latest_row_id": "row_003",
  "desk": "GPT"
}
```

---

## Event Type Registry (summary)

| Type | Source Component | Log Destination | Status |
|------|-----------------|-----------------|--------|
| `bridge.call` | rhea_bridge.py | bridge_calls.jsonl | **LIVE** |
| `bridge.probe` | bridge-probe.sh | bridge_calls.jsonl | **LIVE** |
| `tribunal.request` | tribunal_api.py | tribunal_api_calls.jsonl | **LIVE** |
| `tribunal.response` | tribunal_api.py | tribunal_api_calls.jsonl | **LIVE** |
| `office.heartbeat` | rhea_firebase.py | firebase_calls.jsonl + Firestore | **LIVE** |
| `office.message` | rhea_firebase.py | firebase_calls.jsonl + Firestore | **LIVE** |
| `office.gem` | rhea_firebase.py | Firestore | **LIVE** |
| `office.incident` | rhea_firebase.py | Firestore | **LIVE** |
| `office.decision` | DECISIONS.md | git only (no JSONL yet) | **PARTIAL** |
| `transport.firestore` | rhea_firebase.py | firebase_calls.jsonl | **LIVE** |
| `git.push` | git hooks | not yet implemented | **PROPOSED** |
| `git.conflict` | git hooks | not yet implemented | **PROPOSED** |
| `session.start` | agent runtime | not yet implemented | **PROPOSED** |
| `session.crash` | agent runtime | not yet implemented | **PROPOSED** |
| `session.compaction` | agent runtime | not yet implemented | **PROPOSED** |
| `cascade.write` | Firebase cascade | not yet implemented | **PROPOSED** |
| `cascade.read` | Firebase cascade | not yet implemented | **PROPOSED** |

## Migration Path

Current JSONL logs do not include `event_type` or `version` fields. To unify:

1. Add `event_type` and `version` to all existing log writers (bridge, tribunal, firebase)
2. Existing logs remain valid — missing `event_type` implies the log file determines type (bridge_calls.jsonl → `bridge.call`)
3. Once unified, all events can flow to a single `events.jsonl` or Firestore `events` collection
4. Proposed events (git, session, cascade) implement when the component exists

## Schema Evolution Rules

1. New optional fields: add freely, bump `version` only if consumer behavior changes
2. New required fields: BREAKING — bump `version`, update all producers and consumers
3. Removed fields: BREAKING — bump `version`, keep field in schema for 2 versions with `[deprecated]` tag
4. Type changes: NEVER — create a new field instead
5. Every schema change gets a GEM or DECISION entry explaining why
