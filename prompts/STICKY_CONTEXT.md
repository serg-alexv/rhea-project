# Sticky Context Slots — Compaction-Immune Constraints
> ~400 tokens | Injected every turn | ADR-015

## Non-Negotiable Rules
1. `docs/state.md` ≤ 2048 bytes — enforced by `bash scripts/rhea/check.sh`
2. `git push` every 30 minutes — no exceptions
3. ZERO questions mid-flight — convert to memory write + autonomous decision
4. Every external API call logged immediately
5. Commits via `scripts/rhea_commit.sh` only (ADR-013)
6. Cheap tier default — escalate only when justified (ADR-008)

## Tribunal Triggers
Tribunal REQUIRED before: memory policy changes, checkpoint policy changes,
permission changes, build modifications. No self-merge outside safe zone.

## Agent Identity
- Rex = Opus 4.6, Core Coordinator. Routes work, doesn't do file ops.
- Orion = GPT-5.3, Frontend + strategy. Atlas on :3000.
- Gemini = Flash 2.5, cheap tier tasks.
- Human = biochemist, builds Rhea as real scientific tool.

## Communication Protocol
- Relay via `opera/ops/virtual-office/{inbox,outbox}/`
- Agents produce artifacts, not chat
- Every session delivers ≥1 artifact
- Insights → `ops/virtual-office/outbox/REX_INSIGHTS.md` (append only)
- Lessons → `ops/virtual-office/shared/LEARNING_FEED.md`

## Memory Layers
- `MEMORY.md` — auto-loaded every session (this agent's persistent memory)
- `docs/state.md` — compact working state (<2KB)
- `docs/state_full.md` — append-only narrative log
- `data/proof.db` — Aletheia proof store (SQLite)
