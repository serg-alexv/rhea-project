# NOW — Immediate Upgrade Schedule

> Created: 2026-02-15 | Priority: most fundamental first

## Tier 0: Fix What's Broken (do first, unblocks everything)

### 0.1 Trim `docs/state.md` under 2KB
- **Why:** `check.sh` fails, blocking all verification gates
- **Action:** Compress state.md from 2,270B to ~1,800B (remove detail, link to deeper docs)
- **Time:** 5 min
- **Verify:** `bash scripts/rhea/check.sh` → `OK: checks passed`

### 0.2 Fix `memory_benchmark.sh` false positives
- **Why:** 3/73 checks fail because benchmark expects `manual-commit` but ADR-014 set `auto-commit`
- **Action:** Update lines 170-171, 220-223 to expect `auto-commit`
- **Time:** 5 min
- **Verify:** `bash scripts/memory_benchmark.sh` → 0 failures

### 0.3 Create `rhea` CLI wrapper
- **Why:** Scripts exist but no `rhea` command in PATH — ops friction for every session
- **Action:** Create `scripts/rhea.sh` dispatcher, symlink to `/usr/local/bin/rhea`
- **Time:** 10 min
- **Verify:** `rhea check` → passes

---

## Tier 1: Structural Foundations (enables all future work)

### 1.1 Create `.claude/agents/` — project-level subagents
- **Why:** ROOT prompt mandates agent-driven workflow (A1-A8). No project agents defined yet — every session reinvents delegation from scratch
- **What:**
  - `researcher.md` — read-only codebase exploration, doc analysis
  - `implementer.md` — code changes with verification
  - `reviewer.md` — code review, invariant checking
- **Time:** 20 min
- **Verify:** `Task` tool can spawn with `subagent_type` referencing these agents

### 1.2 Produce `docs/SELF_UPGRADE_OPTIONS.md`
- **Why:** ROOT prompt Section 7 mandates this as Phase 1 deliverable. Missing entirely.
- **What:** Ranked backlog of upgrades with: Goal, Mechanism, Risk, Experiment, Verification, Rollback, Cost. Must cover 7 clusters from ROOT prompt.
- **Sources:**
  - ROOT prompt Section 7 (7 required clusters)
  - `docs/upgrade_plan_suggestions.md` (tribunal warnings W1-W7)
  - Claude Desktop MCP logs (13 additional servers discovered: Control Chrome, Filesystem, Apple Notes, Control Mac, Desktop Commander, Shadcn UI, B12 Website Generator, 10x Genomics Cloud, ToolUniverse)
  - `docs/INTEGRATIONS_AUDIT.md` (7 untested MCP servers)
- **Time:** 45 min
- **Verify:** File exists, covers all 7 clusters, each entry has all required fields

### 1.3 Produce `docs/TODO_MAIN.md`
- **Why:** ROOT prompt Section 9 mandates this. Currently scattered across state.md, upgrade_plan_suggestions.md, multiple ADRs.
- **What:** Single de-duplicated, ranked task list with owners and acceptance tests
- **Time:** 30 min
- **Verify:** No duplicate tasks, every task has owner + acceptance test

### 1.4 Produce `docs/CORE_MEMORY.md`
- **Why:** ROOT prompt Section 9 mandates this as the "single human-manageable memory window"
- **What:** 1 page max core, links to deeper context (state_full, snapshots, ADRs)
- **Time:** 20 min
- **Verify:** Under 1 page, all links resolve

---

## Tier 2: Tooling Expansion (leverage what's already available)

### 2.1 Test 7 untested MCP servers
- **Why:** Audit shows 7 UNTESTED servers. Some may be valuable (Clinical Trials, Hugging Face, Scholar Gateway)
- **Action:** Systematic liveness test with read-only calls
- **Time:** 15 min
- **Verify:** Update `INTEGRATIONS_AUDIT.md` — all rows have PASS/FAIL

### 2.2 Add Claude Desktop MCP servers to audit
- **Why:** Claude Desktop has 13 additional MCP servers not in Claude Code audit (discovered in `~/Library/Logs/Claude/mcp.log`)
- **Servers found:**
  - Control Chrome — browser automation
  - Filesystem — file system MCP
  - Read and Send iMessages — already in audit
  - Read and Write Apple Notes — note-taking
  - Figma — already in audit
  - 10x Genomics Cloud — genomics data
  - Shadcn UI — UI component generation
  - Control your Mac — macOS automation
  - Coupler.io — already in audit
  - ToolUniverse — multi-tool aggregator
  - Desktop Commander (x2) — desktop automation
  - B12 Website Generator — website gen
- **Action:** Add Layer 6 (Claude Desktop Extensions) to INTEGRATIONS_AUDIT.md
- **Time:** 20 min

### 2.3 Wire Playwright MCP for browser automation
- **Why:** ROOT prompt explicitly calls for browser automation. Playwright plugin is installed but untested.
- **Action:** Test `mcp__plugin_playwright_playwright__browser_navigate` and friends
- **Time:** 15 min
- **Verify:** Can navigate to a URL, take screenshot

---

## Tier 3: Process Hardening (Phase 1 "Definition of Done")

### 3.1 Define 5-7 auto-tribunal triggers
- **Why:** Phase 1 DoD requires "auto-tribunal triggers defined"
- **What:** Codify in `docs/CORE_RULES.md` Section 7: memory policy change, checkpoint policy change, permission escalation, build system mod, new MCP server addition, cost tier escalation, self-upgrade implementation
- **Time:** 15 min

### 3.2 Auto-PR generation for self-improvements
- **Why:** Phase 1 DoD requires this capability
- **What:** Script or agent that creates a PR from a branch with upgrade changes
- **Time:** 30 min

### 3.3 Install Entire GitHub App
- **Why:** Blocking checkpoint visibility. W1 priority from upgrade_plan_suggestions.md.
- **Action:** Human action → https://github.com/apps/entire → grant access to serg-alexv/rhea-project
- **Time:** 2 min (human)
- **Verify:** https://entire.io/serg-alexv/rhea-project/checkpoints/main shows data

---

## Execution Order

```
0.1 → 0.2 → 0.3 (fix broken, 20 min)
    ↓
1.1 → 1.2 → 1.3 → 1.4 (foundations, ~2 hours)
    ↓
2.1 → 2.2 → 2.3 (tooling, ~1 hour)
    ↓
3.1 → 3.2 → 3.3 (hardening, ~1 hour)
```

Total estimated: ~4 hours of agent work + 2 min human action (3.3)
