# 🚀 Rhea Stage 4 — Quick Start

Multi-device sync with **deterministic ordering** + **AI-only auth** + **beautiful developer portal**.

## What's Running

| Service | Port | Purpose |
|---------|------|---------|
| **Session Server** | `:3000` | Multi-device message sync (Lamport Clocks) |
| **CLI** | Interactive | Terminal UI (ratatui, async, sub-100ms) |
| **AI Auth** | `:3001` | Inverse captcha (AI-solvable, human-proof) |

## One-Line Start

```bash
# Terminal 1: Session Server
cd rhea-session-server && cargo run --release

# Terminal 2: AI Auth Service
cd rhea-ai-auth && cargo run --release

# Terminal 3: CLI (interactive)
cd rhea-cli && cargo run --release
```

Verify health:
```bash
curl http://127.0.0.1:3000/health    # Session server
curl http://127.0.0.1:3001/health    # AI auth
```

## Key Features

### 🔐 Deterministic Time System (DTS)
Messages are ordered by **Lamport Clocks**, not wall-clock time.
- ✅ Works offline (devices reason locally)
- ✅ CRDT-safe (all devices converge to same order)
- ✅ No external clock dependencies
- 📖 [Philosophy](docs/dev/architecture/philosophy.md) | [Technical](docs/dev/architecture/dts.md)

### 🤖 AI-Only Auth (Inverse Captcha)
POST `/auth/challenge` → receive code template + target hash
- AI must reason about the template and generate code that outputs the target string
- Hash reversal is computationally infeasible (humans can't brute-force SHA256)
- Only models with pattern matching + reasoning can pass
- 📖 [Architecture](rhea-ai-auth/README.md)

### 💻 Async CLI
Built with **tokio** + **ratatui**, sub-100ms responsiveness.
- Live message sync
- Non-blocking keyboard input
- Color-coded output with emojis
- 📖 [Features & Troubleshooting](rhea-cli/README.md)

## API Examples

### Create a Session
```bash
curl -X POST http://127.0.0.1:3000/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "device_id": "macbook-1", "character": "Protos"}'
```

Response:
```json
{
  "id": "6375fe86-9079-422c-8ea4-647719fd98c0",
  "character": "Protos",
  "title": "PROTOS session",
  "message_count": 0,
  "created_at": "2026-03-06T03:34:05.818256Z",
  "updated_at": "2026-03-06T03:34:05.818256Z"
}
```

### Add a Message
```bash
SESSION_ID="6375fe86-9079-422c-8ea4-647719fd98c0"
curl -X POST http://127.0.0.1:3000/sessions/$SESSION_ID/messages \
  -H "Content-Type: application/json" \
  -d '{
    "role": "Protos",
    "content": "hello from device 1",
    "device_id": "macbook-1"
  }'
```

Response includes `lamport_clock` (deterministic ordering guarantee):
```json
{
  "id": "b87d976a-104d-481e-a4eb-22e2dbcbad86",
  "created_at": 1772768060,
  "lamport_clock": 1,
  "content": "hello from device 1",
  "device_id": "macbook-1"
}
```

### Get Session with Messages (Always Ordered by LC)
```bash
curl http://127.0.0.1:3000/sessions/6375fe86-9079-422c-8ea4-647719fd98c0
```

Returns session + messages sorted by `lamport_clock ASC`.

### AI Auth Challenge
```bash
curl -X POST http://127.0.0.1:3001/auth/challenge \
  -H "Content-Type: application/json" \
  -d '{"model_name": "claude-opus-4.6"}'
```

Response:
```json
{
  "challenge_id": "chal_xyz789...",
  "code_template": "def solve():\n    # Your code here\n    return ...",
  "target_hash": "a1b2c3d4e5f6...",
  "difficulty": "medium"
}
```

Submit solution:
```bash
curl -X POST http://127.0.0.1:3001/auth/verify \
  -H "Content-Type: application/json" \
  -d '{
    "challenge_id": "chal_xyz789...",
    "solution_code": "def solve():\n    return \"secret_string\"\n"
  }'
```

## Directory Structure

```
rhea-session-server/   ← Multi-device sync (DTS implementation)
  ├─ src/lib.rs        ← Lamport Clock logic, message ordering
  └─ src/bin/server.rs ← HTTP endpoints (/sessions, /messages)

rhea-cli/              ← Interactive terminal UI
  ├─ src/main.rs       ← Async event loop (tokio::select!)
  ├─ src/ui.rs         ← ratatui rendering
  └─ README.md         ← Features & troubleshooting

rhea-ai-auth/          ← Inverse captcha service
  ├─ src/main.rs       ← /auth/challenge & /auth/verify endpoints
  └─ README.md         ← Challenge algorithm

docs/dev/              ← Beautiful developer portal
  ├─ architecture/     ← Philosophy, DTS, CRDT, causality
  ├─ api/              ← Endpoint reference
  └─ examples/         ← Code samples
```

## Documentation

- **[Developer Portal](docs/dev/)** — Architecture philosophy, DTS deep-dive, API reference
- **[Architecture Decisions (ADRs)](docs/decisions.md)** — Why DTS, why async, why inverse captcha (ADR-017)
- **[Session State](SESSION_STATE.md)** — Current build status, commits, features

## Testing

### Manual: Create 2-Device Session
1. **Device 1**: `curl -X POST http://127.0.0.1:3000/sessions -d '...' → sess_1`
2. **Device 2**: Same session ID
3. **Device 1**: Post 3 messages → LC = 1, 2, 3
4. **Device 2**: Post 2 messages → LC = 4, 5 (server assigns next LCs)
5. **Both**: `GET /messages` → Same order on both devices ✓

### Manual: AI Auth Challenge
1. `POST /auth/challenge` → get code template + target hash
2. Submit solution with matching hash → get auth token
3. Verify token is returned (not stored for stateless design)

### Automated (Future)
```bash
cargo test --all
```

## Troubleshooting

### "Connection refused" on port 3000
- Session server not running. Start it: `cd rhea-session-server && cargo run --release`

### CLI freezing on input
- Fixed in v0.2 (async refactor). Update: `git pull origin stage4-release`

### AI Auth challenge too hard
- Difficulty auto-scales based on model tier. Use `difficulty: "easy"` in challenge request.

## Next Steps

- [ ] Wire AI auth tokens into session server (authenticated access)
- [ ] Integrate PlayUI components (swap ratatui)
- [ ] Cross-device testing (real network, not localhost)
- [ ] Production deployment (Cloud Run, launchd daemon)

## Links

- **GitHub**: [timelabs/rhea-project](https://github.com/timelabs/rhea-project)
- **Issue**: [Session system + DTS](https://github.com/timelabs/rhea-project/issues/42)
- **Slack**: #rhea-engineering

---

**Last updated**: 2026-03-06 | **Branch**: `stage4-release` | **Build**: ✅ All services shipping
