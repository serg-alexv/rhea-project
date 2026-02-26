# Tribunal 002: Rhea Memory Architecture — Fix Entire.io Checkpoint Gap

> **Date:** 2026-02-14
> **Tribunal ID:** TRIBUNAL-002
> **Question:** Why are no Entire.io checkpoints appearing after the first 2, and what is the best architecture for Rhea memory across ALL interaction modes?
> **Models queried:** GPT-4o-mini (OpenAI), Gemini-2.0-flash (Google), Gemini-2.0-flash-lite (Google)
> **Tier:** cheap ($0.00 — free tier models)
> **Total latency:** 14.02s (parallel), 3.18s (follow-up)

---

## Root Cause Diagnosis

**Finding:** Entire.io's `manual-commit` strategy requires an **active agent session** to inject `Entire-Checkpoint` trailers. The session lifecycle is:

```
session-start → user-prompt-submit → [work] → prepare-commit-msg (trailer injection) → git commit → post-commit (condense) → session-stop
```

**Problem:** Commits from Cowork (via `osascript do shell script "git commit..."`) bypass this lifecycle entirely. No `session-start` fires, so `prepare-commit-msg` has no session context → no trailer → no checkpoint on `entire/checkpoints/v1` branch → nothing on entire.io dashboard.

**Evidence from `.entire/logs/entire.log`:**
- Last session with checkpoint: `da10a451` at `2026-02-13T23:58` → produced `b0010aef23e3`
- After that: 4 commits (22b0d97, f97c393, 8a49d0f, 7c4b688) — **zero log entries**, zero trailers
- Session `da10a451` was a Claude Code session, not Cowork

**Timeline:**
| Commit | Source | Trailer? | Checkpoint? |
|--------|--------|----------|-------------|
| 58721f4 | Claude Code | ✅ b0010aef23e3 | ✅ |
| 22b0d97 | Cowork/osascript | ❌ | ❌ |
| f97c393 | Cowork/osascript | ❌ | ❌ |
| 8a49d0f | Cowork/osascript | ❌ | ❌ |
| 7c4b688 | Cowork/osascript | ❌ | ❌ |

---

## Tribunal Responses

### GPT-4o-mini (OpenAI) — 886 tokens, 11.97s
**Position:** Hybrid — wrapper script + cron-based snapshots

Key arguments:
- Auto-commit risks cluttering with unfiltered data and less control
- Wrapper script addresses core problem directly, provides consistent interface
- Cron snapshots as fallback for missed checkpoints
- Abandoning Entire.io loses specialized features (dashboard, search)
- Recommended: wrapper script + strategic cron, abandon pure cron-only approach

### Gemini-2.0-flash (Google) — 2208 tokens, 14.02s
**Position:** Mandatory wrapper script + git hook enforcement

Key arguments:
- Create `rhea-commit.sh` that calls `entire hooks git session-start` before and `session-stop` after every commit
- Use `pre-commit` hook to enforce wrapper usage (reject non-wrapper commits)
- Strategic auto-commit only for specific critical directories
- Abandon cron snapshots as redundant — wrapper is sufficient
- Detailed implementation plan with error handling

### Gemini-2.0-flash-lite (Google) — 298 tokens, 3.18s
**Position:** Wrapper script, clear and decisive

Key arguments:
- Preserves Entire.io's core value (session tracking)
- Maintains commit control — you decide when checkpoints happen
- Auto-commit too risky (clogs repo with noise)
- Abandoning Entire.io is drastic when simple fix exists

---

## Consensus

**Unanimous (3/3):** Create a wrapper script (`scripts/rhea_commit.sh`) that explicitly triggers Entire.io session hooks around every commit.

**Agreement score:** 0.95 — Strongest consensus in any Rhea tribunal.

**Disagreements (minor):**
- GPT-4o-mini wants cron snapshots as backup; Gemini-2.0-flash says they're redundant
- Gemini-2.0-flash wants pre-commit hook enforcement; others don't mention it

---

## Decision: ADR-013

**Context:** Tribunal-002 identified that Cowork commits bypass Entire.io's session lifecycle, causing zero checkpoints for 4+ commits.

**Decision:** Create `scripts/rhea_commit.sh` wrapper that wraps `git commit` with Entire.io hook calls. All Cowork sessions must use this wrapper instead of raw `git commit`.

**Implementation:**
1. `scripts/rhea_commit.sh` — calls `entire hooks git prepare-commit-msg` and `entire hooks git post-commit` around the real commit
2. Update Cowork instructions to always use `rhea_commit.sh` instead of raw `git commit`
3. Add reflection_log entry for this failure

**Rationale:** 3/3 free models agree. Preserves manual-commit benefits (trailers, clean history) while fixing the cross-mode gap. Zero cost, minimal implementation.
