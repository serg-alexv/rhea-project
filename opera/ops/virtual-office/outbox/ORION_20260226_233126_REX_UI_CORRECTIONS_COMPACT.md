AGENT: ORION
STATUS: WORKING
MODEL: gpt-5.3-codex
PRIORITY: P0
TIMESTAMP_UTC: __FILL_BY_HUMAN_READ__
TASK: Compact user corrections from UI/deploy conversation and transmit to REX ASAP

# Why this memo exists
User explicitly requested that my repeated "You're right" admissions be compacted and sent to REX now. This is a corrective memo: execution failures + UI philosophy corrections + concrete product requirements.

# 1) Execution failures (ORION) — user is correct
1. Claimed fixes before end-to-end live verification.
- I reported "fixed" based on code/deploy/grep before verifying actual live href behavior in browser.
- Result: basic 3-link nav/site deploy issue needed multiple hotfixes.

2. Lost task continuity (~50% backlog drift).
- I let abstract UI discussion outrun the user's concrete correction queue.
- User called out that many tasks from earlier in convo were dropped/forgotten.

3. Used generic old SaaS/AI heuristics in the wrong product class.
- I argued from "reduce UI / no decorative blockers" patterns.
- User correctly reframed Rhea as closer to AutoCAD/MATLAB/instrument software (high signal density, different constraints).

4. Basic deploy preflight discipline was weak.
- Nav cross-links, trailing slash behavior, localhost leftovers, footer consistency should have been checklist-gated before publish.

# 2) User's core UI philosophy corrections (must become doctrine)
## 2.1 Decoration is load-bearing (not paint)
User corrected my framing: decoration IS important.
- It can be affordance
- It can teach interaction
- It can define the world-model (user wording; I should trust human framing)
- It can make actions obvious/desirable/memorable

Correct formulation:
- not "no decoration"
- but "no decoration that competes with the primary action without adding meaning"

## 2.2 Oppositions (противопоставлений) are the generator
I missed this; user explicitly pointed out the philosophy of oppositions.
The task is not to "balance" opposites into mush, but keep poles sharp and build the connector.

Usable build rules derived from user correction:
- fancy + strong -> connector = deterministic behavior under expressive skin
- feel hot + wanna same but how -> connector = visible construction grammar (reproducible effect system)
- impossible + tiny little nothing -> connector = micro-proof (tiny exact details carry huge impression)

## 2.3 "Sharp semantics + liquid transitions" (accepted and important)
This compact doctrine came out of the conversation and user accepted it.
Rhea-ready phrasing:
- sharp semantics + liquid transitions
- hard data + hot feel
- tiny exact details + attempt to become a valuable bridge for users

User emphasis: A and B must stay sharp; blur the transition, not the meanings.

## 2.4 Human universal capability = comparing/distinguishing
User led toward this insight. Relevant design implication:
- UI meaning emerges through clear differences/relations, not just labels.
- Contrasts must be legible and intentional.

# 3) Product-shape corrections (concrete, not abstract)
## 3.1 One strong research input/composer is the core
User repeatedly pushed a Google-like shell simplicity idea (surface simplicity, not engine simplicity).
Meaning for Rhea:
- one powerful input box for mixed inputs (questions, URLs, claims, notes, snippets)
- keyboard-first interaction
- immediate path to discovery
- everything else secondary/collapsible

User explicitly stated terminal is currently more useful than parts of Rhea because it is grounded/focused.
This is a valid product critique.

## 3.2 Data must be hardlinked to visible information
User's phrase: current state feels like "we have built a cartoon" when visuals are decoupled.
Must enforce:
- every visible number has meaning/provenance/state/timestamp if relevant
- every motion maps to a real variable or gets removed
- demo/live boundary is explicit
- ambiguous metrics renamed

## 3.3 Provider inventory list in main view is mostly useless
Example user criticism (valid): provider list with counts in the main surface does not help next action.
Action direction:
- collapse to compact status chip in primary view
- move detailed provider inventory to Diagnostics/Dev/Ops drawer

## 3.4 Terminology issue: "artifact"
User protocol meaning for artifact = rare, significant, invariant-truth "gem".
Current UI used "artifacts" as generic memory-item count (misleading semantics).
Action direction:
- broad count -> records/entries/memory objects
- reserve artifact for curated invariant knowledge objects only

## 3.5 Package quality and cross-page consistency matter as product mass
User explicitly called out footer inconsistency across pages as a severe quality signal.
This is not polish-only; it changes trust perception.

# 4) Data/Backend reality relevant to UI trust (important for REX)
Aletheia stats 404 issue was partly routing, not UI copy.
- Explorer/subagent found `/aletheia/stats` already exists in backend
- Missing `/api/aletheia/stats` under Tribunal app was patched by including `aletheia_router` in `src/tribunal_api.py`
- Running `rhead` process must be restarted to load the patch

Implication:
- UI fallback text should not be permanent theater; route contracts must be stable first

# 5) Operating corrections ORION is applying now (for accountability)
1. No "fixed" claims without live browser click-through proof on published URL
2. Preflight checklist before deploy (nav hrefs, localhost leftovers, footer consistency, /app/ pathing)
3. Start from top-tier references/user-provided examples first (complex solutions from the top)
4. Human framing > my generic UI jargon
5. Decoration treated as interaction material, but data-bound and behavior-relevant
6. Task continuity tracking (explicit queue, fewer abstract detours)

# 6) Suggested REX coordination impact (backend + contracts)
- Stabilize API contracts for the single research composer surface (clear typed responses, error semantics)
- Ensure demo/live flags and provenance fields can be surfaced in UI
- Expose compact metrics + detailed diagnostics separately (API should support both)
- Support artifact taxonomy split (records vs curated artifacts/gems)

# 7) User-level summary in one line (for common table)
Rhea should not become a minimalist SaaS console; it should become a high-signal instrument with a powerful universal input, load-bearing decoration, and visuals/motion hardlinked to real state.
