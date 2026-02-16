# Rhea — Upgrade Plan & Suggestions
> Session 17 Tribunal Output | 2026-02-14
> Status: DRAFT — unapproved suggestions, requires human decision

## Overview

This document captures warnings, solutions, and next-step recommendations from the Session 17 deep recheck tribunal. Three perspectives analyzed Rhea's trajectory from the origin point ("Давай обсудим преимущества и недостатки григорианского календаря") through 17 sessions of evolution.

---

## 1. Entire.io Dashboard — ROOT CAUSE & FIX

**Issue:** https://entire.io/serg-alexv/rhea-project/checkpoints/main shows nothing.

**Root cause:** The Entire GitHub App is NOT installed on the rhea-project repository. Checkpoints exist on the `entire/checkpoints/v1` branch (confirmed: 2 checkpoints pushed), but the Entire.io dashboard requires the GitHub App to read them.

**Fix (human action required):**
1. Go to https://github.com/apps/entire
2. Click "Install" → grant read-only access to `serg-alexv/rhea-project`
3. After install, checkpoints should appear at https://entire.io/serg-alexv/rhea-project/checkpoints/main

**Additional:** Strategy switched to `auto-commit` (ADR-014). To fully activate via CLI on macOS:
```bash
cd ~/path-to/rhea-project
entire enable --strategy auto-commit --force
```

---

## 2. Entire.io Branches for Memory

**How it works:**
- `entire/checkpoints/v1` — permanent branch, stores checkpoint metadata (JSON), synced to GitHub remote. This is Rhea's episodic memory backbone.
- Shadow branches `entire/<sessionID>-<worktreeID>` — temporary, local only, used during active sessions for `entire rewind --to <checkpoint-id>`. Auto-cleaned after session ends.
- `entire rewind --to <checkpoint-id>` — restores repo to checkpoint state (destructive: discards uncommitted changes).

**Recommended usage for Rhea memory:**
- Every significant session creates a named checkpoint via `rhea_commit.sh`
- `queries.jsonl` captures per-interaction deltas (ADR-014)
- `entire/checkpoints/v1` is the "long-term episodic memory" — searchable via JSON metadata
- Shadow branches are NOT for memory — they're for rollback only

---

## 3. Tribunal Warnings (Prioritized)

### W1: CRITICAL — No Product-Market Fit Validation
**17 sessions of thinking, zero shipped code.** The intellectual chain (calendars → symbolic power → polyvagal → ADHD) is coherent to the builders, not to users. Most ADHD users will ask "does this help me focus?" — not "what's the Mandate of Heaven?"

**Solution:** Define the minimal user loop: open app → 3-question survey → daily rhythm view → one actionable suggestion. Ship that. Test with 10 real users.

### W2: CRITICAL — iOS App Has Zero Implementation
Architecture docs, agent definitions, 14 ADRs — but no SwiftUI code, no HealthKit integration, no UI wireframes. The frontend is where users live. The backend elegance is invisible.

**Solution:** Wireframe before coding. Design days 1/7/30 UX. One home screen mockup. One notification strategy. Then open Xcode.

### W3: HIGH — Polyvagal Theory Is Contested
Porges' polyvagal theory faces serious anatomical critiques (Grossman 2023, Taylor 2022). Centering the scientific paper on it risks rejection.

**Solution:** Pivot paper focus to chronotype alignment + circadian science (well-established, peer-reviewed). Polyvagal as hypothesis, not centerpiece. Title suggestion: "Personalized Chronotype Adaptation in ADHD-Optimized Task Management."

### W4: HIGH — Multi-Agent System Is Premature Optimization
8 agents with tier routing is architecturally elegant but untested. Users want one good recommendation, not eight perspectives.

**Solution:** MVP uses one model, one agent. Multi-agent reasoning deferred to post-launch validation.

### W5: HIGH — No Validated Intervention Library
"Daily defaults as managed deprivation" is a hypothesis. No specific interventions have been tested on real users.

**Solution:** Pick 3 evidence-based, app-deliverable interventions:
1. Micro-reset (5 min guided breathing) — HPA-axis downregulation
2. Task-start ritual (2 min) — implementation intention literature
3. Energy reframe (1 min) — circadian rhythm alignment
Launch with these. Measure. Kill what doesn't work.

### W6: MEDIUM — Data Privacy Underdeveloped
HRV, sleep, task patterns = sensitive behavioral data. No HIPAA/GDPR plan in ADRs.

**Solution:** Privacy-by-design document before code. On-device encryption, optional cloud sync, export/delete rights. Healthcare disclaimer: "This is not medical advice."

### W7: MEDIUM — "ADHD-Optimized" Not Operationally Defined
Changed from "ADHD-first" but still vague. What does it mean in UX terms?

**Solution:** Define 5 operational patterns:
1. Fewer decision points (suggest, don't configure)
2. Shorter cognitive load (1-2 sentence explanations)
3. Just-in-time delivery (suggestions at low-energy windows)
4. Dopamine-sensitive (small wins, no punishment for misses)
5. Distraction-aware (never interrupt during focus)

---

## 4. TODO Comparison: Old vs New

### OLD TODOs (from state.md, pre-Session 17)
1. Install Entire GitHub App → checkpoints visible
2. Test rhea_commit.sh → verify checkpoint
3. iOS MVP scaffold (Stage 1)
4. Feed prism_paper_outline.md to OpenAI Prism
5. Wire bridge to .env keys → first live tribunal ✅ (done Session 16)

### NEW TODOs (post-tribunal, 3-product architecture)
1. **Install Entire GitHub App** → still #1, still blocking (human action)
2. **Define minimal user loop** → 5-minute interaction design, before any code
3. **Wireframe iOS app** → days 1/7/30 UX, Figma or paper
4. **iOS MVP implementation** → SwiftUI + HealthKit, ONE agent, ONE intervention
5. **Validate 3 interventions** → measure with beta testers
6. **Update terminology** → "ADHD-optimized" across all docs, remove "zero-questionnaire"
7. **Privacy-by-design document** → before code
8. **Paper: pivot focus** → chronotype alignment, not polyvagal-centered
9. **Entire.io CLI confirmation** → `entire enable --strategy auto-commit --force`
10. **Soft launch TestFlight** → 100 beta testers, measure 7-day and 30-day retention

### DROPPED / DEFERRED
- ~~Multi-agent tribunal for iOS~~ → deferred to post-MVP
- ~~8 agents in app~~ → 1 model for MVP
- ~~Prism paper submission~~ → deferred until user data exists
- ~~Rhea Commander (React UI/CLI)~~ → deferred to post-MVP
- ~~LangGraph integration~~ → deferred

---

## 5. Recommended Next Sessions

### Session 18: User Research + Wireframe (1 week)
- Interview 10 ADHD-spectrum users (communities, friends)
- Key questions: "biggest friction?", "would energy rhythm help?", "what opens the app daily?"
- Create low-fi wireframes: onboarding, daily view, intervention screens
- **Deliverable:** User insight doc + Figma/paper prototype

### Session 19: iOS MVP Core (2 weeks)
- Xcode project setup, SwiftUI, HealthKit (HRV proxy)
- Onboarding (3 questions → local storage)
- Daily rhythm view (initially hardcoded, ML later)
- One intervention (task-start ritual)
- **Deliverable:** Testable iOS app on simulator

### Session 20: Beta + Measurement (2 weeks)
- TestFlight with 5 trusted users
- Data logging: intervention offered/accepted/completed
- Iterate UX based on feedback
- **Deliverable:** Working beta with retention metrics

### Session 21: Soft Launch (ongoing)
- TestFlight 100 users
- A/B test 3 interventions
- Measure: 7-day retention, 30-day retention, task completion
- After 2 months: ship/pivot/kill decision

---

## 6. The Origin Recheck — Intellectual Chain Integrity

The chain from "Давай обсудим преимущества и недостатки григорианского календаря" holds at every link:

| Link | Verdict | Notes |
|------|---------|-------|
| Calendar → Symbolic Power | ✅ Solid | Foucault, Agamben, anthropology all back this |
| Symbolic Power → Environmental Constraint | ✅ Valid | Ecology of mind, niche construction theory |
| Environmental Constraint → Health/Cognition | ✅ Grounded | Chronobiology, ultradian rhythms, peer-reviewed |
| Health/Cognition → AI-Mediated Intervention | ⚠️ Speculative | Digital phenotyping exists, but Rhea-specific claims untested |
| Polyvagal mechanism specifically | ⚠️ Contested | Valid as hypothesis, not as centerpiece claim |
| ADHD as "calibration problem" | ⚠️ Novel but unproven | Interesting reframe, needs empirical validation |

**Verdict:** The chain doesn't require every link to be proven — just plausible and connected. The first 3 links are strong. Links 4-6 are the research frontier where Rhea can contribute, but shouldn't overclaim.

**Key insight from the recheck:** The intellectual depth is the *backend*. The UX must be ruthlessly simple. Users experience the conclusions, not the reasoning chain.

---

*This document is a living artifact. Each suggestion requires explicit human approval before implementation. See docs/decisions.md for the formal ADR process.*
