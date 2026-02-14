# Token Optimization Strategy

> Created: 2026-02-15 | Goal: Minimize token spending while maximizing persistent context

## Current Token Waste Analysis

### What loads every session (~tokens)
| Source | Size | Est. Tokens | Loaded When |
|--------|------|-------------|-------------|
| CLAUDE.md | 2.3KB | ~600 | Always (system prompt) |
| Auto-memory (MEMORY.md) | 0B | 0 | Always (empty — unused!) |
| System prompt + skills list | ~15KB | ~4,000 | Always |
| Entire.io hooks (7 hooks) | 7 calls | ~200 overhead | Every interaction |
| File re-reads (docs, scripts) | 10-50KB/session | 3,000-15,000 | Per task |
| Context compaction | variable | 5,000-20,000 wasted | When window fills |

### Data sitting unused
| Asset | Size | Status |
|-------|------|--------|
| `.entire/chat_extracts.json` | 510KB | Never referenced in sessions |
| `.entire/snapshots/` (45 files) | 288KB | Written but not read back |
| `docs/state_full.md` | ~10KB | Rarely read, append-only log |
| Auto-memory directory | 0B | Completely empty |

---

## Layer 1: FREE Models via Bonsai (instant cost → $0)

**What:** Bonsai routes Claude Code through free frontier models (GPT-5, Claude, Grok, Gemini, Qwen, GLM) in exchange for anonymized usage data.

**Already installed:** `bonsai` v0.3.0 at `/opt/homebrew/bin/bonsai`

**Setup options:**

### Option A: Per-session launch (recommended for testing)
```bash
bonsai start claude
```

### Option B: Project-level config (persistent)
Add to `.claude/settings.local.json`:
```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://go.trybons.ai",
    "ANTHROPIC_AUTH_TOKEN": "<bonsai_api_key>"
  }
}
```

### Option C: Environment variables
```bash
ANTHROPIC_BASE_URL="https://go.trybons.ai" ANTHROPIC_AUTH_TOKEN="<key>" claude
```

**Action required:** Run `bonsai login` to authenticate (GitHub OAuth).

**Trade-off:** Anonymized data collection. Model names hidden (stealth mode). Use for dev/experimental sessions; keep direct Anthropic API for production/sensitive work.

**Token savings:** 100% cost reduction on qualifying sessions.

---

## Layer 2: AI-Optimized Docs via Mintlify (reduce context loading)

**What:** Turn local markdown docs into a searchable, AI-indexed documentation site with:
- `llms.txt` — structured page index for LLM consumption
- `llms-full.txt` — entire docs combined into one file
- `skill.md` — capability summary telling agents what Rhea can do
- **Hosted MCP server** — AI tools search docs on-demand instead of loading everything into context

**Key insight from Mintlify docs:** "MCP servers don't consume context until the AI calls a search tool." This means lazy-loading instead of upfront file reads.

### Setup
```bash
npx mintlify@latest init    # Initialize in docs/
npx mintlify@latest dev     # Preview locally
```

### Create local `llms.txt` (immediate, no Mintlify needed)
```markdown
# Rhea Project

## Core
- [State](docs/state.md): Compact working state (<2KB)
- [Architecture](docs/architecture.md): 3-product design, 8 agents
- [Core Rules](docs/CORE_RULES.md): Governance, invariants, constraints

## Operations
- [Integrations Audit](docs/INTEGRATIONS_AUDIT.md): 93 tools, pass/fail status
- [Decisions](docs/decisions.md): 14 ADRs
- [Upgrade Plan](docs/upgrade_plan_suggestions.md): Tribunal warnings W1-W7

## Code
- [Bridge](src/rhea_bridge.py): 6 providers, 31 models, 4 cost tiers
- [Orchestrator](scripts/rhea_orchestrate.py): 8-agent Chronos Protocol

## Guides
- [User Guide](docs/user_guide.md): Setup and usage
- [NOW](docs/NOW.md): Immediate upgrade schedule
```

**Token savings:** Instead of reading 5-10 full files per session (~10,000 tokens), MCP search returns only relevant snippets (~500 tokens per query). Estimated 80% reduction in context loading.

---

## Layer 3: Maximize Entire.io as Cross-Session Memory

### Current problems
1. **Snapshots written but never read** — 45 snapshots sit unused
2. **Settings discrepancy** — `.entire/settings.json` says `manual-commit`, `.entire/settings.local.json` says `auto-commit`
3. **chat_extracts.json** (510KB) never referenced
4. **No snapshot-to-context pipeline** — snapshots don't feed back into sessions

### Fixes

#### 3a. Fix settings discrepancy
```bash
# Align settings.json with settings.local.json (ADR-014)
echo '{"strategy":"auto-commit","enabled":true,"telemetry":true}' > .entire/settings.json
```

#### 3b. Create snapshot-to-CLAUDE.md pipeline
Add to `scripts/rhea.sh`:
```bash
context)
  # Generate context summary from latest snapshot for CLAUDE.md
  latest=$(ls -t .entire/snapshots/*.json | head -1)
  python3 -c "
import json, sys
with open('$latest') as f: d=json.load(f)
print(f'Last snapshot: {d.get(\"label\",\"?\")} @ {d.get(\"ts\",\"?\")}')
print(f'Git: {d.get(\"git_hash\",\"?\")[:7]}')
print(f'Files: {d.get(\"doc_count\",\"?\")} docs, {d.get(\"snapshot_count\",\"?\")} snapshots')
  "
  ;;
```

#### 3c. Prune redundant snapshots
Keep only: latest per label type (BOOT, POST_COMMIT, AUTO, etc.)
```bash
# Show duplicate labels
jq -r '.label' .entire/snapshots/*.json | sort | uniq -c | sort -rn
```

### Token savings
- Reading latest snapshot summary vs full state: ~500 vs ~3,000 tokens
- Pruning 45→15 snapshots reduces disk noise and grep confusion

---

## Layer 4: Maximize Auto-Memory (currently empty!)

**Critical gap:** `~/.claude/projects/-Users-sa-rh-1/memory/MEMORY.md` is empty. This file is loaded into EVERY system prompt for free. It's the highest-leverage token saver available.

### Populate MEMORY.md with persistent patterns
```markdown
# Rhea Project Memory

## Key Paths
- State: docs/state.md (<2KB enforced)
- Bridge: src/rhea_bridge.py (6 providers, 4 tiers)
- Check: bash scripts/rhea/check.sh → "OK: checks passed"
- Benchmark: bash scripts/memory_benchmark.sh → 75/78 pass

## Session Bootstrap
1. Read docs/state.md (compact state, <2KB)
2. Run bash scripts/rhea/check.sh (invariant check)
3. Check docs/NOW.md for current priorities

## Patterns
- ALWAYS use scripts/rhea_commit.sh for git commits (ADR-013)
- Default to cheap tier in rhea_bridge.py (ADR-008)
- auto-commit strategy for Entire.io (ADR-014)
- state.md must stay under 2048 bytes (check.sh enforces)
```

**Token savings:** Eliminates redundant file reads at session start. MEMORY.md is "free" context — already in system prompt. Estimated 1,000-2,000 tokens saved per session on orientation reads.

---

## Layer 5: CLAUDE.md Optimization

### Current: 2.3KB, 44 lines — good density
### Optimizations
- Remove lines that duplicate MEMORY.md content
- Add `llms.txt` path reference so agents know to check it first
- Add Bonsai config reference

---

## Implementation Priority

| # | Action | Savings | Effort | Command |
|---|--------|---------|--------|---------|
| 1 | `bonsai login` | 100% cost | 2 min | `bonsai login` → browser OAuth |
| 2 | Populate MEMORY.md | ~2K tokens/session | 5 min | Write to auto-memory |
| 3 | Create local `llms.txt` | ~5K tokens/session | 10 min | Write file |
| 4 | Fix .entire/settings.json | Eliminates benchmark confusion | 1 min | Overwrite file |
| 5 | Install Mintlify CLI | MCP server for docs | 10 min | `npx mintlify@latest init` |
| 6 | Snapshot pruning script | Reduce disk/grep noise | 15 min | Add to rhea.sh |
| 7 | Create `skill.md` | Agent capability summary | 15 min | Write file |

## Cost Model

| Scenario | Tokens/Session | Cost/Session | Monthly (30 sessions) |
|----------|---------------|--------------|----------------------|
| **Current** | ~50K | ~$0.50 | ~$15 |
| **With MEMORY.md + llms.txt** | ~35K | ~$0.35 | ~$10.50 |
| **With Bonsai (free models)** | ~50K | $0.00 | $0.00 |
| **Full optimization** | ~25K | $0.00 | $0.00 |
