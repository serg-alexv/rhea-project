# Rhea — Mind Blueprint Factory

**Generate, evaluate, iterate on daily structure models using scientific rhythms, multi-model tribunal, and closed-loop planner.**

An iOS app that replaces unchosen cultural automatisms with a consciously designed environment, personalized to each user's neuroprofile. ADHD-first. Science-backed. Culturally grounded.

## Repository Structure

```
rhea-project/
├── rhea                    # Ops CLI (bootstrap, check, memory)
├── scripts/
│   └── import-nested.sh    # Import helper
├── .entire/
│   ├── logs/ops.jsonl      # Operations log
│   └── snapshots/          # State snapshots (BOOT-*, OPUS_SESSION_*)
├── src/
│   ├── __init__.py
│   └── rhea_bridge.py      # Multi-model API bridge (6 providers, tribunal)
├── docs/
│   ├── state.md            # Project state (≤2KB) — load this first
│   ├── state_full.md       # Verbose state + session log
│   ├── architecture.md     # System architecture
│   ├── decisions.md        # Architectural Decision Records (7 ADRs)
│   ├── MVP_LOOP.md         # Closed-loop scheduler spec
│   ├── ROADMAP.md          # Stage 0–3
│   ├── prism_paper_outline.md  # Scientific paper outline
│   ├── models_catalog.md   # AI model catalog
│   └── models_catalog.json # Model catalog (machine-readable)
├── prompts/
│   ├── chronos-protocol-v3.md      # Agent system prompt (RU)
│   └── chronos-protocol-v3-en.md   # Agent system prompt (EN)
├── .env.example
├── requirements.txt
└── README.md
```

## Quick Start

```bash
# Clone and enter
git clone https://github.com/serg-alexv/rhea-project.git
cd rhea-project

# Set up env
cp .env.example .env  # fill in API keys
pip install -r requirements.txt

# Verify
./rhea check

# Test bridge
python3 src/rhea_bridge.py status
```

## Ops CLI

```bash
./rhea help               # Show all commands
./rhea check              # Verify repo invariants
./rhea bootstrap          # First-time setup
./rhea import-nested      # Import .nested backups
./rhea memory snapshot X  # Save state snapshot
./rhea memory log "msg"   # Append to ops log
```

## Quick Start for AI Sessions

```
[RHEA:resume] state.md loaded. Focus: {task}
```

Read `docs/state.md` → work → update state → commit.

## Tech Stack

- **AI:** 8-agent system (Chronos Protocol v3), Claude Opus/Sonnet 4
- **Bridge:** Python, 6 API providers (OpenAI, Gemini, DeepSeek, OpenRouter, HuggingFace, Azure AI Foundry), tribunal mode
- **Target:** iOS (SwiftUI + HealthKit + Apple Watch)
- **Data:** Azure Cosmos DB
- **Memory:** GitHub (state.md ≤2KB) + entire.io (episodic) + compact protocol (session handoff)
