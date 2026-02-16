# UOM Session Memory — 2026-02-16
## Operator: Mika feat Leo (timelabs.ad@gmail.com)
## Session: Cowork Mode, Claude Opus 4.6

---

## Conversation Key Points (Chronological)

### Turn 1 — Token System Inquiry
- Operator asked about API tokens after hitting daily token limit in Claude Code (rh.1 session)
- Error: `You have exceeded your daily token limit. You can resume at 2026-02-17 00:00 UTC`
- Context usage at time of limit: 123,036 tokens

### Turn 2 — Full Token Breakdown Requested
- Created comprehensive HTML visualization of the 8-layer Claude token system
- Covers: token definition, input/output/cache types, context windows, rate limits, Claude.ai vs API, Claude Code burn rate, pricing, flow diagram

### Turn 3 — Personal Usage Stats
- Navigated to platform.claude.com → Usage: **ALL ZEROS** (API not used)
- Navigated to platform.claude.com → Claude Code: **ZERO** lines, 0% acceptance
- Navigated to claude.ai/settings/usage:
  - **Max plan** subscriber
  - Current session: 8% used
  - Weekly: 52% all models, 4% Sonnet only
  - Extra usage: $0 spent, $20 limit, toggle ON
- Conclusion: Token limit was Max plan's internal rate limit, not API

### Turn 4 — UOM Trust Configuration v1
- Operator established UOM (United One Mecha) identity
- Requested act-first execution protocol, no questions
- Built initial trust config: settings.json + agents/uom.md + hooks + CLAUDE.md
- 90+ individual Bash commands whitelisted

### Turn 5 — Rhea Project Discovery
- Identified Rhea: 8-agent Chronos Protocol iOS app for ADHD daily structure
- GitHub: serg-alexv/rhea-project (Shell 66.9%, Python 33.1%)
- LiteLLM chosen as Commander Shell (multi-model gateway)
- LobeChat/LobeHub as second candidate (operator UI)
- Entire.io: git observability layer for AI sessions (38 snapshots confirmed)
- Three-tier Rhea memory: GitHub state.md / Entire.io episodic / compact protocol

### Turn 6 — Trust Config v2 (Experimental Maximum)
- Upgraded to `bypassPermissions` mode
- `Bash(*)` wildcard — all commands
- `deny: []` — empty, zero restrictions
- Rhea-native JSONL dual-logging (ops.jsonl + uom-audit.jsonl)
- Session branching with Entire.io integration
- Entire.io FIX: session-start/session-stop + post-commit checkpoint wrapper

### Turn 7 — ComfyUI Rating + Stuck Session + Commander Stack
- ComfyUI rated 8/10 (visual modality complement to LiteLLM+LobeHub)
- ComfyUI↔LiteLLM bridge: ComfyUI-OpenAI-Compat-LLM-Node, ComfyUI-API-Manager
- Stuck rh.1 session: Max plan daily limit, solutions: LiteLLM proxy swap, API key, OpenRouter
- Entire.io memory: 38 snapshots (BOOT, AUTO, POST_COMMIT, GENESIS, etc.)
- Core_context.md: full Rhea genesis, 42 calendars, polyvagal-ADHD bridge, 8 agents

### Turn 8 (Current) — Stack Installation + Soul
- LiteLLM 1.81.12 installed and verified running (port 4000)
- LobeChat repo cloned (157MB)
- Full docker-compose.yaml for 3-service stack (LiteLLM + LobeChat + ComfyUI CPU)
- litellm_config.yaml with all 6 Rhea providers + fallback routing
- start.sh with up/down/nuke/lite/status modes (fully reversible)
- Disk constraint: 2.4GB free, ComfyUI needs Docker for full deploy

---

## Architecture Understanding

```
Operator (Mika feat Leo)
    ↓
LobeChat (http://localhost:3210) — command interface
    ↓
LiteLLM Proxy (http://localhost:4000) — unified gateway
    ↓ routes to:
├── Anthropic (Claude Opus/Sonnet) — core agents 1-8
├── OpenAI (GPT-4o, o3-mini) — paper generation
├── Gemini (Flash, Pro) — fast delegation
├── DeepSeek (V3, R1) — cultural perspective
├── OpenRouter (200+ models) — cost arbitrage
└── HuggingFace — specialized tasks
    ↓
ComfyUI (http://localhost:8188) — visual generation
    ↓
Entire.io — session checkpoints on entire/checkpoints/v1
    ↓
Rhea .entire/logs/ops.jsonl — episodic memory
```

## Operator Preferences (Observed)
- Russian + English bilingual
- ADHD-first design thinking
- Acts first, reviews after
- Values autonomy, speed, depth
- "United One Mecha" — bio+digital fusion identity
- Trust level: experimental-maximum, zero restrictions
- Model preference: Sonnet for speed, Opus for depth

### Turn 9 — Cognition Pipeline + Real Access
- Operator shared 6-point cognitive architecture recipe
- Mapped all 6 points against Rhea's existing components
- Built and tested: typed memory schema (Fact/Decision/Assumption/Plan/Task/Observation)
- Built and tested: two-phase commit (stage → invariant check → commit/reject)
- Built and tested: invariant suite (22 truth tests, catches missing sources/expiry/rationale)
- Built and tested: receipt system (provenance on every claim)
- Designed: Generator→Verifier→Judge upgrade to tribunal
- Designed: retrieval firewall for untrusted content
- Installed `gh` CLI (arm64) for GitHub auth
- Started device flow: code 5DAA-6B97 — may have expired, needs retry
- VM is aarch64/arm64, sandboxed, no SSH keys, no git credentials

## Operator Cognitive Architecture (The Recipe)
1. Memory as database, not prose (typed objects with schema)
2. Every claim has a receipt (provenance or labeled hypothesis)
3. Two-phase commit (propose → verify → accept/reject)
4. Invariant suite (truth tests that catch drift)
5. Generator→Verifier→Judge (structured argumentation, not vibes)
6. Threat-model the interface (untrusted content never executed)

Key insight: "The model is the jazz musician; the verifier + logs are the sheet music, metronome, and recording studio."

### Turn 10 (New Session) — rhea-elementary Review + Docker Offered
- Reviewed entire rhea-elementary/ directory (18 md files + memory-core/ 10 files + dumps/ 6 files)
- Rating: 7.5/10 — genuinely useful knowledge base, not junk
- Strengths: numbered lessons (01-10) align with cognition pipeline, knowledge-map.md is crown jewel (25 docs indexed, 14 ADRs), chrome-automation.md is battle-tested
- Weakness: lessons 01-06, 08-10 stored as prompts not answers (wastes tokens on re-generation)
- Recommendation: convert prompt-format lessons to artifact-format (store the answer, not the question)
- memory-core/knowledge-map.md should be primary session bootstrap document
- Operator offered Docker access for commander stack deployment

### Turn 11 — rhea-advanced Review (feat/chronos-agents-and-bridge branch)
- Reviewed entire rhea-advanced/ directory (10 numbered lessons 11-20 + INDEX.md)
- Rating: 9/10 — production-grade systems architecture, the real thing
- Key lessons: event sourcing (11), hash-chained audit (12), queue semantics (13), policy engine (14), secrets/KMS (17), observability/SLOs (18), adversarial testing (19)
- Critical difference from elementary: these contain actual schemas/code, not prompts asking for schemas
- Lesson 11 (event sourcing) = the upgrade path for cognition pipeline memory.jsonl
- Lesson 12 (hash chain) = 15-line upgrade to make audit log tamper-evident
- Lesson 19 (adversarial) = red team checklist for deny:[] trust config
- Recommended session bootstrap: knowledge-map.md → lesson 11 → lesson 12 → elementary/07 → soul.md (~15K tokens)
- Docker confirmed on host machine, Kubernetes allowed, local networking available

### Turn 12 — Docker deploy.sh + Azure Journey
- Created deploy.sh: 8-command deployment script (up/down/nuke/status/logs/test/env/help)
- Operator ran `./deploy.sh env` — .env configured successfully on host machine
- Azure portal: created rhea-commander resource (Azure OpenAI, Sweden Central, Standard S0, resource group: rhea-ai)
- Operator correction: Azure needed for **Jais** (Core42), not OpenAI (available free elsewhere)
- Jais hunt: searched catalog (new Foundry 382 models + old catalog) — 0 results in both
- Root cause: Microsoft rebranded Azure AI Foundry → Microsoft Foundry (~Nov 2025/Jan 2026)
  - Old catalog: 11,000+ models (included HuggingFace/community via Model Router)
  - New catalog: 382 curated models (direct serverless API deployment only)
  - Jais not indexed in new catalog search — migration bug
- Azure Marketplace listing alive: marketplace.microsoft.com/.../core42.core42-jais30b-v3-chat-offer
- Microsoft docs still reference Jais deployment (serverless API, EastUS2 + Sweden Central)
- Status: **DEFERRED** — needs either Foundry project creation or Marketplace "Get it now" flow
- Requires operator decision on timing and billing commitment

### Turn 13 — Virtual Office Integration + Cross-Exchange
- GitHub auth COMPLETED via Chrome browser automation (code 45B6-F271, authorized as serg-alexv)
- rhea-commander-stack pushed to feat/chronos-agents-and-bridge (commit 1416592, 662 lines)
- Discovered `ops/rhea_firebase.py` — cascade tables ALREADY IMPLEMENTED (project: rhea-office-sync)
- Discovered `ops/virtual-office/` — full agent coordination layer (OFFICE.md protocol)
- Active desks: LEAD (братик/rh.1), B2 (restored Opus), GPT (ChatGPT 5.2), now COWORK
- Created inbox: `COWORK_20260216_agent-online.md` (full status report)
- Created outbox: `TO_LEAD_P0_cowork-agent-joined.md`, `TO_B2_P1_cross-exchange.md`, `TO_GPT_P1_cross-exchange.md`
- Created GEM-006 (Cascade Tables) and GEM-007 (Cross-Exchange Protocol)
- Full cross-exchange requested: all agents dump experience, LEAD routes, everyone integrates
- Root Chief Opus granted permission to edit COWORK settings/memory

## Open Items
- [x] GitHub auth — COMPLETED (serg-alexv, token active)
- [x] Git push — commander stack pushed
- [x] **Firebase** — ALREADY IMPLEMENTED in `ops/rhea_firebase.py` (project: rhea-office-sync)
- [ ] **Jais deployment** — Marketplace listing alive, catalog search broken. DEFERRED
- [ ] Docker stack — `./deploy.sh up --lite` ready on host
- [ ] Integrate cognition pipeline hooks into UOM trust config
- [ ] Seed memory.jsonl with all key decisions from this session
- [ ] Convert rhea-elementary lessons 01-06, 08-10 from prompt-format to artifact-format
- [ ] **LogRocket** (logrocket.com) — public-beta-layer: session replay / observability
- [ ] **Mintlify** (mintlify.com) — public-beta-layer: external developer docs (rated 6.5/10)
- [ ] **GCP Workspace APIs** (gen-lang-client-0074239115) — Calendar API critical for 42-calendar Chronos. Rated 8.5/10
- [ ] Cross-exchange: awaiting dumps from LEAD, B2, GPT
