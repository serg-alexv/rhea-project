---
sidebar_position: 1
---

# Services

The Rhea system comprises multiple services that communicate over HTTP, TCP, and SSE.

## Service Topology

| Service | Port | Language | Description |
|---------|------|----------|-------------|
| **Tribunal API** | 8400 | Python/FastAPI | Main API server — tribunal, clipboard, office, salon, orchestration, billing |
| **Session Server** | 3000 | Rust/Axum | Session CRUD with Lamport clocks and character system |
| **frontier-gem** | 3456 (HTTP), 4444 (TCP) | Rust | Local daemon — 0.log writer, mDNS discovery, clipboard proxy |
| **rhea-dash** | — | Rust/egui+wgpu | GPU-rendered agent dashboard (desktop app, not a network service) |
| **Caddy** | 80/443 | Go | Reverse proxy with auto-TLS (production only) |
| **MongoDB** | 27017 | — | Optional change-stream source → SSE push |
| **CockroachDB** | — | — | Optional distributed persistence |

## Communication Patterns

### Tribunal API → Rhea Bridge → LLM Providers

The Tribunal API is the central hub. When a `/tribunal` request arrives:

1. FastAPI handler validates auth (JWT Bearer or X-API-Key)
2. Rate limiter checks per-minute and daily quotas
3. `RheaBridge.tribunal()` fans out to `k` models concurrently via `ThreadPoolExecutor`
4. `ConsensusAnalyzer` computes agreement scores, stance summaries, divergence points
5. Response is persisted to SQLite (`rhea_db.persist_history()`) and broadcast on SSE

### frontier-gem → 0.log (Event Bus)

frontier-gem is the **sole writer** to `/tmp/0.log`. Other services send events to frontier-gem via:
- **HTTP POST** to `:3456` — any JSON payload becomes a hash-chained Frame
- **TCP** to `:4444` — bidirectional bus; clients both send events and receive broadcasts

### SSE Radio (Tribunal API)

The Tribunal API maintains an in-memory event bus with SSE streaming:
- `GET /feed` — SSE stream of all system events
- Events include: tribunal results, office messages, clipboard changes, MongoDB change stream events
- In-memory radio log capped at 200 items
- Write-through to `radio` table in SQLite

### Session Server ↔ Clients

The Rust session server provides a simpler, lower-latency path for session operations:
- In-memory `Vec<Session>` store (no persistence — designed for CRDT sync later)
- Lamport clock incremented on each message
- Independent from the Tribunal API — can run standalone

## Data Flow Diagram

```
Client App
    │
    ├─── POST /tribunal ──────► Tribunal API ──► RheaBridge ──► LLM Providers
    │                                │                              │
    │                                ├─ persist_history() ──► SQLite
    │                                ├─ _broadcast_event() ──► SSE subscribers
    │                                └─ record_usage() ──► billing credits
    │
    ├─── POST /sessions ──────► Session Server (Rust)
    │         (Lamport clocks)
    │
    └─── POST :3456 ─────────► frontier-gem ──► 0.log (hash chain)
              (local only)         │
                                   └─► mDNS broadcast
```
