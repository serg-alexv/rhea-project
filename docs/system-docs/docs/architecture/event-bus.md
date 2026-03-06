---
sidebar_position: 2
---

# Event Bus — 0.log

The **0.log** (`/tmp/0.log`) is Rhea's universal event bus: a hash-chained, append-only JSONL file that records every system event with tamper-evident integrity.

## Design Philosophy

Instead of a message broker (Kafka, RabbitMQ), Rhea uses a **file-based event log** — simple, debuggable, zero-dependency. The frontier-gem daemon is the sole writer, ensuring consistent hash chaining.

## Frame Structure

Every event is a `Frame` — a JSON object with a cryptographic link to the previous frame:

```rust
struct Frame {
    prev_hash: String,          // SHA-256 of the previous frame
    timestamp: i64,             // Unix millis (UTC)
    origin: String,             // Source identifier (e.g., "http", "cl-tcp", "discovery")
    payload: serde_json::Value, // Arbitrary JSON event data
    hash: String,               // SHA-256(prev_hash + timestamp + payload)
}
```

### Hash Chain Computation

```rust
let mut hasher = Sha256::new();
hasher.update(prev_hash.as_bytes());
hasher.update(timestamp.to_string().as_bytes());
hasher.update(serde_json::to_string(&payload).unwrap().as_bytes());
let hash = hex::encode(hasher.finalize());
```

The first frame uses `prev_hash = "0"` (genesis).

## Example Frames

```json
{"prev_hash":"0","timestamp":1719500000000,"origin":"discovery","payload":{"nodes_count":3,"focus":"Xcode"},"hash":"a1b2c3..."}
{"prev_hash":"a1b2c3...","timestamp":1719500001234,"origin":"http","payload":{"status":"ok","path":"/api/event"},"hash":"d4e5f6..."}
```

## Writing Events

Only **frontier-gem** writes to 0.log. Events arrive via two channels:

### HTTP (port 3456)
Any POST request with a JSON body creates a frame:
```bash
curl -X POST http://127.0.0.1:3456/ \
  -H "Content-Type: application/json" \
  -d '{"event": "user_action", "detail": "opened settings"}'
```

### TCP Bus (port 4444)
Bidirectional: clients send JSON lines, receive all broadcast frames:
```bash
echo '{"event":"heartbeat"}' | nc 127.0.0.1 4444
```

## Reading Events

0.log is a plain JSONL file. Read it with standard tools:
```bash
# Last 5 events
tail -5 /tmp/0.log | jq .

# Events from a specific origin
grep '"origin":"discovery"' /tmp/0.log | jq .

# Verify hash chain integrity
python3 -c "
import json, hashlib
lines = open('/tmp/0.log').readlines()
for i, line in enumerate(lines):
    frame = json.loads(line)
    if i > 0:
        prev = json.loads(lines[i-1])
        assert frame['prev_hash'] == prev['hash'], f'Chain broken at line {i}'
print(f'Chain valid: {len(lines)} frames')
"
```

## DTN Outbox (Offline Support)

When the TCP bus is unreachable, frontier-gem buffers events to `~/.frontier_outbox.jsonl`. On reconnection, the `drain_outbox()` function replays buffered events:

```
Client offline → buffer to ~/.frontier_outbox.jsonl
Client online  → drain_outbox() replays via TCP :4444
```

## Event Origins

| Origin | Source |
|--------|--------|
| `http` | Generic HTTP POST to frontier-gem |
| `cl-tcp` | TCP bus client message |
| `discovery` | AI discovery endpoint (focus tracking) |
| `inject` | Text injection event |
| `clipboard` | Clipboard proxy event |

## File Permissions

0.log is created with mode `0o666` (world-readable/writable) to allow any local process to read events without privilege issues.
