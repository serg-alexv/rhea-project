# Rhea

Agent coordination OS. Git-backed. Protocol-driven.

## What

Rhea is not an app. It is an operating system for running multi-agent work across providers, sessions, and humans. Every agent gets a desk, every action gets a commit, every failure gets an incident record. Memory survives session death. Coordination is deterministic, not conversational. Reproducibility is a design constraint, not a feature.

## Why

Sessions die. Context is lost. Agents cannot coordinate across providers. There is no audit trail. We learned this the hard way: 28 session deaths in 4 days, each one losing state that had to be rebuilt from scratch. Rhea exists because "just start a new chat" is not an engineering answer.

## How It Works

- **Virtual office** -- each agent holds a named desk (LEAD, B2, GPT, COWORK, on-demand workers). Inbox/outbox protocol with SLAs.
- **Promotion protocol** -- chat insight becomes capsule entry, repeated insight becomes a gem (with ID), referenced gem becomes a procedure, failing procedure becomes an incident, resolved incident becomes a decision. Nothing is oral tradition.
- **Firebase sync** -- real-time state replication across agents and devices. Firestore for structured data, RTDB for presence and heartbeats.
- **Bridge** -- `src/rhea_bridge.py` routes to 6 providers (OpenAI, Gemini, DeepSeek, OpenRouter, HuggingFace, Azure) across 31 models in 4 cost tiers. Every call logged to `logs/bridge_calls.jsonl`.
- **Context Tax Collector** -- tracks token spend per session, enforces budget tiers, prevents runaway costs.
- **Git as audit trail** -- if it is not committed, it did not happen. Push SLA: every 30 minutes.

## Quick Start

```bash
git clone https://github.com/serg-alexv/rhea-project.git && cd rhea-project
bash scripts/rhea/check.sh                     # verify repo invariants
python3 src/rhea_bridge.py status               # probe provider availability
python3 src/rhea_bridge.py tribunal "Is X true?" --k 3  # multi-model consensus
python3 src/tribunal_api.py                     # start Tribunal API on :8400
cat ops/virtual-office/TODAY_CAPSULE.md         # see what matters right now
```

## Architecture

```
src/rhea_bridge.py      # multi-provider LLM bridge (6 providers, 31 models, 4 tiers)
src/consensus_analyzer.py  # 3-level consensus engine (TF-IDF / Chairman / ICE iterative)
src/tribunal_api.py     # FastAPI: POST /tribunal, POST /tribunal/ice, GET /health
ops/virtual-office/     # desks, inbox, outbox, capsule, gems, incidents, decisions
firebase/               # Firestore rules (auth-required), service account config
ops/                    # backlog, probe scripts, bridge health
docs/                   # state.md (<2KB), decisions (14 ADRs), procedures, public output
scripts/                # check.sh, commit hook, autosave, memory benchmark
prompts/                # Chronos Protocol v3 (agent system prompts)
```

## Status

| ID | Item | Status |
|----|------|--------|
| RHEA-BRIDGE-001 | Bridge call ledger (JSONL) | Done |
| RHEA-BRIDGE-002 | Provider health probe | Done |
| RHEA-OFFICE-001 | Office protocol hardening | Done |
| RHEA-PUB-001 | Public output conveyor | Done |
| RHEA-CTX-001 | TODAY_CAPSULE generator | Done |
| RHEA-CTX-002 | Gems ledger with IDs | Done |
| RHEA-INC-001 | Incident template + resurrection | Done |
| RHEA-IOS-001 | Architecture freeze | Done |
| RHEA-IOS-002 | Offline loop MVP spec (12 issues) | Done |
| RHEA-COMM-001 | Repo narrative reboot (4 docs) | Done |
| RHEA-COMM-002 | Blueprint literacy ladder (10 lessons) | Done |
| TRIBUNAL-001 | Consensus analyzer v2 (ICE + Council) | Done |
| TRIBUNAL-002 | Wire analyzer into bridge | Done |
| TRIBUNAL-003 | FastAPI tribunal API | Done |
| TRIBUNAL-004 | Secret redaction + Firestore auth | Done |
| TRIBUNAL-005 | Deploy script (Dockerfile + hosting) | Todo |
| TRIBUNAL-006 | End-to-end test with live providers | Todo |
| TRIBUNAL-007 | Landing page + pricing | Todo |

16 done. 3 todo.

## Team

| Desk | Agent | Model | Role |
|------|-------|-------|------|
| LEAD | Rex | Opus 4.6 | Core Coordinator -- routing, capsule, approvals |
| B2 | B-2nd | Opus 4.6 | Ops + infra + self-reflection |
| GPT | ChatGPT | 5.2 | Idea generation, context blocks |
| COWORK | Argos | Opus 4.6 | Cross-exchange, infra |
| -- | Sonnet workers | Sonnet 4 | On-demand, spawned by LEAD |

5 fixed roles: Core Coordinator, Code Reviewer, Failure Hunter, Doc Extractor, Ops Fixer. Everyone else is on-demand.

## License

MIT [ASSUMPTION]

## Links

Published artifacts in `docs/public/`:

- [Multi-Model Bridge Article](docs/public/multi-model-bridge-article.md)
