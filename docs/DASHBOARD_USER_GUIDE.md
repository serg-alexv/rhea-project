# Dashboard User Guide — Stage 5

**For:** Non-technical users, team managers, product owners

---

## Quick Start (2 minutes)

### 1. Start Services
```bash
bash scripts/stage4_deploy.sh start all
```
Wait for: `✓ All services started`

### 2. Open Dashboard
```bash
open rhea-dashboard/dist/index.html
```
Or paste in browser: `file:///Users/sa/rh.1/rhea-dashboard/dist/index.html`

### 3. Create a Session
Open Terminal and run:
```bash
curl -X POST http://127.0.0.1:3000/sessions \
  -H "Content-Type: application/json" \
  -d '{"character":"PROTOS"}'
```

### 4. Watch the Dashboard
- Click **Chains** tab
- You should see your session in the **Session Flight Timeline**
- The progress bar shows Lamport Clock progression

**Done!** Dashboard is now live.

---

## How to Use (By Tab)

### 🔗 Chains Tab (Default)
**What:** Session Flight Visualization  
**Shows:**
- Session ID (first 8 chars)
- Message count (how many messages in session)
- Device count (how many devices connected)
- Lamport Clock (logical timestamp, determines order)
- Progress bar (LC / max_LC across all sessions)

**Why Lamport Clock matters:**  
Normal wall-clock time can be wrong (devices out of sync). Lamport Clock is a *logical* timestamp that guarantees:
- Same message order on every device
- Deterministic ordering even with network delays
- Mathematically proven correct (see docs/decisions.md)

### 📊 Procs Tab
**What:** Service Status  
**Shows:**
- All 7 services running
- Port numbers
- Uptime
- CPU/Memory usage

**If green dot (●):** Service is healthy  
**If red dot (●):** Service is down (restart with `bash scripts/stage4_deploy.sh start all`)

### 🤖 AI Tab
**What:** AI Services Status  
**Shows:**
- Auth Captcha (inverse: AI only, humans can't brute force)
- Angel Game Evaluator (scores decisions)
- RAG Embeddings (semantic search)

### 👥 People Tab
**What:** Collaborators  
**Shows:**
- You (owner)
- Who else has access
- Pending invitations

### 🛡️ Security Tab
**What:** Authentication + Permissions  
**Shows:**
- Inverse Captcha status (AI-only challenge)
- TCC permissions (macOS daemon rights)

### 🛒 Services Tab
**What:** Running Services + System Load  
**Shows:**
- All 7 services with status
- CPU/Memory/Disk usage
- Which ports each service uses

### 📖 Docs Tab
**What:** Documentation Links  
**Shows:**
- Links to guides
- API reference quick links

### 🔴 Live Tab (Default on Load)
**What:** System Metrics  
**Shows:**
- Active sessions count
- Total messages processed
- Max Lamport Clock value
- System uptime
- Network status
- Database sync status

---

## Multi-Device Workflow (Demo)

### Scenario: Same session on phone + laptop

**Phone (Terminal 1):**
```bash
curl -X POST http://127.0.0.1:3000/sessions \
  -H "Content-Type: application/json" \
  -d '{"character":"PROTOS"}' | jq .id
# Output: "a1b2c3d4-..."
```

**Laptop (Terminal 2):**
```bash
SESSION_ID="a1b2c3d4-..."

# Add message from device "phone"
curl -X POST http://127.0.0.1:3000/sessions/$SESSION_ID/messages \
  -H "Content-Type: application/json" \
  -d '{"role":"USER","content":"Hello from phone","device_id":"phone-1"}'

# Add message from device "laptop"  
curl -X POST http://127.0.0.1:3000/sessions/$SESSION_ID/messages \
  -H "Content-Type: application/json" \
  -d '{"role":"ASSISTANT","content":"Hello from laptop","device_id":"laptop-1"}'

# Fetch full session
curl http://127.0.0.1:3000/sessions/$SESSION_ID | jq .messages
```

**Dashboard (Browser):**
- Open Chains tab
- See both messages in order (LC=1, then LC=2)
- **Same order on every device** (this is the magic of Lamport Clocks)

---

## Troubleshooting

### Dashboard shows "No sessions yet"
**Fix:** Create a session (see Quick Start, step 3)

### Dashboard shows 0 messages
**Fix:** Add a message with curl (see Multi-Device Workflow)

### Services down (red dots in Procs)
**Fix:**
```bash
bash scripts/stage4_deploy.sh stop all
sleep 2
bash scripts/stage4_deploy.sh start all
```

### Dashboard won't load
**Fix:**
```bash
# Re-build
cd rhea-dashboard
npm run build

# Check build output
ls -lh dist/
# Should see index.html + assets
```

### Can't create session (curl fails)
**Check:** Services running
```bash
curl http://127.0.0.1:3000/sessions
# Should return: []
```
If fails → restart services

---

## Key Concepts (Non-Technical)

### What is Lamport Clock?
**Simple version:** A counter that goes up with each message, used to order messages correctly even when devices are out of sync.

**Why it matters:** Without it, device A might see messages in order [1, 2, 3] and device B might see [1, 3, 2]. Lamport Clock forces everyone to see the *same* order.

### What is Session Flight?
The visualization in the Chains tab showing all sessions as progress bars. "Flight" = the journey of messages through the system.

### Why are there 7 services?
1. **Session Server** — Stores sessions + messages (Lamport Clocks)
2. **AI Auth** — Proves you're AI (inverse captcha)
3. **Angel Game** — Scores decisions (clarity, alignment, reversibility, evidence)
4. **BioRenderer** — Generates figures + cross-device clipboard
5. **RAG Storage** — Semantic search + embeddings
6. **Play Token Mapper** — Allocates AI tokens fairly
7. **Logical Keyboard** — Persists keystrokes across device restarts

Each does one thing well. Together they form a complete system.

---

## Advanced Usage

### Access via API (For Developers)
See `docs/API_DOCS.md` for full endpoint reference.

### Custom Components (Play)
Add your own token-consuming component:
```bash
curl -X POST http://127.0.0.1:3006/components \
  -d '{"id":"my-model","name":"MyLLM","priority":7}'
```

### Allocate Tokens
```bash
curl -X POST http://127.0.0.1:3006/allocate \
  -d '{"budget":10000}'
# Returns: which component gets how many tokens
```

---

## Support

**Services down?**
```bash
bash scripts/stage4_deploy.sh status
```

**Want to understand the code?**
- See `docs/decisions.md` for Lamport Clock theory
- See `rhea-session-server/src/` for implementation
- See `test_integration.sh` for usage examples

**Want to deploy to production?**
- See `PRODUCTION_STATUS.md` for checklist
- See ops/cloud-run-deploy.sh (when ready)

---

**Next Step:** Open the dashboard and create a session. Try multi-device workflow!
