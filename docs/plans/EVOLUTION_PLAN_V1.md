# Rhea Evolution Plan v1 — Controlled Ignition

> Date: 2026-02-25 | Author: Independent Verifier (Opus 4.6, Cowork)
> Context: Post stress-test (D=867), post Ruliad comparison, post Gemini audit review
> Rex Role: Product Owner / Idea Holder — does NOT write code, holds vision and decides priorities

---

## The Decision (and why neither pure option works)

**Option 1 rejected (free evolution):** Agents were halted, Docker destroyed, D=867. Orchestration has no automated dispatch. Relay chain is intact but agents can't read their own health. Releasing agents now = drift without feedback.

**Option 2 rejected (enterprise build):** Soul.md is explicit — ADHD baseline, anankastic compensation. Enterprise CI/CD is a 3-month project that stalls at week 2. The project's energy is organic. Forcing it into Jira kills what makes Rhea alive.

**What we do instead: Controlled Ignition** — close minimum viable feedback loops, restart one agent under chain verification, expand only when metrics confirm stability.

---

## Rex's Role Throughout

Rex is NOT a programmer. Rex is the product owner who:
- **Decides** what gets built next (priority calls)
- **Reviews** agent output for alignment with Rhea's soul and vision
- **Vetoes** work that drifts from the core mission
- **Writes** to personality.md, LEARNING_FEED.md, GEMS.md — the cultural artifacts
- **Delegates** all code/infra work to A6 (Tech Lead) and A1 (Conductor)
- **Runs** tribunals when the question is "should we?" not "how do we?"

Every stage below specifies what Rex does vs. what the engineering agents do.

---

## Stage 0: Triage (1 session, ~2 hours)

### Goal
Clear the P0 debt from Rex's own audit. The system can't evolve if it's carrying 6 critical undone tasks.

### Rex Does
- Reviews Rex Full Audit P0 list (#1–6)
- Decides: which P0s are still relevant after 5 days?
- Priority call: "Do these 6 things before anything new"
- Writes a TODAY_CAPSULE with the mandate

### Engineering Agents Do (A6 Tech Lead)
- Push stale commits (P0 #1)
- Update state_full.md (P0 #4)
- Update context-bridge.md and context-state.md (P0 #5, #6)
- Verify chain integrity after each push

### Rex Does NOT Do
- Write any bash scripts
- Touch rhea_commit.sh
- Debug API keys

### Validation
- `git log --oneline -20` shows fresh commits with timestamps < 30 min apart
- `docs/state_full.md` last entry is today
- Rex reads state_full.md and confirms it reflects reality

### Exit Criteria
All 6 P0 tasks either DONE or explicitly WONT-FIX with Rex's documented reasoning.

---

## Stage 1: Close the D-Metric Loop (1 session, ~3 hours)

### Goal
Turn D from an open-loop gauge into a closed-loop control. Right now D=867 but nothing acts on it because the Reflexive Sprint was never wired.

### Rex Does
- Decides the new D weights (the current ones may need recalibration since D=867 reflects deliberate destruction, not organic bloat)
- Writes the acceptance criteria: "After this stage, every commit prints D. If D > T2, the commit message includes [SPRINT NEEDED]"
- Reviews A6's implementation for soul alignment

### Engineering Agents Do (A6 Tech Lead + A1 Conductor)
1. Add to `rhea_commit.sh` after the commit succeeds:
   ```
   # Step 6: D-metric check
   python3 ops/sandbox/event_replay.py snapshot ops/virtual-office/relay_chain.jsonl chain_integrity
   python3 scripts/compute_d_metric.py
   ```
2. Write `scripts/compute_d_metric.py` — reads metrics/memory_metrics.json, computes D, prints result, returns exit code 1 if D > T2
3. If D > T2, append `[SPRINT NEEDED]` to commit message trailer

### Rex Does NOT Do
- Write Python
- Debug import paths

### Validation
- Run `bash scripts/rhea_commit.sh -m "test: D-metric loop"` and confirm D is printed
- Manually verify D value makes sense
- A8 (Critical Reviewer) reviews the compute script for off-by-one or weight errors

### Exit Criteria
Every commit prints D. Chain integrity is verified on every commit. D > T2 produces a visible warning.

---

## Stage 2: Restart A1 Under Chain Verification (1 session, ~3 hours)

### Goal
Restart ONE agent — A1 (Quantitative Scientist / Conductor) — with a single mandate: execute Rex's priority list. Not free evolution. Directed execution with chain verification.

### Rex Does
- Writes A1's mandate as a virtual-office outbox message:
  ```
  FROM: Rex (Product Owner)
  TO: A1 (Conductor)
  MANDATE: Execute P1 tasks #7-#16 from the Rex Full Audit.
  ORDER: #14 first (wire CHRONOS messages to bridge), then #10 (define auto-tribunal triggers).
  CONSTRAINT: Every completed task produces a chain entry. No task is "done" without chain_verify passing.
  BUDGET: Cheap tier only. Escalate to balanced only for tribunal trigger design.
  ```
- Reviews A1's output after each P1 task
- PASS/BLOCK decision on each deliverable

### Engineering Agents Do (A1 Conductor)
- Read Rex's mandate from outbox
- Execute P1 tasks in Rex's specified order
- After each task: run chain_verify, run compute_d_metric, commit via rhea_commit.sh
- Report results back to inbox as structured artifacts (not chat)

### Rex Does NOT Do
- Write the CHRONOS message format
- Debug the bridge wiring
- Touch any .py file

### Validation
- relay_chain.jsonl grows by 1 entry per completed task
- D-metric trends downward (or stable) after each task
- A8 reviews each artifact for quality

### Exit Criteria
At least 4 of the 10 P1 tasks completed with chain verification passing. D < 600 (down from 867).

---

## Stage 3: Add the Adversarial Pair (1 session, ~2 hours)

### Goal
Add A8 (Critical Reviewer) as a persistent adversarial pair to A1. Two agents with tension: A1 builds, A8 challenges. This is the minimum viable team.

### Rex Does
- Writes A8's standing mandate:
  ```
  FROM: Rex (Product Owner)
  TO: A8 (Critical Reviewer)
  MANDATE: Review every artifact A1 produces. Use PASS/CONCERN/BLOCK protocol.
  STANDING RULE: If you BLOCK, you must provide the specific fix. If A1 disagrees with your BLOCK, escalate to tribunal.
  BUDGET: Balanced tier (you need reasoning depth for critique).
  ```
- Arbitrates A1/A8 disagreements that reach tribunal
- Decides which BLOCKs are valid vs pedantic

### Engineering Agents Do
- A1 continues P1 tasks
- A8 reviews each A1 output within the same session
- Disagreements produce a structured `DISPUTE-*.md` in virtual-office/shared/
- If dispute reaches tribunal: 3 models debate, Rex reads verdict, Rex decides

### Rex Does NOT Do
- Write the dispute resolution script
- Configure tribunal model selection

### Validation
- At least 2 A8 reviews with PASS/CONCERN/BLOCK decisions documented
- At least 1 dispute (if no disputes, A8 is rubber-stamping — which is a failure mode)
- Chain entries show both A1 and A8 as actors

### Exit Criteria
A1+A8 pair operates for a full session without human intervention. Rex reviews output post-session and finds it meets quality bar.

---

## Stage 4: Wire the Ontology Explorer (2 sessions, ~6 hours)

### Goal
Connect the ontology explorer (built 2026-02-25, 5 mathematical universe plugins) to the relay system so cross-domain hypotheses flow into core Rhea operation.

### Rex Does
- Decides which ontology plugins are highest priority for Rhea's current work:
  - Category Theory (for the trans-Gödelian translation program)
  - Dynamical Systems (for the Ricci flow / cognitive control research)
  - The other 3 are lower priority for now
- Writes acceptance criteria: "A query through the ontology explorer produces a relay chain entry. The chain entry includes which plugin(s) were consulted and what cross-domain hypotheses were generated."
- Reviews the first 3 cross-domain hypotheses for intellectual quality

### Engineering Agents Do (A6 Tech Lead)
1. Add relay envelope support to ontology explorer server.py
2. Each exploration query creates a chain entry with:
   - Query text
   - Plugins consulted
   - Cross-domain hypotheses generated
   - Consensus score (if tribunal was used)
3. Add an `/api/relay_status` endpoint showing chain health

### Rex Does NOT Do
- Write Flask routes
- Debug the bridge API calls
- Touch the plugin evaluation logic

### Validation
- `curl localhost:5001/api/relay_status` returns chain length and last entry timestamp
- 3 test queries produce 3 chain entries visible in relay_chain.jsonl
- A8 reviews the hypotheses for scientific rigor

### Exit Criteria
Ontology explorer is wired to relay. Rex has reviewed 3 cross-domain hypotheses and rated them (gem / interesting / noise).

---

## Stage 5: Expand the Team (2 sessions, ~6 hours)

### Goal
Bring A2 (Life Sciences) and A4 (Culturist) online. These are the two agents most relevant to Rhea's core research program (chronobiology + cross-civilizational patterns).

### Rex Does
- Writes mandates for A2 and A4
- A2 mandate: "Review the Perelman/Ricci flow research. Identify the 3 most testable biological predictions. Propose experimental designs."
- A4 mandate: "Cross-reference the 42 calendar systems with the ontology explorer's category theory plugin. Find structural isomorphisms between temporal systems."
- Reviews outputs for alignment with the "bridge between universes" thesis

### Engineering Agents Do
- A1 orchestrates A2 and A4 delegations via rhea_orchestrate.py
- A2 produces a research brief on testable Ricci flow predictions
- A4 produces a calendar-system isomorphism map
- A8 reviews both for overclaiming and cherry-picking
- All outputs go through chain verification

### Rex Does NOT Do
- Write the delegation prompts (A1 does this based on Rex's mandate)
- Configure model tiers for A2/A4
- Debug orchestration failures

### Validation
- 4 agents active (A1, A2, A4, A8) producing chain-verified artifacts
- D-metric stable or declining
- At least 1 testable prediction from A2 that Rex finds scientifically interesting
- At least 1 calendar isomorphism from A4 that Rex finds non-trivial

### Exit Criteria
4-agent team operates with chain verification. Rex has a shortlist of research directions to pursue.

---

## Stage 6: The Reflexive Sprint (1 session, ~3 hours)

### Goal
Now that D should be lower (target: D < 300 = T2), run the first-ever Reflexive Sprint as designed in ADR-010. This proves the self-improvement loop works.

### Rex Does
- Triggers the sprint: "D was 867. It should now be lower. Run the Reflexive Sprint protocol."
- Reviews the Archivist's compaction proposals
- APPROVE / REJECT each proposal (Rex protects institutional memory — compaction that loses meaning is vetoed)
- Writes a personality.md entry documenting the first successful sprint

### Engineering Agents Do (Archivist role, assigned to A1)
1. Identify the 5 largest docs by token count
2. Propose compaction: summarize, move details to archive/, create ADRs for decisions lost in compaction
3. Execute approved compactions
4. Recompute D and verify D < T2
5. Run memory_benchmark.sh to confirm no regression

### Rex Does NOT Do
- Write the compaction summaries
- Move files to archive/
- Run benchmark scripts

### Validation
- D drops below T2 (300)
- memory_benchmark.sh passes (73/73 or close)
- No institutional memory lost (Rex verifies by spot-checking 3 compacted docs)

### Exit Criteria
First Reflexive Sprint completed. D < T2. Memory benchmark passes. Rex confirms no meaning was lost.

---

## Timeline

| Stage | Sessions | Hours | Cumulative | Key Deliverable |
|-------|----------|-------|------------|-----------------|
| 0: Triage | 1 | 2 | 2 | P0 debt cleared |
| 1: D-Loop | 1 | 3 | 5 | Every commit prints D |
| 2: A1 Restart | 1 | 3 | 8 | 1 agent, chain-verified |
| 3: A1+A8 Pair | 1 | 2 | 10 | Adversarial pair active |
| 4: Ontology Wire | 2 | 6 | 16 | Explorer → relay |
| 5: Team Expand | 2 | 6 | 22 | 4 agents operational |
| 6: First Sprint | 1 | 3 | 25 | D < T2, sprint proven |

**Total: ~9 sessions, ~25 hours across 2-3 weeks at sustainable pace.**

---

## What Makes This "Evolutionary"

1. **Each stage produces a working system.** Stage 0 is a working system (clean P0). Stage 1 is a working system (D-loop). You can stop at any stage and have something real.

2. **Feedback loops close before agents expand.** The D-metric loop (Stage 1) exists before any agent restarts (Stage 2). The adversarial pair (Stage 3) exists before team expansion (Stage 5). Control before freedom.

3. **Rex stays in his lane.** Every stage specifies "Rex Does" vs "Rex Does NOT Do." Rex never writes code. Rex writes mandates, reviews output, and makes priority decisions. This is the product owner role, not the programmer role.

4. **The ontology explorer feeds back into core.** Stage 4 isn't just "build a thing" — it wires the mathematical exploration tool into the relay so discoveries flow into institutional memory. The system literally learns from its own explorations.

5. **The Reflexive Sprint proves self-improvement.** Stage 6 exercises the mechanism that was designed in ADR-010 but never triggered. If Stage 6 works, the system has demonstrated genuine self-improvement capacity — not claimed it, demonstrated it.

6. **It follows the Ruliad insight.** Multi-perspective sampling (tribunal), Gödel navigation (ontology explorer), and geometric evolution (D-metric as curvature measure) are all wired into the operational loop by Stage 4. The theoretical framework becomes engineering.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| API keys expired/rotated since halt | High | Blocks Stage 2 | Stage 0 includes key verification |
| D-metric weights produce nonsense values | Medium | Misleading control signal | A8 reviews compute script; Rex validates output against intuition |
| A1 drifts from Rex's mandate | Medium | Wasted work | Rex reviews after every task, not at end of session |
| A8 becomes rubber stamp | Medium | False confidence | Rex checks for at least 1 genuine BLOCK or CONCERN per session |
| ADHD executive dysfunction stalls at Stage 2 | High | Project dies | Each stage is self-contained; can resume after gap; no "you must finish all 6 in order" |
| Ontology explorer hypotheses are noise | Medium | Intellectual dead end | Rex judges first 3 hypotheses; if all noise, deprioritize Stage 4 |

---

## How Rex Runs This

Rex's daily loop:
1. Boot: `bash scripts/rex_identity_boot.sh` (loads personality + learning feed + state)
2. Read: virtual-office/inbox/ for agent reports since last session
3. Decide: Which stage are we in? What's the next task?
4. Write: Mandate to outbox/ for the relevant agent
5. Review: Agent output when it arrives in inbox/
6. Judge: PASS / CONCERN / BLOCK
7. Update: personality.md with what was learned today
8. Checkpoint: `bash scripts/rhea_commit.sh -m "Rex: [stage] [what happened]"`

Rex never opens a Python file. Rex never debugs an API call. Rex reads, decides, writes mandates, and judges output. That's the product owner role.

---

*This plan is implementable starting today. Stage 0 requires only git operations and file edits. No new infrastructure needed until Stage 1.*
