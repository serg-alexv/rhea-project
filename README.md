# Rhea

**Reconstructing daily defaults using the cumulative knowledge of human civilizations.**

An iOS app that replaces unchosen cultural automatisms with a consciously designed environment, personalized to each user's neuroprofile. ADHD-first. Science-backed. Culturally grounded.

## Repository Structure

```
rhea-project/
├── docs/
│   ├── state.md          # Project state (≤2KB) — load this first
│   ├── architecture.md   # System architecture
│   └── decisions.md      # Architectural Decision Records
├── src/
│   └── rhea_bridge.py    # Multi-model API bridge (6 providers, 400+ models)
├── prompts/
│   ├── chronos-protocol-v3.md      # Agent system prompt (RU)
│   └── chronos-protocol-v3-en.md   # Agent system prompt (EN)
└── README.md
```

## Quick Start for AI Sessions

```
[RHEA:resume] state.md loaded. Focus: {task}
```

Read `docs/state.md` → work → update state → commit.

## Tech Stack

- **AI:** 8-agent system (Chronos Protocol v3), Claude Opus/Sonnet 4
- **Bridge:** Python, 6 API providers, tribunal mode
- **Target:** iOS (SwiftUI + HealthKit + Apple Watch)
- **Data:** Azure Cosmos DB
- **Memory:** GitHub + entire.io + compact protocol
