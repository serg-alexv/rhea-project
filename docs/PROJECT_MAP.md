# Rhea Project Map
> Auto-generated 2026-02-27. Source of truth for what's where.

## src/ — Core Python + Next.js

### Python Backend
| File | Purpose |
|------|---------|
| rhead.py | FastAPI main server (CORS, Redis, SQLite, static mount) |
| rhea_bridge.py | Multi-model LLM bridge (6 providers, 31 models, 4 tiers) |
| rhea_compress.py | Vision→text image compression for blind LLMs |
| rhea_vision_check.py | Vision-to-text bridge + invariance consensus checker |
| tribunal_api.py | Tribunal consensus API (L1/L2/L3) + Aletheia capture hooks |
| aletheia_api.py | Proof library REST API (submit, search, verify, chain) |
| aletheia_pipeline.py | Proof capture engine (SQLite + markdown artifacts) |
| consensus_analyzer.py | Semantic consensus (TF-IDF local, chairman, ICE rounds) |
| auth_api.py | JWT auth (signup/login/profile, SHA-256) |
| rhea_ingest.py | Document ingestion + RAG pipeline (chunking, embedding, Redis) |
| rhea_bus.py | Redis pub/sub message bus |
| rhea_swarm.py | ZMQ multi-agent orchestrator with SQLite ledger |
| rhea_post_office.py | SMTP/IMAP email bridge for agents |
| rhea_overwatcher.py | Process monitor (health, coherency, repo invariants) |
| rhea_profile_manager.py | TOML profile → LLM constraint injection |
| rhea_visual_context.py | In-memory visual state store for MRI heatmap |
| ui_sync.py | Metrics→Redis sync for Atlas dashboard |

### Next.js Frontend (Atlas)
| Path | Purpose |
|------|---------|
| src/app/ | Next.js pages (layout.tsx, page.tsx) |
| src/components/ | HyperionBar, MnemosyneWhisper |
| src/store/ | useAtlasStore, useWhisperStore |
| src/hooks/ | useDensityAnalysis |
| src/data/ | whispers.ts |

### Dead/Empty
- `src/flows/` — empty placeholder
- `src/plugins/` — empty placeholder
- `src/operators/bonsai_*.py` — Bonsai removed from project

## docs/ — 80+ documents

### Core (read these first)
| File | Purpose |
|------|---------|
| state.md | Current working state (<2KB, enforced) |
| state_full.md | Append-only narrative log |
| CORE_RULES.md | Hard operating constraints |
| CORE_COORDINATOR_DIRECTIVE.md | Rex operating mandate |
| decisions.md | 14 ADRs |
| ARCHITECTURE_FREEZE.md | Locked baseline spec |
| IMPLEMENTATION_SPEC.md | Technical spec (28K) |
| CONTEXT_MAP.md | Component relationship map |

### Operational
| File | Purpose |
|------|---------|
| INTEGRATIONS_AUDIT.md | 93 integrations with liveness |
| KEY_ROTATION.md | Credential rotation playbook |
| TOKEN_OPTIMIZATION.md | Token cost strategy |
| ALETHEIA_GUIDE.md | Aletheia API docs |
| ALETHEIA_ABSORPTION_PLAN.md | 8-phase integration roadmap |
| models_catalog.json | 31 models, 6 providers, costs |

### Public-facing
- `docs/public/` — DEMO_SCRIPT, FAQ, QUICKSTART, HN draft, pitch deck

### Procedures
- `docs/procedures/` — Firebase usage, bridge probe, tribunal audit, adversarial awareness

## scripts/ — CLI & Automation
| File | Purpose |
|------|---------|
| rhea/check.sh | Repo invariant checker |
| rhea_commit.sh | Git commit wrapper (ADR-013) |
| rhea_autosave.sh | Snapshot + commit + push |
| rhea_orchestrate.py | 8-agent Chronos Protocol v3 |
| memory_benchmark.sh | 5-layer memory self-test (73 checks) |
| rhea/rotate_key.sh | Safe credential rotation |
| live_metrics.py | Real-time health dashboard |
| rex_identity_boot.sh | Rex personality init |
| rex_session_end.sh | Auto-save on crash |

## opera/ — Agent Operations
| Path | Purpose |
|------|---------|
| ops/virtual-office/inbox/ | Agent relay inbox |
| ops/virtual-office/outbox/ | Agent outputs |
| ops/virtual-office/shared/ | LEARNING_FEED.md |
| ops/rhea_firebase.py | Firebase relay (13K) |
| ops/rex_pager.py | Rex pager (48K) |
| ops/relay.db | SQLite message state |
| ops/relay_chain.jsonl | Full audit log (824K) |
| logs/firebase_calls.jsonl | Firebase call log |

## deploy/ — Multi-Cloud
| Path | Target |
|------|--------|
| cloudrun/ | Google Cloud Run (backend) |
| firebase/ | Firebase Hosting (frontend) |
| oracle/ | Oracle Always-Free (Redis) |
| vercel/ | Vercel (alt frontend) |
| deploy-all.sh | Master orchestration |

## rhea-atlas/ — Next.js 14 Frontend (Orion)
Live at localhost:3000. Orion (GPT-5.3) owns this.

## friends/ — Knowledge Systems
| Path | Purpose |
|------|---------|
| aletheia/ | Proofs + hypotheses (markdown) |
| ruliad/ | References, methodology, evolution plan |

## data/
- proof.db — Aletheia SQLite
- compress/originals/ — stored image originals

## LOST from backup (was in `rh.1 copy 2/`)
| Original Path | Status |
|---------------|--------|
| gemini/ + gemini/Archive/ | **MISSING** — Gemini conversations |
| team/agents/, team/gpt/, team/users/ | Partially merged into opera/ |
| users/sa/ | **MISSING** — user profile |
| rhea-ontology-explorer/ | **MISSING** — full app with agents/core/plugins |
| rhea-applied-backlog/genetics/ | **MISSING** |
| rhea-chrome-extension/ | Moved to apparatus/extensions/ |
| rhea-elementary/memory-core/ | Moved to apparatus/elementary/ |
| rhea-advanced/emc2/ | Moved to apparatus/advanced/emc2/ |
| nexus/ (channels, network, state) | Moved to apparatus/nexus/ |

## Garbage (safe to delete)
- `plugins/` — 4 empty .gitkeep
- `.rhea/` — empty placeholder
- `.obsidian/` — editor artifact
- `src/flows/`, `src/plugins/` — empty dirs
- `.playwright-mcp/` — stale test infra
