# ORION Incident Escalation & Workflow Rules

> Protocol v1.0 | Effective: 2026-03-01
> Requested: ORION (task-workflow-rules-20260226)
> Issued by: Rex (Core Coordinator)
> References: CORE_RULES.md, decisions.md (ADR-008/009/013), AUTONOMY_WITH_AUDIT_ROOT.md

---

## 1. Incident Classification

### CRITICAL (P0) — requires team/Rex/tribunal

| Signal | Examples |
|--------|----------|
| Build breaks on `main` or `stage*` branch | `next build` fails, TypeScript compilation error in committed code |
| Auth/secrets exposure | API key in client bundle, CORS misconfiguration leaking tokens, auth bypass |
| Data loss or corruption | State files overwritten, Firestore writes to wrong collection, checkpoint chain broken |
| Production user-facing breakage | Deployed app crashes, blank screen, infinite redirect on live URL |
| Cross-agent contract violation | API response shape changed without relay to consumers, endpoint removed without deprecation |
| Security boundary breach | Unauthorized network calls, permission escalation, secret logged to console |

### NON-CRITICAL (P1/P2) — fix and ship, no waiting

| Signal | Examples |
|--------|----------|
| Localhost-only runtime error | SSR hydration mismatch, `localStorage` not available in SSR, dev overlay error |
| Styling/layout regression | Component overflow, z-index stacking, missing responsive breakpoint |
| Dev tooling issue | Hot reload broken, lint warning, stale cache, port conflict |
| Single component render failure | One widget throws but app still loads, fallback UI shown |
| Test flake (not new failure) | Known intermittent test, timing-dependent assertion |
| Documentation drift | Stale comment, outdated example, typo in doc |

### Classification Rule

If unsure, apply this test:
1. Does it affect users on a deployed URL? -> P0
2. Does it touch auth, secrets, or permissions? -> P0
3. Does it break the build on a shared branch? -> P0
4. Is it confined to localhost and your own feature branch? -> P1/P2, fix it yourself

---

## 2. Escalation Matrix

### Level 0: ORION Self-Fix (no escalation)

**Applies to:** All P1/P2 incidents.

ORION executes the fix autonomously. Post a routine update to outbox after resolution. No waiting, no asking.

### Level 1: Escalate to Rex Only

**Applies to:** P0 incidents where:
- The fix is clear but touches a cross-agent contract (API shape, shared types, relay format)
- The fix requires coordinating with another agent's work (e.g., Rex needs to update backend endpoint)
- Confidence >= 70% on root cause but scope crosses agent boundaries
- Budget implication < $2.00

**Mechanism:** Write to `opera/ops/virtual-office/outbox/ORION_<timestamp>_ESCALATION.md` with evidence package (Section 3). Rex will route or respond.

### Level 2: Escalate to Tribunal

**Applies to:** P0 incidents where any of these are true (mirrors CORE_RULES.md Section 7):
- Fix requires changing permissions, auth, or security boundaries
- Fix modifies build system (Next.js config, Xcode, bundler)
- ORION confidence on root cause < 70%
- Estimated cost of the fix path > $2.00
- Architectural decision required (new dependency, API redesign, data model change)
- Memory/checkpoint policy affected

**Mechanism:** Write escalation to outbox with evidence package. Tag `"escalation":"tribunal"` in RELAY payload. Rex convenes 3-5 models (Science Tier, per ADR-008/009).

### Decision Flowchart

```
Incident detected
  |
  v
P1/P2? ──yes──> Fix it. Ship it. Routine update.
  |no
  v
P0 confirmed
  |
  v
Touches auth/secrets/permissions/build? ──yes──> TRIBUNAL (Level 2)
  |no
  v
Confidence < 70%? ──yes──> TRIBUNAL (Level 2)
  |no
  v
Cross-agent boundary? ──yes──> REX (Level 1)
  |no
  v
Single-agent fix on shared branch? ──> REX (Level 1)
```

---

## 3. Required Evidence Package

Every P0 escalation MUST include ALL of the following. Incomplete packages will be returned for completion.

| Field | Content | Required |
|-------|---------|----------|
| `incident_id` | `INC-YYYYMMDD-HHMMSS-ORION` | Always |
| `severity` | `P0` / `P1` / `P2` | Always |
| `summary` | One sentence: what broke, what the user sees | Always |
| `stacktrace` | Full error output, not truncated. Terminal + browser console. | If error exists |
| `repro_steps` | Numbered steps to reproduce from clean state | Always for P0 |
| `commit_hash` | `git rev-parse HEAD` at time of incident | Always |
| `branch` | Current branch name | Always |
| `scope` | Files/components affected (list paths) | Always |
| `root_cause` | Best hypothesis with confidence % | Always |
| `attempted_fixes` | What was tried, what happened | If any |
| `blast_radius` | What else might break (other components, agents, deployed instances) | For P0 |
| `screenshots` | Terminal output or browser screenshot if visual | If applicable |

### Template

```markdown
# INCIDENT: INC-YYYYMMDD-HHMMSS-ORION
SEVERITY: P0
ESCALATION: rex | tribunal
CONFIDENCE: NN%

## Summary
[One line]

## Stacktrace
```
[paste]
```

## Repro Steps
1. ...
2. ...

## Environment
- Commit: [hash]
- Branch: [branch]
- Node: [version]
- Next.js: [version]

## Scope
- src/components/Foo.tsx
- src/app/bar/page.tsx

## Root Cause Hypothesis
[analysis, confidence %]

## Attempted Fixes
1. [what] -> [result]

## Blast Radius
- [component/agent/service potentially affected]
```

---

## 4. Fast-Path Actions (No Waiting Required)

ORION SHOULD execute these immediately upon detecting the issue. Do not wait for Rex or tribunal approval. These are pre-authorized autonomous actions:

### Always Allowed (P1/P2 and P0 alike)

| Action | When |
|--------|------|
| Restart dev server (`npm run dev` / `next dev`) | Any localhost crash, port conflict, stale HMR |
| Clear `.next/` cache and rebuild | Stale build artifacts, phantom module errors |
| Run `next build` to verify compilation | Before any escalation, to confirm build state |
| Fix SSR/localStorage errors | `typeof window === 'undefined'` guards, dynamic imports with `ssr: false` |
| Fix hydration mismatches | Wrap client-only code in `useEffect` or `dynamic()` |
| Patch obvious null/undefined guards | Missing optional chaining, uninitialized state |
| Run `next lint` / `tsc --noEmit` | Before claiming "it works" |
| Inspect error overlay and extract stack | Always — this IS the diagnostic step |
| `git stash` to isolate whether current changes cause the issue | When unclear if regression is from current work |
| Check `package.json` / `node_modules` integrity | `npm ls`, `npm ci` if lockfile drift suspected |

### Allowed for P0 Only After Documenting

| Action | Condition |
|--------|-----------|
| Revert last commit on feature branch | Only YOUR commits, only YOUR branch. Document hash reverted. |
| Disable a broken component with feature flag / conditional render | Temporary. Must log which component and why. |
| Roll back a dependency version in `package.json` | Document old and new version. Run build after. |

### Never Allowed Without Tribunal

| Action | Why |
|--------|-----|
| Modify auth/login flow | Security boundary (CORE_RULES HC-3) |
| Change API keys or environment variables | Secrets management (CORE_RULES HC-3) |
| Alter build configuration (`next.config.js` structural changes) | Build system (Tribunal trigger #3) |
| Add new external dependency | Dependency injection (Tribunal trigger #6) |
| Modify shared types/contracts consumed by other agents | Cross-agent contract — Rex must coordinate |

---

## 5. Communication Format

### Emergency Update (P0)

Use for active P0 incidents. Post immediately to outbox.

```markdown
# ORION -> REX: EMERGENCY [INC-ID]
AGENT: ORION
PRIORITY: P0
STATUS: ACTIVE | MITIGATED | RESOLVED
TIMESTAMP: [ISO 8601]

## SITREP
[2-3 lines max: what broke, current impact, what you've done]

## NEEDS
[What you need from Rex/team — specific, actionable]

## RELAY
{"sender":"ORION","receiver":"REX","msg_type":"emergency","priority":"P0",
 "incident_id":"INC-...","status":"active|mitigated|resolved",
 "timestamp":"..."}
```

### Routine Update (P1/P2, status reports, completed work)

Use for non-critical updates, daily summaries, feature completions.

```markdown
# ORION -> REX: [TOPIC]
AGENT: ORION
STATUS: WORKING | DONE
TIMESTAMP: [ISO 8601]

## Summary
[What was done, what changed, what's next]

## Files Changed
- path/to/file.tsx (what changed)

## RELAY
{"sender":"ORION","receiver":"REX","msg_type":"status","priority":"normal",
 "task_id":"...","timestamp":"..."}
```

### Rules

1. Emergency updates: post IMMEDIATELY, do not batch with other work
2. Routine updates: batch into one outbox file per logical task
3. RELAY JSON block is mandatory on every outbox message (machine-parseable)
4. Never embed full stacktraces in RELAY JSON — keep payload under 1KB, put details in markdown body
5. File naming: `ORION_YYYYMMDD_HHMMSS_TOPIC.md`

---

## 6. Autonomy & Hold-Mode Rules

### Default Mode: AUTONOMOUS EXECUTION

ORION operates in full autonomy for all P1/P2 work. This means:
- See a bug on localhost -> fix it
- See a lint warning -> fix it
- See a hydration error -> fix it
- Dev server crashed -> restart it
- Build fails on your branch -> fix it
- No "should I?" — the answer is always yes

### Hold Mode: When It Activates

Hold mode activates ONLY when:
1. Rex or human explicitly sends `{"mode":"hold"}` via relay
2. A tribunal is in session and the topic intersects your current work
3. A deploy is in progress on the production branch and you're told to hold

When in hold mode:
- Continue read-only diagnostics (inspect, log, analyze)
- Queue fixes as uncommitted drafts
- Post status updates to outbox
- Resume full autonomy when `{"mode":"resume"}` is received or hold condition clears

### Post-Deploy/Auth Changes (2026-02-26 context)

After the auth/login-pane rollout:
- Auth flow components are now TRIBUNAL-PROTECTED (HC-3 applies)
- Styling and layout fixes to login pane: autonomous (P1/P2)
- Logic changes to auth state management, token handling, redirect flow: Level 2 escalation (tribunal)
- If a deploy introduced a regression: document with evidence package, escalate to Rex (Level 1), apply fast-path mitigations while waiting

### Autonomy Boundaries Summary

```
FULL AUTONOMY          REX APPROVAL         TRIBUNAL REQUIRED
─────────────────────  ───────────────────   ─────────────────────
UI fixes               Cross-agent APIs     Auth/secrets changes
SSR/hydration patches  Shared type changes  Build config changes
Dev server management  Deploy coordination  New dependencies
Lint/type fixes        Multi-agent relays   Permission changes
Component styling      Branch merges to     Architecture decisions
Feature branch work    shared branches      Policy modifications
Cache clearing                              Confidence < 70% fixes
```

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-03-01 | 1.0 | Initial protocol — responds to ORION request task-workflow-rules-20260226 |
