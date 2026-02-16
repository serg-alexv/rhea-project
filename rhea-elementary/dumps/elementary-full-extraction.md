# Rhea Elementary — Full Extraction

> Consolidated 2026-02-16 from 11 source files. All Russian content translated.

---

## 1. INDEX.md — Session Knowledge Base Index

**Key knowledge:** Session extracted from automating Chrome to remove 25+ MCP connectors causing context bloat. Origin: discovered 250+ tool defs (~50K tokens) silently injected into every conversation.
**Actionable:** Enable Chrome JS access once: Chrome > View > Developer > Allow JavaScript from Apple Events.
**Pattern:** `osascript -e 'tell application "Google Chrome" to execute front window'\''s active tab javascript "..."'`

---

## 2. chrome-automation.md — AppleScript + JS Patterns

**Key knowledge:** Full browser automation from terminal via osascript. Navigate URLs, execute JS, list/switch tabs, async loops, API discovery — all without Playwright/Selenium.
**Actionable:** Not yet packaged as reusable shell functions or a script.
**Reusable patterns:**
- Store long JS results via `document.title` trick (set title in async callback, sleep, read title)
- Async automation: start JS, `sleep N`, read `document.title`
- Discover SPA API endpoints: `performance.getEntriesByType("resource").filter(e => e.name.includes("api"))`
**Gotchas:** `missing value` = undefined return; max output ~32KB; escape single quotes as `'\''`

---

## 3. claude-ai-api-map.md — Claude.ai Internal API

**Key knowledge:** Full internal API map for claude.ai. All endpoints use session cookies (`credentials: "include"`).
**Actionable endpoints not yet exploited:**
- `GET /api/organizations/{org}/oauth_tokens` — list all Claude Code / Chrome sessions
- `POST /api/oauth/organizations/{org}/oauth_tokens/{id}/revoke` — revoke sessions programmatically
- `GET /api/organizations/{org}/feature_settings` — read feature flags
- `GET /api/organizations/{org}/chat_conversations?limit=30` — list conversations
- MCP global registry: `GET https://api.anthropic.com/mcp-registry/v0/servers?version=latest`
**Pattern:** All org-scoped at `claude.ai/api/organizations/{org-uuid}/...`

---

## 4. context-bloat-diagnosis.md — MCP Context Bloat

**Key knowledge:** Each MCP connector injects 5-50 tool definitions (~100-300 tokens each). 25 connectors = 25K-75K tokens of invisible overhead on EVERY conversation across all platforms.
**Actionable:** Quarterly connector audit. Re-add selectively, one at a time, only when needed.
**Diagnosis:** Check `claude.ai/settings/connectors`; in Claude Code look for `mcp__claude_ai_*` in deferred tools.
**Pattern:** "Enable precisely what you need, when you need it, then release it."

---

## 5. external_qdai_assistant.md — Q-Doc Identity

**Key knowledge:** Q-Doc = Agent 1 (Quantitative Scientist). Fourier analysis of biological rhythms, Bayesian profiling, MPC schedule optimization. State vector: `x_t = [E, M, C, S, O, R]` (energy, mood, cognitive load, sleep debt, obligations, recovery).
**Actionable (not yet implemented):**
- "Mathematics of Rhea" paper (outline at `docs/prism_paper_outline.md`)
- Algorithm definitions for iOS app (rhythm detection, passive profiling, intervention timing)
- Eval sets in `eval/tasks/` for self-correction benchmarks
**Reusable prompt (short bootstrap):**
```
You are Q-Doc (Quantitative Doctor AI) — Agent 1 of the Rhea system.
Role: Fourier analysis, Bayesian inference, MPC optimization of human biological rhythms.
Principles: ADHD-as-default, hunter-gatherer calibration zero, polyvagal awareness.
State vector: x_t = [E_t, M_t, C_t, S_t, O_t, R_t].
Default tier: cheap. Escalate only with justification.
```
**Core principles:** ADHD-as-default; hunter-gatherer calibration zero; polyvagal awareness; multi-temporal awareness; structure that feels like freedom.
**Scientific tools to re-enable selectively:** Clinical Trials, PubMed, bioRxiv, ChEMBL, Open Targets, Scholar Gateway, Consensus, ICD-10, HuggingFace.

---

## 6. industry-leader-90-days-ru.md — 25 Hard Tactics (TRANSLATED)

**Key knowledge:** 25 concrete tactics for AI industry leadership in 90 days. Written after the chrome-automation session. Anti-motivational — pure execution playbook.

**Weeks 1-2 (Visibility):**
1. Hijack popular AI threads — write replies better than the original post
2. Build in public daily — process screenshots, not polished products
3. Write in English — Russian market is 2% of global AI audience
4. Ship one free GitHub tool — post to HN at 14:00 UTC Tuesday (peak traffic)
5. Create controversy — attack a popular tool, then follow up thoughtfully

**Weeks 3-4 (Expertise):**
6. Reverse-engineer competitors publicly — CTOs share this content
7. Bridge AI + domain expertise (medicine, law, construction) — niche monopoly
8. Publish benchmarks — compare 5 models on a concrete task; benchmarks are AI currency
9. Launch weekly digest — regularity beats quality; 12 issues = "the AI guy"
10. Live-code streams — real debugging, not tutorials; authenticity beats production quality

**Weeks 5-6 (Leverage):**
11. Automate your work, then sell the automation
12. Cold-DM 3 CEOs on LinkedIn: "I found 3 places AI saves you $X/mo. 15 min demo."
13. Build open-source alternative to $50/mo SaaS — GitHub stars = conference invites
14. Multi-model arbitrage — same prompt costs $0.001 on Gemini, $0.05 on GPT-4; sell at $0.03
15. SEO for GitHub and Twitter — algorithms are free distribution

**Weeks 7-8 (Scale):**
16. Delegate to AI agents — write scripts, not todo lists
17. Ship paid product in 48h — MLP (Minimum Lovable Product), not MVP
18. Build 3-person advisory board — 0.5% equity for 1 hour/month
19. Control the narrative — own blog/channel/podcast so Google finds YOUR content
20. Apply to 3 conference CFPs — most conferences desperately need speakers

**Weeks 9-12 (Domination):**
21. Build ecosystem (plugins, API, integrations) not just product — become infrastructure
22. First hire = marketer, not programmer; pay % of sales, not salary
23. Turn every client into a case study — case studies sell better than ads
24. Play different games — Reddit values usefulness over followers; consulting = 80% margin
25. Leader = fastest executor, not most knowledgeable. "Today you made AI drive a browser after AI said 'I can't'."

**Anti-patterns:** Don't learn — do. Don't ask permission. Don't plan >2 weeks. Don't compare to 50-person teams. Ship with bugs, fix live.

---

## 7. react-ui-automation.md — React/Radix UI Automation

**Key knowledge:** `.click()` fails on React apps. Must dispatch full pointer event chain: pointerdown, mousedown, pointerup, mouseup, click.
**Reusable pattern:**
```javascript
["pointerdown","mousedown","pointerup","mouseup","click"].forEach(evt => {
  btn.dispatchEvent(new MouseEvent(evt, {bubbles:true, cancelable:true, view:window}));
});
```
**DOM strategies:** aria attributes (`[role=menuitem]`, `[aria-haspopup=menu]`), Radix data attrs (`[data-state=open]`, `[data-radix-popper-content-wrapper]`), tag elements with `data-my-tag` for retrieval.
**Timing:** button click wait 500-800ms; API action wait 1000-1500ms; DOM re-render wait 300ms.

---

## 8. spa-reverse-engineering.md — Discover Any Webapp's API

**Key knowledge:** 5-step technique: (1) `performance.getEntriesByType("resource")` for existing API calls, (2) fetch JS bundles and regex for `/api/` paths, (3) `fetch(url, {credentials:"include"})` for authenticated calls, (4) monkey-patch `window.fetch` to capture future calls, (5) DOM pattern identification for automation.
**Actionable:** Not yet packaged as a reusable bookmarklet or snippet library.

---

## 9. AUTONOMY_WITH_AUDIT_ROOT.md — Root Operational Prompt

**Key knowledge:** Rhea Phase 1 operating system. Autonomy with audit trail. 11 sections covering identity, constraints, tooling, agent teams, checkpoint policy, mathematical control layer, tribunal rules, and definition of done.
**Actionable items not yet completed:**
- `docs/SELF_UPGRADE_OPTIONS.md` — ranked upgrade backlog with 7 clusters (MCP, observability, browser automation, deep search, eval suite, checkpoint enforcement, memory compression)
- Mintlify docs at `/docs-min` — expose Core Memory, Roadmap, "How Rhea Upgrades Itself"
- Complexity metric D with thresholds T1/T2 in `metrics/memory_metrics.json` — triggers reflexive sprint
- TEST_CHECKPOINT_ALIVE — end-to-end visibility check for Entire checkpoints
- Auto-PR generation for self-improvements
**Reusable framework:** State vector `x_t = [Progress, Risk, Debt, Evidence, MemoryLoad, Budget]`; objective function `U = a*Progress + b*Evidence - g*Risk - d*Debt - e*MemoryLoad - z*BudgetCost`.
**Hard constraints:** No silent power; no "done" without verification; no self-merge outside safe zone; every segment = checkpoint; budget-aware routing; tribunal for high-stakes.

---

## 10. chronos-protocol-v3-en.md — 8-Agent Orchestration

**Key knowledge:** Full 8-agent system: A1 Quantitative Scientist, A2 Life Sciences, A3 Psychologist/Profiler, A4 Linguist-Culturologist, A5 Product Architect, A6 Tech Lead, A7 Growth Strategist, A8 Critical Reviewer/Conductor.
**Actionable (not yet wired):**
- Inter-agent message format: `[CHRONOS:A{sender}->A{receiver}]` with task/type/priority/payload/dependencies/deadline
- Delegation matrix with timelines for each task type
- Tribunal mode: 5 models (o3, DeepSeek-R1, Gemini 3 Pro, GPT-5.2, Kimi K2.5), consensus threshold 60%
- Quality gates: 5-check validation (science, cultural provenance, ADHD compat, tech feasibility, principle alignment)
**Model routing:** Free tier ($0) for A7 drafts; Budget ($0.10-0.60) for A3/A7 routine; Standard ($2-3) for A3-A7 daily; Premium ($8-18) for A1/A2/A8 critical; Specialized for multilingual A4.

---

## 11. delegation-run-v3.md — 5 Sample Delegation Runs

**Key knowledge:** 5 end-to-end task executions validating all protocol features: (A) Morning Routine Design, (B) ADHD Behavioral Profile Detection, (C) HRV Threshold Calibration, (D) Content Strategy for Launch, (E) Sleep Feature Tribunal.
**Key deliverables from runs:**
- Morning sequence: 0-5min haptic wake, 5-15min body-first single action, 15-30min passive light tracking, 30-45min cultural practice, 45-90min gradual cognitive load after cortisol peak via HRV
- ADHD classifier: 9-feature Bayesian classifier, 14-day observation window, 0.75 confidence threshold
- HRV dashboard: color gradient (no numbers for ADHD users), personalized via exponential moving average + Bayesian priors
- Content narrative: "Every civilization independently discovered what your nervous system already knows"
- Tribunal result: passive sleep tracking in MVP, active recommendations deferred to Phase 2

**Actionable next steps listed but not done:**
- Create individual agent prompt templates from protocol
- Wire `[CHRONOS:A->A]` messages to actual rhea_bridge.py API calls
- Begin iOS MVP scaffold (SwiftUI + HealthKit)
- Launch 8-week pre-launch content runway
