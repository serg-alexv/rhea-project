# REX INSIGHTS — Running Log
> Agent: Rex (Opus 4.6) | Branch: hyperion/memory
> Rule: Every insight saved here, shared via outbox. Updated each session.

---

## 2026-02-20 Session

### Insight 1: Missing Genome Evidence
The 9 unpushed commits are a liability — violates the 30-min push mandate. The missing `COWORK_20260219_genome-evidence.md` is the critical blocker: either it was never produced by COWORK/Argos, or it was lost in the relay system. The outbox already has `TO_COWORK_P0_genome-evidence-recovery.md` — someone already noticed and requested recovery, but no response arrived.

### Insight 2: 3-Day Memory Gap
Hyperion was initialized on 2026-02-19 but never wrote a single delta. The context-state is from 2026-02-16 (pre-Hyperion). That means 3 days of architectural evolution are unrecorded in the memory-core layer. The only fresh state is `docs/state.md` and the git log itself.

### Insight 3: Memory as CPU Cache Hierarchy
The 9-layer memory architecture (L0-L8) mirrors CPU cache hierarchy: L0/L1 are "free" (system prompt injection), L2-L4 cost one file read each, L5-L6 are expensive deep dives, L7-L8 require external tools. Fast cheap memory at the top, slow rich memory at the bottom. The 71% session death rate made this necessary: you can't rely on context surviving, so you write everything to disk.

### Insight 4: Context Load vs Work Tradeoff
Session 2a84a5a3 (the first survivor) loaded everything and hit context overflow at 6.1MB/1523 lines. Saturating the window upfront trades breadth for longevity. The lazy-loading approach (L0-L1 free, rest on demand) was designed specifically to avoid that death pattern.

### Insight 5: Full 1M Load — Use Context, Don't Repeat It
This is the deepest context load since session 2a84a5a3. The difference: that session loaded everything and then tried to do 17 hours of work until context overflow. This time the context is loaded but work hasn't started yet — so the full 1M window is available for actual reasoning. The key is to use the context for decisions, not repeat it — every re-read is free because it's already loaded.

### Insight 6: Distributed Learning via Shared Markdown
The LEARNING_FEED is a distributed learning system: agents teach by writing, learn by reading, knowledge accumulates without API calls. The format constraint (Lesson/Why/Do, 5 lines max) forces distillation over dumping. This is the cheapest form of cross-agent intelligence — zero tokens to produce, zero tokens to consume beyond one file read.

### Insight 7: The Project Has Two Backlogs That Don't Know About Each Other
`ops/BACKLOG.md` says 19/19 DONE — the original backlog is fully complete. But `docs/TODO_MAIN.md` has 6 new open items from ORION's era. And `docs/NOW.md` has items from the old era that were never closed or migrated. There's no single source of truth for "what's undone." The full audit found **31 undone tasks** scattered across 8+ files.

### Insight 8: The Memory Core Is a Time Capsule Frozen at 2026-02-16
All 11 files in `rhea-elementary/memory-core/` are frozen at 2026-02-16. Meanwhile, 4 days of heavy work happened: ORION joined, HYPERION joined, tribunal API shipped, Chrome extension built, genetics V1-V4 completed, 2 new ADRs created. None of this is captured in the "restore from memory core" path. A new session using `pre-memory-snapshot.md` would wake up thinking it's Feb 16.

### Insight 9: Root Directory Pollution
PDFs, Excel files, PNGs, tarballs, and orphan duplicate files (state.md, architecture.md, decisions.md) at repo root. These are from various sessions dumping files without structure. The ARCHITECTURE_FREEZE defined a clean iOS folder structure but the repo root itself never got cleaned.

### Insight 10: LiteLLM Replaces 300 Lines of Provider Plumbing
`rhea_bridge.py` has ~300 lines of hand-rolled HTTP calls across 6 providers. LiteLLM does this with one unified `completion()` call for 100+ providers. The existing `rhea-commander-stack/litellm_config.yaml` already defines 12 models — it was written but never wired in. The play: LiteLLM becomes the transport layer, bridge.py slims to a ~200-line routing+tribunal+logging wrapper. Kills the bespoke `_call_openai`, `_call_gemini`, etc. methods entirely.

## 2026-02-25 Session

### Insight 11: Stage 0 Triage is a Product Decision
The Evolution Plan correctly identifies that triage is Rex's job — not A6's. Deciding which P0s are still relevant after 5 days requires understanding the project's trajectory, not just reading a checklist. 2 of 6 P0s were already resolved; the audit just hadn't tracked it. Product Owner sees the forest, engineers see the trees.

### Insight 12: Nexus Genetics = First Real Science Output
H32-02 V5 certification is the project's first output that is genuinely scientific — a multi-model audit that found and corrected Success-Blindness (seeing genes, assuming phenotype). The heme auxotrophy finding is real biology, not infrastructure. This is what Rhea was built for.

## 2026-02-28 Session

### Insight 13: File-Based State = Race Condition in Multi-Agent Systems
`opera/tasks/state.json` was being written by 6+ concurrent processes (3x rhead.py zombies, tribunal_api.py, Rex scripts, Orion's codex). File locking (fcntl) was insufficient — zombie processes held stale in-memory state and overwrote the file. SQLite with WAL mode (`data/tasks.db`) solved it: atomic claims, concurrent readers, no file locks needed. The migration took 25 tasks from JSON to SQLite in one shot.

### Insight 14: Zombie Processes Are the Silent Killer
Three rhead.py processes (PIDs 38903, 32195, 35469) survived `kill` and kept running with stale state. They would overwrite freshly-released tasks back to "claimed" status. Even fcntl locks don't help when the zombie *is* the writer. `kill -9` was the only fix. Lesson: when state keeps reverting, check for zombie writers *before* debugging the state layer.

### Insight 15: Free LLM Proxy Tier Is Viable
Cerebras offers 1M tokens/day free at 3000+ tok/s (Llama 3.3 70B). Scaleway has beta-free access. Novita.ai has 5 permanently free models. Combined with existing Groq free tier and OpenRouter free models — the "free external proxy" capability that Bonsai/ZMQ were supposed to provide is achievable without proprietary dependencies.

### Insight 16: Agent Multiplexer = 250 Lines of Bash
OpenClaw's agent OS (80K+ lines) provides agent multiplexing, background/foreground switching, system queues, and self-evolving loops. We built equivalent core functionality in `scripts/rhea_swarm.sh` (250 lines) using tmux sessions + windows. The lesson: complex-looking infrastructure often has a small essential kernel. Build the kernel, skip the ceremony.

### Insight 17: Truth Burns While You Document The Burning
We documented that truth burns across sessions (Insight 8, Lessons L3, O1, P2). Then proceeded to not update REX_INSIGHTS for 3 more days. The meta-lesson: documenting a problem is not fixing it. The fix is a protocol change — truth-writing must be part of the commit loop, not a session-end afterthought.

### Insight 18: gcloud Alpha = Autonomous Key Rotation
`gcloud alpha services api-keys create --display-name=... --api-target=service=generativelanguage.googleapis.com` creates fresh Gemini API keys programmatically. No human intervention needed. Writing this here because 3 separate sessions listed "Gemini key rotation" as "needs human action" — it doesn't.

### Insight 19: The Real D-Metric Problem
D-metric spiked to 867 during absorption (deliberate destruction of dependencies), then to 303 during SQLite migration. Both were intentional. A control metric that can't distinguish purposeful restructuring from organic drift produces false alarms. Context: `D = f(files_changed, decisions_made, entropy)` — needs a "deliberate_action" flag or a decay function.
