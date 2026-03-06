# Rhea Dashboard — User Guide

## Overview
The Rhea Dashboard is a mobile-responsive web interface for managing multi-device sessions, monitoring services, and visualizing real-time message synchronization with Lamport Clock ordering.

## Getting Started

### Start the Dashboard
```bash
cd rhea-dashboard
npm install && npm run dev
```
Opens on `http://localhost:5173`

### Create Your First Session
1. Open dashboard
2. Go to **Chains** tab
3. Click **Create Session** button
4. Select a character (Protos, Zerg, Terran, Aeon)
5. Give it a name
6. Session appears in Chains list with sync status

## Chains Tab
**View all active sessions and their synchronization status.**

- **Session ID**: Unique identifier (first 8 chars shown)
- **Message Count**: Number of messages in session
- **Lamport Clock (LC)**: Current causal timestamp (higher = more recent messages)
- **Devices**: Number of connected devices
- **Sync Status**: Green dot = all devices synchronized, Yellow = catching up

### Multi-Device Workflow
1. Open same session ID on Device 1 and Device 2
2. Both devices show identical message order (LC-based)
3. Add message on Device 1 → LC increments
4. Device 2 automatically fetches → sees new message with correct LC
5. Messages are causally ordered: no race conditions, no conflicts

### Reading Order
Messages are sorted by **Lamport Clock**, not creation time. This ensures:
- Same order on every device
- Deterministic behavior (no randomness)
- Causal relationships preserved (if A references B, B appears first)

## Procs Tab
**Monitor all running services.**

Each service shows:
- **Name**: Service identifier
- **Port**: REST API port
- **Status**: Running (green) or Stopped (red)
- **Uptime**: How long service has been running
- **CPU/Memory**: Resource usage

### Services
1. **Session Server** (3000) — Message storage + LC assignment
2. **AI Auth** (3001) — Challenge-response authentication
3. **Angel Game** (3002) — Decision evaluation + scoring
4. **BioRenderer** (3003) — Scientific figure generation
5. **RAG Storage** (3004) — Context indexing + semantic search

## Bottom Navigation

### 🤖 AI
Manage AI authentication and model settings.
- View challenges issued
- Test auth endpoint
- Configure model parameters

### 👥 People
Collaboration and device management.
- Add collaborators to session
- Manage device permissions
- View device connection history

### 🛡️ Shield
Security and access control.
- Review access logs
- Manage API keys
- Configure TLS certificates

### 🛒 Services
Manage integrated services.
- Health check each service
- View service logs
- Restart services

### 📖 Docs
Developer documentation (opens external link to docs/).

### 🔴 Live
Real-time session visualization (Session Flight).
- See Lamport Clock timeline
- View causal graph
- Color-coded by device
- Shows convergence in action

## Session Flight (Real-Time Sync Visualization)

Session Flight visualizes how messages converge across devices using Lamport Clocks.

### Components
1. **LC Timeline**: Horizontal axis = Lamport Clock value
2. **Causal Graph**: Arrows show message dependencies
3. **Device Lanes**: One row per device (color-coded)
4. **Convergence**: All devices reach same LC = ✅ synced

### Reading the Graph
```
Device 1: [msg1] -→ [msg2] -→ [msg3]   (LC: 1, 2, 3)
             ↓       ↓       ↓
Device 2: [msg1] -→ [msg2] -→ [msg3]   (LC: 1, 2, 3)

Both devices see identical order, guaranteed by LC.
```

### How It Works
1. Device 1 sends message → Server assigns LC=5
2. Device 2 sends message → Server assigns LC=6 (not 2!)
3. When Device 2 fetches Device 1's message, it sees LC=5
4. Even with network delay, order is deterministic

## API Integration

Dashboard uses these endpoints:

### Session Server
```
GET  /sessions              → List all sessions
POST /sessions              → Create new session
GET  /sessions/:id          → Get session details + messages
POST /sessions/:id/messages → Add message to session
```

### Example: Create & Sync
```bash
# Device 1: Create session
curl -X POST http://localhost:3000/sessions \
  -H "Content-Type: application/json" \
  -d '{"character":"Protos"}'

# Returns: { "id": "abc-123-def", ... }

# Device 1: Add message
curl -X POST http://localhost:3000/sessions/abc-123-def/messages \
  -d '{"role":"Protos","content":"Hello!","device_id":"device-1"}'

# Returns: { "lamport_clock": 1, ... }

# Device 2: Fetch session (same session ID)
curl http://localhost:3000/sessions/abc-123-def

# Sees: messages ordered by LC (guaranteed same as Device 1!)
```

## Troubleshooting

### Messages appear out of order
→ **Check Lamport Clocks**: Dashboard sorts by LC, not created_at.
→ **Verify clock sync**: LC should increment monotonically (1, 2, 3, ...)
→ **Clear browser cache**: Old message list may be cached

### Session shows "syncing..." indefinitely
→ **Check network**: Can dashboard reach localhost:3000?
→ **Restart Session Server**: `scripts/stage4_deploy.sh start session`
→ **Check logs**: `logs/stage4/session-server.log`

### Device shows different message count
→ **Wait 2-5 seconds**: Background sync may still be fetching
→ **Manual refresh**: Click session → Pull down to refresh
→ **Check device_id**: Each device must have unique device_id

### Service status shows red (stopped)
→ **Start all services**: `bash scripts/stage4_deploy.sh start all`
→ **Check ports**: `lsof -i :3000` (for port 3000, etc.)
→ **View logs**: `bash scripts/stage4_deploy.sh logs session`

## Performance Tips

1. **Large sessions (1000+ messages)**: Use search/filter
2. **Many devices (10+)**: LC may reach 2^64 eventually (use LC++ after restart)
3. **Offline devices**: Queue messages, sync on reconnect (idempotent)
4. **Mobile**: Dashboard is responsive — works on phones/tablets

## Next Steps

- **Try multi-device**: Open session on 2 devices simultaneously
- **Test offline**: Disconnect network, queue messages, reconnect
- **Explore Services**: Call BioRenderer endpoint to see SVG output
- **Read Theory**: See `docs/dev/architecture/dts.md` for DTS proofs

---

**Questions?** Check `docs/` directory or run `bash test_integration.sh` to verify system.
