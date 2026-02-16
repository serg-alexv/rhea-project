# Rhea Docs Full Extraction (27 files)
> 2026-02-16 | Compact structured report

## PER-FILE EXTRACTS

**CORE_RULES.md** -- 5 hard constraints (HC-1..HC-5), state vector [Progress,Risk,Debt,Evidence,MemoryLoad,Budget]. Phase 1 DoD entirely unchecked. Missing required artifacts: CORE_MEMORY.md, TODO_MAIN.md, SELF_UPGRADE_OPTIONS.md.

**INTEGRATIONS_AUDIT.md** -- 93 integrations, 86 pass, 0 fail, 7 untested. All 6 API providers + 4 tiers operational. 7 MCP servers still UNTESTED. "Known Issues" section has stale entries (says state.md violated, rhea CLI missing -- both fixed).

**MVP_LOOP.md** -- Draft spec. Controller proposing next-best-action. State: sleep_proxy/energy/time_budget/friction. Bayesian online updates. Zero implementation.

**NOW.md** -- 4-tier upgrade schedule. Tier 0 (fixes) done. Tier 1 undone: no .claude/agents/, no SELF_UPGRADE_OPTIONS.md, no TODO_MAIN.md, no CORE_MEMORY.md. Tier 2-3 undone.

**ROADMAP.md** -- 13 lines. S0 specs, S1 iOS MVP, S2 passive signals, S3 MPC optimization. All stages unstarted. Conflicts with richer plan in upgrade_plan_suggestions.md.

**TOKEN_OPTIMIZATION.md** -- 5-layer: Bonsai free models, Mintlify docs, Entire.io memory, MEMORY.md auto-context, CLAUDE.md tuning. Bonsai login undone. MEMORY.md now populated (was empty when written).

**api_contracts.md** -- Bridge API implemented. State/Metrics/Eval/PWA APIs all "future."

**architecture.md** -- iOS app reconstructing daily defaults. Polyvagal/HRV/interoception/circadian/cultural. 8 agents, 6 providers. Claims "400+ models" -- actually 31 configured.

**article_gpt_pro_vs_cowork.md** -- Publishable article (unpublished). Multi-provider abstraction > single vendor. *"The future of AI productivity isn't choosing one vendor."*

**core_context.md** -- Full genesis: calendar critique -> 42 systems -> symbolic power (8 levels) -> hunter-gatherer zero -> polyvagal/ADHD -> agents -> app. 9 research domains identified but unimplemented. *"They define not behavior but categories of thought."*

**cost_guide.md** -- Target $0.05/day. Cheap tier ~80% calls. No actual cost tracking implemented.

**decisions.md** -- 14 ADRs. Key: ADR-007 three-tier memory, ADR-008 cheap-first, ADR-010 discomfort D, ADR-012 manual-commit SUPERSEDED by ADR-014 auto-commit. ADR-013 wrapper script.

**langgraph_architecture.md** -- DESIGN ONLY. RheaState TypedDict, 9 agent + 6 meta nodes, dual checkpoint. Zero code.

**memory_managing2025-2026.md** -- Research memo. Workspace-first (InfiAgent), memory as tool-actions (AgeMem), gated retrieval, revisitable pointers. None implemented. *"'Infinite chat history' is fragile."*

**prism_paper_outline.md** -- 8-section paper: Fourier/Bayesian/MPC/bandit math, cross-cultural validation. Not generated. W3 warns polyvagal focus is contested.

**reflection_log.md** -- 5 failure entries. Key lesson: verify ALL execution contexts trigger lifecycle hooks.

**soul.md** -- Base config every agent inherits. ADHD + anankastic compensatory architecture. 7 principles. *"Structure that feels like freedom."*

**state.md** -- Compact ~1.2KB. Bridge live, 14 ADRs, D=63.4. Next: Entire GitHub App, user loop, iOS MVP.

**state_agents_core.md** -- 9 agents with tier policy. soul.md base + agent delta. Definitions only, no code wired.

**state_full.md** -- Append-only log. STALE (last updated 2026-02-13, missing 2+ sessions). Refs say "7 ADRs" (actually 14). Tech debt: sync requests, count-based consensus, no retry.

**tribunal_001_autocommit.md** -- Kept manual-commit (2-1). Hybrid deferred. SUPERSEDED by ADR-014.

**tribunal_002_memory_architecture.md** -- 3/3 unanimous: wrapper script. Agreement 0.95. ADR-013.

**ui_pwa_vision.md** -- FUTURE. 4 prerequisites unmet. React/TypeScript/Tailwind/Vite planned.

**upgrade_plan_suggestions.md** -- 7 warnings: W1 zero shipped code, W2 no iOS implementation, W3 polyvagal contested, W4 multi-agent premature, W5 no validated interventions, W6 no privacy doc, W7 ADHD-optimized undefined. All unaddressed. *"17 sessions of thinking, zero shipped code."*

**user_examples.md** -- 5 examples. Benchmark numbers stale (shows 70/71, now 75/78).

**user_guide.md** -- Full guide. D=91.96 stale (now 63.4). Says 13 ADRs (now 14).

**plans/2026-02-15-fix-audit-failures.md** -- 5-task plan. Tasks 1-3 done. Task 4 partial (audit Known Issues stale).

---

## CROSS-CUTTING

### Contradictions
1. **D metric:** 63.4 (state.md) vs 62.7 (state_full) vs 91.96 (user_guide)
2. **ADR-012 vs ADR-014:** manual-commit reversed to auto-commit; many docs still say manual
3. **Model count:** 400+ (architecture) vs 31 (bridge code)
4. **ADR count:** 7 (state_full refs) vs 13 (user_guide) vs 14 (actual)
5. **state_full.md** stale by 3+ days

### Top 10 Undone
1. Zero shipped code (iOS, LangGraph, any product)
2. Three required docs missing: CORE_MEMORY.md, TODO_MAIN.md, SELF_UPGRADE_OPTIONS.md
3. .claude/agents/ not created
4. 7 MCP servers untested, 13 Desktop MCPs unaudited
5. Paper not generated; polyvagal focus contested
6. No privacy-by-design document
7. No validated intervention library
8. Bonsai login undone (free models not activated)
9. Entire GitHub App not installed
10. No cost tracking in metrics

### Quotes Worth Preserving
- "Alive = reliable loops + memory + tool use + correction." (CORE_RULES)
- "17 sessions of thinking, zero shipped code." (upgrade_plan W1)
- "They define not behavior but categories of thought." (core_context)
- "Structure that feels like freedom." (soul.md)
- "If you have to pay for it -- it was probably free in the ancestral environment." (core_context)
- "'Infinite chat history' is fragile. Workspace/state first." (memory_managing)
- "The future of AI productivity isn't choosing one vendor." (article)
