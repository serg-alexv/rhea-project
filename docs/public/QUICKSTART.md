# Quickstart

## Prerequisites
- macOS with Homebrew
- Git, Python 3, Node.js
- Firebase CLI (`brew install firebase-cli`)
- API keys in `.env` (copy from `.env.example`)

## 1. Clone and verify
```bash
git clone git@github.com:serg-alexv/rhea-project.git
cd rhea-project
bash scripts/rhea/check.sh
```
Expected: `OK: checks passed`

## 2. Run bridge probe
```bash
export $(grep -v '^#' .env | xargs)
bash ops/bridge-probe.sh
```
Expected: table showing LIVE/DOWN per provider. At least OpenAI + OpenRouter should be LIVE.

## 3. Firebase setup
```bash
export GOOGLE_APPLICATION_CREDENTIALS=firebase/service-account.json
/usr/bin/python3 ops/rhea_firebase.py heartbeat YOUR_DESK ALIVE
/usr/bin/python3 ops/rhea_firebase.py status
```
Expected: your desk appears with timestamp.

## 4. Office protocol
```bash
# Read the capsule
cat ops/virtual-office/TODAY_CAPSULE.md

# Check your inbox
/usr/bin/python3 ops/rhea_firebase.py inbox YOUR_DESK

# Send a message
/usr/bin/python3 ops/rhea_firebase.py send YOUR_DESK LEAD "reporting in"

# Structured message (P0)
/usr/bin/python3 ops/rhea_firebase.py send YOUR_DESK LEAD '{"job_id":"JOB-001","priority":"P1","task":"description","outputs":["file.md"]}'
```

## 5. Rules
- **No-output-is-failure.** Every session must produce at least 1 artifact.
- **Questions Gate.** No questions mid-flight. Produce outputs first. Max 3 at end. Each costs 1 artifact.
- **Git push every 30 minutes.** Non-negotiable.
- **Commit every minute during active work.** Use `scripts/rhea_commit.sh`.
- **Context Tax Collector.** If you paste the same thing twice, promote it to GEM/PROCEDURE.

## Verify
```bash
bash scripts/rhea/check.sh          # repo health
bash ops/bridge-probe.sh             # provider status
/usr/bin/python3 ops/rhea_firebase.py status  # office status
```

## Rollback
- Firebase down? Fall back to file-based inbox/outbox in `ops/virtual-office/`.
- Bridge down? OpenAI + OpenRouter are the minimum viable pair.
- Session dying? Read `rhea-elementary/memory-core/context-core.md` + `context-state.md` + `context-bridge.md`.
