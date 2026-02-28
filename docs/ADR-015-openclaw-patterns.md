# ADR-015: Adopt OpenClaw Patterns for Autonomous Agent Evolution (2026-02-28)

**Context:** OpenClaw (216K GitHub stars, MIT) proves that two abstractions —
Autonomous Invocation + Persistent State — are sufficient for full agent autonomy.
Rhea already has elements of both but lacks critical glue: hybrid memory search,
sticky context, heartbeat daemon, skill self-authoring, and channel adapters.

**Decision:** Adopt 5 high-ROI patterns from OpenClaw, adapted to Rhea's Python/FastAPI stack.

## Pattern 1 — Sticky Context Slots (~500 tokens, survive compaction)
**What:** Critical constraints re-injected every LLM turn, immune to context compression.
**Why:** OpenClaw's "Summer Yue incident" showed agents lose safety rails after long sessions.
**Implementation:** `prompts/STICKY_CONTEXT.md` loaded by rhea_bridge.py into every system prompt.
**Contains:** state.md size limit, push mandate, no-questions rule, tribunal triggers.
**Rhea equivalent:** We already have CLAUDE.md + MEMORY.md as auto-context, but they can be
compacted. Sticky slots guarantee ~500 tokens are NEVER compacted.

## Pattern 2 — Heartbeat Daemon with Smart Suppression
**What:** Periodic health check that returns HEARTBEAT_OK (silent) or escalates.
**Why:** Agents are currently reactive — no proactive monitoring between sessions.
**Implementation:** `scripts/rhea_heartbeat.py` + `HEARTBEAT.md` checklist + launchd plist.
**Checks:** state.md size, git push recency, unread relay messages, bridge health, task queue.
**Suppression:** Only P0/P1 issues trigger notification. P2/P3 batched to daily capsule.

## Pattern 3 — Hybrid Memory Search (SQLite + FTS5 + Vectors)
**What:** Index all memory files into SQLite for semantic + keyword search.
**Why:** Current memory is read-only files — no search, no ranking, no decay.
**Implementation:** `src/memory_index.py` + sqlite-vec + FTS5 over memory/*.md, outbox/*.md.
**API:** `/memory/search?q=...&agent=rex&limit=10` in tribunal_api.py.
**Temporal decay:** 30-day half-life. Evergreen files (MEMORY.md) skip decay.

## Pattern 4 — Skill Self-Authoring with Hot-Reload
**What:** Agents create new skills/ folders with SKILL.md at runtime.
**Why:** Current .claude/agents/ are static — no runtime evolution.
**Implementation:** `skills/` directory, YAML frontmatter format, file watcher for reload.
**Two-tier:** Protected (tribunal-gated) vs Self-Modifiable (skills/, no gate).
**Audit:** Every self-authored skill committed + logged to state_full.md.

## Pattern 5 — Channel Adapter Layer
**What:** UnifiedMessage format + adapter classes for each communication channel.
**Why:** Adding Telegram/WebSocket/new channel currently requires ad-hoc wiring.
**Implementation:** `src/adapters/` directory with base class + relay/api/websocket adapters.
**Message schema:** `{text, sender, channel, media, reply_to, metadata, urgency}`.
**Router:** Incoming → normalize → route by agent → denormalize → deliver.

## Implementation Priority
1. Sticky Context (2h) — highest safety ROI, prevents constraint loss
2. Heartbeat (4h) — enables 24/7 monitoring
3. Skill system (6h) — runtime evolution
4. Memory search (8h) — semantic retrieval
5. Channel adapters (8h) — multi-interface support

**Rationale:** OpenClaw validates local-first, file-based, single-process architecture — which
is exactly what Rhea already uses. The patterns above fill specific gaps without architectural
refactoring. Each can be implemented independently.

**Status:** Accepted. Implementation begins with Sticky Context.
