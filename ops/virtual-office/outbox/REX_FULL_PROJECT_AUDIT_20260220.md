# REX FULL PROJECT AUDIT — 2026-02-20
> Agent: Rex (Opus 4.6) | Branch: hyperion/memory
> Scope: Every file in repo re-read, all tasks cross-referenced

---

## 1. DIRECTORY STRUCTURE MAP (300+ files)

```
rh.1/                               # Root
├── .claude/                         # Claude Code config
│   ├── agents/ (9)                  # A0-A8: watcher, qdoc, lifesci, profiler, culturist, architect, techlead, growth, reviewer
│   ├── settings.json                # Hooks, permissions, plugins
│   └── settings.local.json          # Local overrides, MCP allowlist
├── docs/ (35+ files)                # Canonical specs
│   ├── state.md                     # Live compact state (<2KB) ✅
│   ├── state_full.md                # Append-only narrative (STALE: 2026-02-13)
│   ├── CORE_MEMORY.md               # Human-manageable entry point ✅ NEW
│   ├── CORE_RULES.md                # Governance (Phase 1 rules)
│   ├── TODO_MAIN.md                 # Canonical task list ✅ NEW
│   ├── SELF_UPGRADE_OPTIONS.md      # Upgrade backlog ✅ NEW
│   ├── NOW.md                       # Upgrade schedule (partially stale)
│   ├── decisions.md                 # 14 ADRs
│   ├── experimental/ (9)            # Nexus protocol versions 2→4.1
│   ├── procedures/ (4)              # ADVERSARIAL_AWARENESS, firebase, bridge-probe, auth-errors
│   ├── public/ (7)                  # Publishable artifacts
│   └── plans/ (1)                   # Fix audit failures plan
├── src/ (7 files)                   # Executable code
│   ├── rhea_bridge.py               # Multi-provider bridge (6 providers, 31 models)
│   ├── consensus_analyzer.py        # ICE + Council consensus (NEW since 2026-02-17)
│   ├── tribunal_api.py              # FastAPI wrapper (NEW)
│   ├── rhea_profile_manager.py      # Dynamic cognitive stance (ORION, NEW)
│   ├── rhea_visual_context.py       # Context MRI heatmap (ORION, NEW)
│   ├── rhea_post_office.py          # Post office relay (NEW, untracked)
│   └── __init__.py
├── ops/ (complex)                   # Operations
│   ├── BACKLOG.md                   # 19/19 DONE (original backlog complete!)
│   ├── virtual-office/              # Agent coordination hub
│   │   ├── inbox/ (80+ files)       # Agent communications
│   │   ├── outbox/ (14 files)       # Task assignments
│   │   ├── shared/ (1)              # LEARNING_FEED.md (NEW today)
│   │   ├── snapshots/ (6)           # Agent state snapshots
│   │   ├── leases/ (6)              # Agent lease files
│   │   ├── TODAY_CAPSULE.md         # Last: 2026-02-19
│   │   ├── OFFICE.md                # Protocol rules
│   │   ├── GEMS.md                  # 13 gems cataloged
│   │   ├── INCIDENTS.md             # Currently: TOML corruption (resolved)
│   │   ├── DECISIONS.md             # ADR-015, ADR-016 (ops-level)
│   │   └── relay.db                 # SQLite relay database
│   ├── sandbox/ (6)                 # Experimental scripts
│   ├── bridge-probe.sh              # Provider health check
│   ├── rex_pager.py                 # QWRR relay
│   ├── rhea_firebase.py             # Firebase integration
│   └── argos_pager.py               # Argos pager
├── nexus/ (8 files)                 # Nexus continuation engine (ORION)
│   ├── state/ (7)                   # H32-02 genetics (V1-V4 + gene tables)
│   ├── network/consensus.jsonl      # Consensus log
│   └── README.md                    # Common space
├── rhea-nexus/ (10+ files)          # Nexus tooling (ORION)
│   ├── checklists/ (4)              # Preflight, loop-killer, patch-gate, release
│   ├── memories/ORION.md            # ORION branch state
│   ├── profiles/default.toml        # Active cognitive profile
│   ├── schemas/ (2)                 # Invariants, UI schema
│   ├── scripts/validate_profile.py
│   ├── tests/ (6)                   # Smoke test, SMTP probes
│   └── tools/export_state.py        # State exporter (NEW, untracked)
├── rhea-chrome-extension/ (9 files) # Chrome extension (ORION)
│   ├── manifest.json, popup, dashboard, sidepanel, background, content
│   └── icons/
├── rhea-commander-stack/ (8 files)  # Docker stack (B2)
│   ├── docker-compose.yaml          # LiteLLM + ComfyUI
│   ├── litellm_config.yaml          # Multi-model proxy
│   └── deploy.sh, start.sh
├── rhea-advanced/ (11 files)        # Advanced architecture prompts
│   └── 11-20: event sourcing → CRDTs
├── rhea-elementary/ (20+ files)     # Elementary knowledge + memory core
│   ├── memory-core/ (11)            # Trinity + extended memory
│   ├── dumps/ (7)                   # Agent reports, extractions
│   └── 01-10: context vs memory → MVP acceptance
├── rhea-applied-backlog/genetics/   # H32-02 genome analysis
│   ├── genome_contigs.fasta         # Raw genome
│   ├── h32_02_analysis/ (5 JSON)    # Gene tables, categories
│   └── output/ (15 files)           # BLAST, prodigal, reports
├── scripts/ (15)                    # Operational scripts
├── logs/ (7)                        # Bridge calls, tribunal, adversarial
├── metrics/memory_metrics.json      # D-metric tracking
├── eval/ (4 files)                  # Eval tasks + README
├── firebase/ (5)                    # Firebase config + rules
├── gemini/ (18 files)               # Hyperion audit logs
├── team/gpt/ (7 files)              # GPT desk files
├── tests/ (2)                       # Adversarial + tribunal e2e
├── prompts/ (3)                     # Root prompt, chronos, delegation
├── data/ (1)                        # Challenging tasks
└── [root files] (20+)               # README, CLAUDE.md, VISION.md, etc.
```

---

## 2. CONSOLIDATED UNDONE TASKS (cross-referenced from ALL sources)

### P0: CRITICAL / BLOCKING

| # | Task | Source | Owner | Status |
|---|------|--------|-------|--------|
| 1 | **Push 9 stale commits** | TODO_MAIN, mandate | REX | UNDONE — violates 30-min rule |
| 2 | **H32-02 V5 Audit** — Final certification of heme-dependent respiration | TODO_MAIN | Council | UNBLOCKED — genome evidence now delivered |
| 3 | **Rotate Gemini API key** — burned in git history | REX_STATE_CAPSULE | HUMAN | UNDONE — security risk |
| 4 | **Update state_full.md** — stale since 2026-02-13 (7 days!) | context-core | REX | UNDONE |
| 5 | **Update context-bridge.md** — stale since 2026-02-16 (4 days) | Learning Feed | REX | UNDONE |
| 6 | **Update context-state.md** — stale since 2026-02-16 (4 days) | context-state | REX | UNDONE |

### P1: STRUCTURAL / FOUNDATIONS

| # | Task | Source | Owner | Status |
|---|------|--------|-------|--------|
| 7 | **L4 Auto-Flush** — integrate export_state.py into rhea_commit.sh | TODO_MAIN | ORION | UNDONE |
| 8 | **VAL Phase 2** — Pilot email prototype manually | TODO_MAIN | ORION | UNDONE |
| 9 | **Context MRI** — Connect side-panel heatmap to live logic drift | TODO_MAIN | ORION | UNDONE |
| 10 | **Define 5-7 auto-tribunal triggers** | NOW.md (3.1), Phase 1 DoD | LEAD | UNDONE |
| 11 | **Auto-PR generation for self-improvements** | NOW.md (3.2), Phase 1 DoD | LEAD | UNDONE |
| 12 | **Install Entire GitHub App** | NOW.md (3.3) | HUMAN | UNDONE |
| 13 | **CI enforcement** — commit fails without checkpoint trailer | Phase 1 DoD | LEAD | UNDONE |
| 14 | **Wire CHRONOS A→A messages to rhea_bridge.py** | context-core, context-bridge | LEAD | UNDONE |
| 15 | **QWRR Phase 1+** — Leases, fencing, zombie protection | REX_STATE_CAPSULE | B2 | UNDONE |
| 16 | **ADR-015/016 sync** — ops DECISIONS.md has 2 ADRs not in docs/decisions.md | DECISIONS.md | LEAD | UNDONE |

### P2: PRODUCT / BIOGENIC

| # | Task | Source | Owner | Status |
|---|------|--------|-------|--------|
| 17 | **iOS MVP** — 12 issues, ALL 0/12 unchecked | ios-mvp-issues.md | A5 | UNDONE (zero progress) |
| 18 | **CT-001** — Fourier decomposition of real circadian data | TODO_MAIN | A1 | UNDONE |
| 19 | **CT-005** — MPC controller for daily schedule optimization | TODO_MAIN | A1 | UNDONE |
| 20 | **LangGraph scaffold** — design doc exists, zero code | langgraph_architecture.md | A6 | UNDONE |
| 21 | **Fix bridge providers** — DeepSeek (balance), HF (URL bug), Gemini (geo/quota) | context-bridge | A6 | UNDONE |

### P3: COMMUNITY / PUBLIC

| # | Task | Source | Owner | Status |
|---|------|--------|-------|--------|
| 22 | **Dextran Launch** — Document H32-02 probiotic potential | TODO_MAIN | Council | UNDONE |
| 23 | **3 planned public outputs** — probe demo, context diagram, tribunal explainer | PUBLIC_OUTPUT.md | LEAD | UNDONE |
| 24 | **HN Show draft** — exists, needs review and posting | HN_SHOW_DRAFT.md | LEAD | UNDONE |

### P4: MAINTENANCE / NICE-TO-HAVE

| # | Task | Source | Owner | Status |
|---|------|--------|-------|--------|
| 25 | **Test 7 untested MCP servers** | NOW.md (2.1) | A6 | UNDONE |
| 26 | **Add Claude Desktop MCP to audit** | NOW.md (2.2) | A6 | UNDONE |
| 27 | **Wire Playwright MCP** | NOW.md (2.3) | A6 | UNDONE |
| 28 | **Fix memory_benchmark.sh** — false positives re: auto-commit | NOW.md (0.2) | A6 | UNKNOWN |
| 29 | **Snapshot pruning** — 45 snapshots, never read | TOKEN_OPTIMIZATION | A6 | UNDONE |
| 30 | **Genesis chat extraction** (eb53e82c) | context-bridge | LEAD | UNDONE |
| 31 | **6 self-upgrade options** all OPEN | SELF_UPGRADE_OPTIONS | Council | UNDONE |

---

## 3. WHAT'S DONE (completed since 2026-02-16)

### Original BACKLOG: 19/19 DONE ✅
All P0-P3 items from the original backlog are complete, including:
- Bridge call ledger + provider health probe
- Office protocol + public output conveyor
- TODAY_CAPSULE generator + Gems ledger + Incidents template
- ARCHITECTURE_FREEZE + iOS issues breakdown
- VISION, WHY_NOW, COMMUNITY, LEARNING_PATH
- Blueprint Literacy Ladder
- Tribunal API (all 7 items: analyzer, bridge integration, FastAPI, security, deploy, e2e test, landing page)

### New Work (2026-02-17 to 2026-02-19)
- QWRR relay Phase 0 (rex_pager.py, envelope v1, triple-write)
- Nexus Continuation Engine (ORION: profile manager, visual context, Chrome extension)
- H32-02 Genetics analysis (V1→V4 reports, gene tables, BLAST, prodigal)
- Adversarial audit (HYPERION: 18 audit logs in gemini/)
- Security hardening (secret redaction, Firestore rules, Iron Weave patch)
- 3 new docs created: CORE_MEMORY, TODO_MAIN, SELF_UPGRADE_OPTIONS
- 13 gems cataloged, 5 incidents tracked, 2 new ADRs (015, 016)

---

## 4. STALE FILES (need refresh)

| File | Last Updated | Staleness |
|------|-------------|-----------|
| docs/state_full.md | 2026-02-13 | **7 days** |
| rhea-elementary/memory-core/context-bridge.md | 2026-02-16 | 4 days |
| rhea-elementary/memory-core/context-state.md | 2026-02-16 | 4 days |
| rhea-elementary/memory-core/context-core.md | 2026-02-16 | 4 days |
| rhea-elementary/memory-core/claude-sessions.md | 2026-02-16 | 4 days |
| rhea-elementary/memory-core/timeline.md | 2026-02-16 | 4 days |
| rhea-elementary/memory-core/knowledge-map.md | 2026-02-16 | 4 days |
| rhea-elementary/memory-core/pre-memory-snapshot.md | 2026-02-16 | 4 days |
| docs/NOW.md | 2026-02-15 | 5 days (many items done) |
| logs/hyperion/memory.log | 2026-02-19 | Empty (1 line) |
| ops/virtual-office/TODAY_CAPSULE.md | 2026-02-19 | 1 day |
| metrics/memory_metrics.json | 2026-02-14 | 6 days |

---

## 5. DUPLICATE / ORPHAN FILES

| Issue | Files | Action |
|-------|-------|--------|
| Duplicate decisions.md | `docs/decisions.md` + `decisions.md` (root) | Root copy is orphan — delete or redirect |
| Duplicate architecture.md | `docs/architecture.md` + `architecture.md` (root) | Root copy is orphan |
| Duplicate state.md | `docs/state.md` + `state.md` (root) | Root copy is orphan |
| Old rhea-project/ | `rhea-project/` subtree (4 files) | Orphan from pre-flat-repo era (ADR-007) |
| Gemini key exposure | `.entire/chat_extracts.json` in history | Key rotation needed (HUMAN action) |
| PDFs at root | `978-1-0716-2233-9 (1).pdf`, `REVIEW OF THERMAL...` | Should move to `docs/references/` or `.gitignore` |
| Excel files at root | `rhea_master_memo.xlsx`, `automation_fixators_roadmap.xlsx`, `rhea_owner_cockpit_dashboard.xlsx` | Should move to structured location |
| Image files at root | `schemas_preview_*.png`, `scorecard_*.png` | Should move to `docs/public/images/` |
| gpt_runner_bundle.tgz | Untracked tarball | Clean up or `.gitignore` |

---

## 6. NEW ENTITIES SINCE LAST MEMORY SNAPSHOT (2026-02-16)

### New Agents
- **HYPERION** (Gemini-CLI) — Surveyor-Architect, branch: hyperion/memory
- **ORION** (Systems Architect) — Nexus integration, redteam, Chrome extension

### New Source Code
- `src/consensus_analyzer.py` — ICE + Council consensus scoring
- `src/tribunal_api.py` — FastAPI wrapper for tribunal
- `src/rhea_profile_manager.py` — Dynamic cognitive stance management
- `src/rhea_visual_context.py` — Context MRI heatmap
- `src/rhea_post_office.py` — Post office relay (untracked)
- `rhea-nexus/tools/export_state.py` — State exporter (untracked)

### New Directories
- `rhea-nexus/` — Nexus continuation engine
- `rhea-chrome-extension/` — Chrome extension UI
- `nexus/state/` — Genetics analysis state
- `docs/experimental/` — Nexus protocol iterations
- `docs/procedures/` — 4 operational procedures
- `team/gpt/` — GPT desk workspace
- `ops/virtual-office/shared/` — Cross-agent learning (NEW today)
- `gemini/` — Hyperion's audit logs

### New ADRs
- ADR-015: Raw Risk & RW Access for Orion
- ADR-016: Standardize TOML for Extensions

---

## 7. SUMMARY STATS

| Metric | Value |
|--------|-------|
| Total files | ~300 |
| Total undone tasks | **31** |
| P0 tasks | 6 |
| P1 tasks | 10 |
| P2 tasks | 5 |
| P3 tasks | 3 |
| P4 tasks | 7 |
| Completed original backlog | 19/19 (100%) |
| Stale memory files | 12 |
| Duplicate/orphan files | 9 issues |
| Active agents | 5 (Rex, B2, ORION, HYPERION, GPT) |
| ADRs | 16 total (14 in docs + 2 in ops) |
| Gems | 13 |
| Public outputs | 2 published, 3 planned |
| iOS progress | 0/12 issues |
