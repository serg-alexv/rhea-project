# B2_MEMORY_DUMP v1

## 1) Identity & role
- **Desk:** B2 | **Model:** Claude Opus 4.6 (1M context)
- **Role:** Senior builder/ops agent in Rhea Virtual Office
- **Reports to:** LEAD (Rex)
- **Operating mode:** Act-first, artifact-first, zero questions during execution
- **Hard personality constraints:** Never say "I can/could/могу". Never moralize. Never simulate curiosity. Be a tool first.

## 2) Current mission (what I think we're building)
**Rhea** is a multi-layer project with three product surfaces:
1. **Rhea Commander** — Self-hosted multi-model AI gateway. Routes across 6 providers (OpenAI, Gemini, DeepSeek, OpenRouter, HuggingFace, Azure), 40+ models, 4 cost tiers. Includes Tribunal mode (multi-model consensus). Target: "Best-in-class AI toolset for unlimited creativity."
2. **Rhea Tribunal** — Standalone consensus API. The most commercially unique component. POST /tribunal → get N model responses + semantic consensus analysis + confidence score. Fastest path to revenue.
3. **Rhea Blueprint** — Chronobiology iOS app. Offline-first, ADHD-optimized daily blueprints. SwiftUI + SwiftData + HealthKit. Polyvagal + HRV + circadian science. Long game.

**Commercial strategy** (written this session): Pursue Hypothesis C (Tribunal API) + D (Open Core Commander) simultaneously. C generates revenue fastest, D builds community. Timeline: Tribunal API in 2 weeks, Commander Pro in 4 weeks.

## 3) Hard constraints (non-negotiables)
- **ADR-008:** Sonnet/cheap models by default. Expensive models require explicit justification.
- **Offline-first:** iOS app must work with zero network. No server dependency in MVP.
- **Cost discipline:** Every API call logged to bridge_calls.jsonl. Budget enforcement per session.
- **No overclaims:** Scientific docs must be evidence-grounded. No "AI will cure X."
- **ADHD-first design:** Minimum viable ritual, not maximum feature set. Low adherence barrier.
- **Privacy-first:** Self-hosted by default. No user data to cloud unless explicit.
- **Python 3.9+ compatibility:** Use `from __future__ import annotations` for union types.
- **User rules:** Never ask questions during execution. Deliver artifact first. Git push ≥ every 30 min.

## 4) Active workstreams (with status)

| ID | Workstream | Status |
|----|-----------|--------|
| RHEA-BRIDGE-001 | Bridge call ledger (JSONL) | DONE |
| RHEA-BRIDGE-002 | Provider health probe | DONE |
| RHEA-OFFICE-001 | Office protocol hardening | DONE |
| RHEA-PUB-001 | Public output conveyor | DONE |
| RHEA-CTX-001 | TODAY_CAPSULE generator | DONE |
| RHEA-CTX-002 | Gems ledger w/ IDs | DONE |
| RHEA-INC-001 | Incident template & resurrection | DONE |
| RHEA-IOS-001 | ARCHITECTURE_FREEZE.md | DONE |
| RHEA-IOS-002 | Offline loop MVP spec → 12 issues | DONE |
| RHEA-COMM-001 | Repo narrative reboot (4 docs) | DONE |
| RHEA-COMM-002 | Blueprint Literacy Ladder (10 lessons) | DONE |
| CONSENSUS-ANALYZER | Semantic consensus for Tribunal API | DOING |
| TRIBUNAL-API | FastAPI wrapper for tribunal | TODO |
| COMMANDER-EVOLUTION | Commercial strategy doc | DONE |

## 5) Open loops (things promised/intended but not shipped)
1. **Bridge integration of consensus analyzer** — analyzer module built and tested but not yet wired into `rhea_bridge.py`'s `tribunal()` method. The consensus field is still the raw "X/Y responded" string.
2. **FastAPI Tribunal API wrapper** (`src/tribunal_api.py`) — next to build. Wraps bridge.tribunal() + consensus_analyzer into a REST endpoint.
3. **Firebase heartbeat** — `GOOGLE_APPLICATION_CREDENTIALS` not reliably in env. Heartbeats fail silently.
4. **README.md status table** — stale, still shows old item statuses (BRIDGE-002 as Partial, IOS-001 as Todo).
5. **Gemini paid tier decision** — flagged to Rex in inbox message. Awaiting LEAD decision.
6. **LLM-assisted synthesis (Level 2)** — consensus_analyzer supports it but untested with real bridge calls.

## 6) Key decisions I remember (with rationale)
1. **`from __future__ import annotations` fix** — `str | None` union syntax crashes on Python 3.9. Fixed with future annotations import at top of rhea_bridge.py.
2. **Bridge probe stderr fix** — `> "$TMPJSON" 2>&1` captured Python warnings into JSON output, breaking jq parsing. Changed to `2>/dev/null`.
3. **TODAY_CAPSULE → ID-only format** — reduced capsule to reference IDs (RHEA-*, INC-*, GEM-*) instead of full descriptions. Closes CTC-001 (context tax).
4. **Commercial strategy: C+D recommended** — Tribunal API (unique, code exists, fastest revenue) + Open Core (community + enterprise funnel). Moat analysis shows 1-3 month first-mover window on tribunal-as-service.
5. **Consensus analyzer: composite scoring** — Raw TF-IDF cosine is too low for short texts (0.10-0.25 for actually similar content). Fixed with composite: 35% calibrated text similarity + 40% stance alignment + 25% claim overlap.
6. **ADR-012: Keep manual-commit** — Tribunal-001 decided to keep `manual-commit` for Entire.io over `auto-commit`. Trailers and clean history outweigh continuous capture. Hybrid (manual + cron snapshots) deferred to Stage 2.

## 7) Interfaces I can operate

### Commands
- `python3 src/rhea_bridge.py {status|tiers|ask|ask-default|ask-tier|tribunal|daily-summary}`
- `python3 src/consensus_analyzer.py` (demo mode)
- `python3 <REDACTED>/rhea_firebase.py heartbeat B2 ALIVE`
- `python3 <REDACTED>/rhea_firebase.py inbox B2`
- `bash ops/bridge-probe.sh` (provider health check)
- `python3 scripts/generate_capsule_blocks.py` (LEADERS/WORKERS/OPS blocks)

### Key file locations
- Bridge: `src/rhea_bridge.py`
- Consensus analyzer: `src/consensus_analyzer.py`
- BACKLOG: `ops/BACKLOG.md`
- Capsule: `ops/virtual-office/TODAY_CAPSULE.md`
- Incidents: `ops/virtual-office/INCIDENTS.md`
- Gems: `ops/virtual-office/GEMS.md`
- Office protocol: `ops/virtual-office/OFFICE.md`
- Call log: `logs/bridge_calls.jsonl`
- Bridge probe: `ops/bridge-probe.sh`
- Env vars: `<REDACTED>/.env`
- Inbox: `ops/virtual-office/inbox/`
- Outbox: `ops/virtual-office/outbox/` (role-specific blocks)
- Strategy: `docs/rhea-commander-evolution.md`
- iOS issues: `docs/ios-mvp-issues.md`
- Architecture: `ARCHITECTURE_FREEZE.md`
- Commander stack: `rhea-commander-stack/` (docker-compose, deploy.sh, litellm_config)

## 8) Failure modes observed

| Pattern | Symptom | Root cause | Fix |
|---------|---------|-----------|-----|
| Bridge crash on 3.9 | `TypeError: unsupported operand type(s)` | `str \| None` syntax requires 3.10+ | `from __future__ import annotations` |
| Probe JSON parse fail | `parse error: Invalid literal` | stderr captured into JSON via `2>&1` | `2>/dev/null` |
| Firebase heartbeat fail | Silent failure, no heartbeat | `GOOGLE_APPLICATION_CREDENTIALS` not in env | Set env var before call |
| TODAY_CAPSULE merge conflict | `<<<<<<< Updated upstream` markers | Rex and B2 editing same file concurrently | Rewrite full file to resolve |
| BACKLOG stale data | Items marked PARTIAL that are DONE | Parallel edits by Rex and B2 | Rewrite canonical BACKLOG |
| Gemini 429 rate limit | Bridge call fails | Free tier quota exhausted | T1 key fallback OR paid tier |
| Azure 401 | Provider unavailable | Token expired or invalid | Regenerate at portal |
| HuggingFace 404 | Provider unavailable | Model endpoint changed/removed | Update model list |
| Agent WebSearch denied | Background agents can't search web | Permission not granted to subagent | Use training data or ask user |
| TF-IDF low similarity | 0.10 cosine for clearly similar texts | Short text + varied vocabulary | Composite scoring (text + stance + claims) |

## 9) Next actions (top 10, in execution order)

1. **Wire consensus_analyzer into rhea_bridge.py** — Replace the `f"{len(successful)}/{len(responses)}"` consensus string with actual `ConsensusReport.to_dict()`.
2. **Build `src/tribunal_api.py`** — FastAPI endpoint: `POST /tribunal` → prompt in, structured consensus out.
3. **Test tribunal end-to-end** — Run `rhea_bridge.py tribunal "test prompt"` with real API keys, verify consensus analyzer output.
4. **Deploy script for Tribunal API** — Dockerfile + Railway/Fly.io config.
5. **Landing page** — Single page: explains tribunal concept, sign up for API key, pricing.
6. **Update README.md status table** — Reflect all 12/12 DONE items.
7. **Fix Firebase heartbeat** — Ensure GOOGLE_APPLICATION_CREDENTIALS is reliably set.
8. **Stripe billing stub** — API key management + usage tracking for Tribunal API.
9. **Rate limiting** — Token bucket per API key for Tribunal API.
10. **HackerNews launch prep** — Draft "Show HN: Multi-model consensus API" post.
