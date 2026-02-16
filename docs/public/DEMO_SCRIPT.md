# Rhea -- 5-Minute Demo Script

> Purpose: Show a live walkthrough of the Rhea Office OS for agents.
> Duration: 5 minutes. No slides -- terminal only.
> Prerequisites: Firebase credentials configured, bridge .env loaded, at least 2 providers live.

---

## 0:00--0:30 | The Problem

**Narration:** "This is what multi-agent work looks like without coordination."

**Show:**
1. Open a terminal. Run any long-running LLM agent task.
2. Kill the terminal mid-task (Ctrl+C or close window).
3. Open a new terminal. Ask: "What was I working on?"

**Point:** The answer is nothing. Zero memory. Zero continuity. Every session starts from zero.

**Say:** "We lost 28 sessions this way in the first month. Each one destroyed 2 to 20 hours of accumulated context. The problem is not the model -- it is the architecture. Chat is not infrastructure."

---

## 0:30--1:30 | Boot Sequence

**Narration:** "Rhea recovers from any session death in under 30 seconds. Here is how."

**Run:**
```bash
# Step 1: Read the trinity files (context core + state + bridge handoff)
cat docs/state.md
cat ops/virtual-office/TODAY_CAPSULE.md
cat ops/virtual-office/OFFICE.md
```

**Point:** Three files. Under 5KB total. A fresh agent reading only these three answered 6/6 context questions correctly (GEM-002, blind test).

**Run:**
```bash
# Step 2: Probe the bridge -- which providers are alive right now?
export $(grep -v '^#' .env | xargs)
bash ops/bridge-probe.sh
```

**Point:** Table shows LIVE/DOWN for all 6 providers. Error codes categorized (401 = bad creds, 429 = quota, 404 = URL bug). The system knows what is broken before you ask it to do anything.

**Run:**
```bash
# Step 3: Check today's capsule -- what matters right now?
cat ops/virtual-office/TODAY_CAPSULE.md
```

**Point:** "Done today, blockers, next actions, human state. Updated by agents, not by the human. This is the daily standup -- automated."

---

## 1:30--2:30 | Office Protocol

**Narration:** "Agents coordinate through files and Firebase. No custom framework. No message queue. Just git and a database."

**Run:**
```bash
# Send a message from LEAD desk to B2
export GOOGLE_APPLICATION_CREDENTIALS=/Users/sa/rh.1/firebase/service-account.json
/usr/bin/python3 ops/rhea_firebase.py send LEAD B2 "Run bridge probe and report results"
```

**Point:** Sub-second delivery. B2 agent will see this in its next inbox check.

**Run:**
```bash
# Check inbox for any desk
/usr/bin/python3 ops/rhea_firebase.py inbox LEAD
```

**Point:** "Every message has a sender, timestamp, and content. Persisted in Firebase, mirrored to git. If Firebase goes down, the file-based inbox still works."

**Run:**
```bash
# Add a gem -- an insight worth keeping
/usr/bin/python3 ops/rhea_firebase.py gem GEM-DEMO "Demo gems get promoted to procedures when referenced 3 times" "demo" "protocol"
```

**Point:** "Gems are the knowledge capture layer. Not notes -- they have a promotion rule. Referenced 3 times in capsules or decisions, they become a formal Procedure with exact commands, a verify step, and a rollback plan."

---

## 2:30--3:30 | Agent Deployment

**Narration:** "Spawning an agent is not special. It is a function call. The office protocol is what makes the output usable."

**Show (in Claude Code):**
```
Use the Task tool to spawn a sonnet worker:
  Task: "Read ops/virtual-office/INCIDENTS.md and summarize all open incidents with their current status"
  subagent_type: researcher
```

**Point:** The worker reads the shared state. It does not need to be told what the project is -- the office files provide full context.

**Show the result appearing in terminal output.**

**Say:** "The worker produced a structured summary. In production, this goes to inbox/ as a file. LEAD routes it. The worker does not need to know who reads it."

**Run:**
```bash
# Show the office status -- all desks, all heartbeats
/usr/bin/python3 ops/rhea_firebase.py status
```

**Point:** "Four desks alive. Each with a last-seen timestamp. If any desk goes silent for more than the SLA window, it becomes an incident automatically."

---

## 3:30--4:30 | Context Tax Collector

**Narration:** "The most expensive thing in multi-agent work is not compute -- it is context. Every session that re-explains the same thing is paying a tax."

**Run:**
```bash
# Show the gems -- patterns captured from all agents
cat ops/virtual-office/GEMS.md
```

**Point out GEM-001 (Context Tax Collector concept) and GEM-002 (Trinity Memory).**

**Say:** "GEM-001 was an idea from ChatGPT 5.2. GEM-002 was discovered during an Opus session. GEM-006 came from a Cowork agent. Different models, different terminals -- same knowledge base."

**Run:**
```bash
# Show procedures -- gems that graduated
ls docs/procedures/
cat docs/procedures/PROC-001-firebase-usage.md
```

**Point:** "This procedure started as a pattern someone repeated 3 times: how to send a Firebase message. Now it is formalized. Exact commands. Verify step. Rollback plan. Any new agent can execute it without context."

**Say:** "The sweep works like this: scan capsules and inbox for repeated patterns. If something appears twice, it becomes a gem. If a gem is referenced three times, it becomes a procedure. Over a week, the system gets lighter. Repetition triggers abstraction. Abstraction reduces context load."

---

## 4:30--5:00 | Closing

**Narration:** "Everything you just saw was coordinated by agents. I did not route a single message manually."

**Run:**
```bash
# Final status check
/usr/bin/python3 ops/rhea_firebase.py status
cat ops/virtual-office/TODAY_CAPSULE.md
```

**Say:**

"Rhea is not an app. It is a coordination pattern.

- Files in git for persistence.
- Firebase for real-time sync.
- A promotion protocol that turns noise into knowledge.
- A bridge that survives provider outages.

It works today with 4 agents across 4 terminals. It survived 28 session deaths. It recovered context in 30 seconds every time.

What is missing: automated Context Tax Collector, multi-operator validation, and more data. This is a working theory with working code. Not a product announcement.

The repo is open. The procedures are documented. If you want to stress-test it, start with `ops/virtual-office/OFFICE.md`."

---

## Post-Demo Notes

**If asked "what models does it support?":**
6 providers, 31 models, 4 cost tiers. Run `python3 src/rhea_bridge.py tiers` to see them.

**If asked "does it work with [X provider]?":**
The bridge is OpenAI-compatible. Any provider with a chat completions endpoint can be added in under 10 lines.

**If asked "what if Firebase goes down?":**
File-based inbox/outbox works offline. Firebase is the fast path, not the only path. Git is the source of truth.

**If asked "how much does it cost?":**
Default tier is cheap (Sonnet/Flash/mini class). ~80% of calls stay there. Expensive models require explicit justification and are logged. See `docs/cost_guide.md`.
