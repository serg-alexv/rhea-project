---
sidebar_position: 1
---

# frontier-gem

A Rust daemon that acts as the local system bridge — writing to the 0.log event bus, discovering peers via mDNS, proxying clipboard requests, and providing AI-powered focus tracking.

## Architecture

```
┌─────────────────────────────────────────┐
│            frontier-gem daemon           │
│                                          │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ HTTP     │  │ TCP Bus  │  │ mDNS   │ │
│  │ :3456    │  │ :4444    │  │ disco  │ │
│  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       │             │            │       │
│       └──────┬──────┘            │       │
│              ▼                   │       │
│       ┌────────────┐             │       │
│       │   0.log    │◄────────────┘       │
│       │ /tmp/0.log │                     │
│       └────────────┘                     │
│                                          │
│  ┌──────────────┐  ┌──────────────────┐  │
│  │ Clipboard    │  │ DTN Outbox       │  │
│  │ Proxy        │  │ ~/.frontier_     │  │
│  │ → fly.dev    │  │    outbox.jsonl  │  │
│  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────┘
```

## Running

```bash
cd frontier-gem
cargo build --release
./target/release/frontier-gem daemon
```

The `daemon` mode starts all subsystems:
- **HTTP server** on `127.0.0.1:3456`
- **TCP bus** on `127.0.0.1:4444`
- **mDNS** registration as `_frontier-gem._tcp.local.`

## HTTP Endpoints (port 3456)

### GET /api/discovery

Returns AI discovery state: active nodes, system focus (which app is in foreground), and window metadata.

```bash
curl http://127.0.0.1:3456/api/discovery
```

Response includes:
- Active mDNS-discovered nodes
- Current focused application (`system_focus`)
- Focused window class and title
- Timestamp of focus update

Each discovery request also appends a frame to 0.log.

### POST /api/inject

Inject text into the currently focused window (platform-dependent).

```bash
curl -X POST http://127.0.0.1:3456/api/inject \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, world!", "delay_ms": 50}'
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `text` | string | *required* | Text to inject |
| `delay_ms` | int | 50 | Delay between keystrokes in ms |

### POST /api/clipboard/* and GET /api/clipboard/*

Clipboard requests are proxied to the upstream Tribunal API:
- Upstream: `RHEA_SERVER` env var (default: `https://rhea-tribunal.fly.dev`)
- Auth: `RHEA_AUTH_TOKEN` env var forwarded as `Authorization: Bearer`

**Exception:** `GET /api/clipboard/stream` returns 501 — SSE proxy is not yet implemented.

### POST / (generic event)

Any POST with a JSON body creates a hash-chained frame in 0.log:

```bash
curl -X POST http://127.0.0.1:3456/ \
  -H "Content-Type: application/json" \
  -d '{"event": "custom", "data": "anything"}'
```

## TCP Bus (port 4444)

The TCP bus is bidirectional:
- **Send:** Write JSON lines to the socket → each line becomes a 0.log frame
- **Receive:** All frames broadcast to all connected TCP clients

```bash
# Connect and receive all events
nc 127.0.0.1 4444

# Send an event
echo '{"type":"heartbeat","agent":"A1"}' | nc 127.0.0.1 4444
```

TCP connections use `tokio::select!` to handle concurrent read and write tasks.

## mDNS Discovery

frontier-gem registers itself as `_frontier-gem._tcp.local.` on port 4444 using `mdns-sd`. It also browses for other gem instances, enabling automatic peer discovery on the local network.

## DTN Outbox

When TCP bus connections fail, events are buffered to `~/.frontier_outbox.jsonl`. The `drain_outbox()` function periodically attempts to replay buffered events via TCP. Lines that succeed are removed; failures remain in the outbox.

## Modules

| Module | Description |
|--------|-------------|
| `windows_injector` | Platform-specific text injection (keystroke simulation) |
| `discovery` | `DiscoveryState` struct with example nodes and system info |
| `focus` | `get_focused_window()` — returns process name, window class, title |
| `clipboard` | Clipboard monitoring and relay |

## Build Dependencies

```toml
[dependencies]
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
sha2 = "0.10"
hex = "0.4"
chrono = "0.4"
mdns-sd = "0.11"
tokio = { version = "1", features = ["full"] }
reqwest = { version = "0.12", features = ["json"] }
```
