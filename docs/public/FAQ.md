# Rhea -- Frequently Asked Questions

---

### 1. What is Rhea?

Rhea is a coordination pattern for AI agents. It provides git-backed persistence, a file-based office protocol (inbox/outbox/capsule/gems/incidents/decisions/procedures), a multi-provider LLM bridge, and a knowledge promotion chain. It is not an app or a framework -- it is an operating pattern that runs on top of existing tools (git, Firebase, any LLM provider).

---

### 2. Who is it for?

Engineers and researchers running multi-agent workflows who are frustrated by: sessions dying and losing all context, agents that cannot coordinate across terminals, single-provider lock-in, and the inability to audit why an agent made a specific decision. If you have ever restarted a session and spent the first 20 minutes re-explaining what you were doing, Rhea addresses that problem.

---

### 3. Why not just use ChatGPT / Claude / a single provider?

Single-provider dependency creates three risks: (1) provider outage stops all work, (2) single-model bias in reasoning -- one model's blind spots become your project's blind spots, (3) cost lock-in at premium tiers for work that a cheaper model handles fine. Rhea's bridge (`rhea_bridge.py`) routes across 6 providers and 31 models with cheap-first defaults. In observed operation (2026-02-16), 2 of 6 providers went down during a session. Work continued without interruption because the cheap tier always had at least 3 available candidates. A single-provider setup would have stopped.

---

### 4. How does memory work?

Three tiers (ADR-007):

1. **Git** -- `docs/state.md` (under 2KB, enforced by `check.sh`) is long-term memory. Everything committed is permanent and auditable.
2. **Virtual office** -- `ops/virtual-office/` files (capsule, gems, incidents, decisions) are working memory. Updated by agents in real-time.
3. **Firebase** -- real-time sync for cross-terminal coordination. Heartbeats, messages, gems mirrored to Firestore collections.

Session death recovery: three files (`state.md`, `TODAY_CAPSULE.md`, `OFFICE.md`) restore full context in under 30 seconds. Tested with a fresh agent that had never seen the project -- it answered 6/6 context questions correctly from these files alone (GEM-002).

---

### 5. What about costs?

Default behavior is cheap-first (ADR-008). The bridge routes ~80% of all calls to the cheapest available tier (Sonnet, Flash, mini class models). Expensive models (Opus, GPT-4.5, o3) require explicit justification and are logged. The tribunal mode (3-5 models voting) is reserved for high-stakes decisions. Two tribunals have been run to date -- both used free-tier models and produced unanimous results. Per-call cost logging goes to `.entire/logs/ops.jsonl`. See `docs/cost_guide.md` for per-provider pricing.

---

### 6. Is it open source?

The repository (`rh.1`) is on GitHub. The coordination pattern (virtual office protocol, promotion chain, bridge architecture) is fully documented in markdown files within the repo. There is no proprietary component -- it runs on git, Python, and Firebase (which has a free tier). The bridge uses standard OpenAI-compatible chat completions APIs. Adding a new provider requires under 10 lines of configuration.

---

### 7. What models are supported?

31 models across 6 providers and 4 cost tiers:

| Tier | Purpose | Example Models |
|------|---------|---------------|
| Cheap (default) | Routine work | Claude Sonnet 4, Gemini 2.0 Flash, GPT-4o-mini, DeepSeek Chat |
| Balanced | Complex reasoning | GPT-4o, Gemini 2.5 Flash, GPT-4.1, Mistral Large |
| Expensive | Deep research, critique | Gemini 2.5 Pro, GPT-4.5, Claude Opus 4.6 |
| Reasoning | Chain-of-thought, math, logic | o4-mini, DeepSeek Reasoner, o3 |

Run `python3 src/rhea_bridge.py tiers` to see the full list with availability status.

---

### 8. How do I contribute or try it?

1. Clone the repo.
2. Copy `.env.example` to `.env` and add at least one API key (OpenAI or Gemini recommended as starting points).
3. Run `python3 src/rhea_bridge.py status` to verify provider connectivity.
4. Read `ops/virtual-office/OFFICE.md` for the coordination protocol.
5. Run `bash scripts/rhea/check.sh` to verify repo invariants.

To contribute: open an issue or PR. The most valuable contributions right now are: stress-testing the office pattern with different agent configurations, adding new providers to the bridge, and reporting what breaks when running with more than 4 concurrent agents.

---

### 9. What is the roadmap?

**Near-term (weeks):** Publish the office protocol as a reproducible pattern. Add per-call cost dashboards to the bridge. Build automated Context Tax Collector (detect repeated patterns across sessions, auto-promote to gems/procedures).

**Medium-term (months):** iOS offline-first MVP (SwiftUI + HealthKit, one agent, one intervention). Formalize the promotion protocol (capsule/gem/incident/decision/procedure) as a publishable framework. Validate with operators beyond the original team.

**Long-term:** Persistent agent services (not session-bound). Cross-project knowledge sharing. Scientific paper on the mathematical foundations (Fourier analysis of biorhythms, Bayesian personalization, model predictive control).

See `docs/ROADMAP.md` for the stage-by-stage plan.

---

### 10. Is the polyvagal / chronobiology science proven?

Polyvagal theory (Porges) is an established framework in clinical psychology and neuroscience, though it has critics. The specific claims Rhea builds on:

- **HRV as proxy for vagal tone and cognitive control** -- well-supported (Laengle et al. 2025, Takeda et al. 2025).
- **Diminished interoception in ADHD** -- supported (Bruton et al. 2025).
- **Hunter-gatherer sleep patterns as calibration baseline** -- supported (Yetish et al. 2015, Wiessner 2014 PNAS).
- **Circabidian rhythms explaining ADHD "good day / bad day" alternation** -- working theory. Plausible mechanism (48-hour oscillation in dopaminergic tone) but not yet validated in Rhea's context.

**Rhea's position:** The chronobiology foundation informs the design of the iOS app and the agent recommendations. It does not affect the coordination infrastructure (office protocol, bridge, promotion chain), which is model-agnostic and science-agnostic. If the polyvagal angle turns out to be wrong, the Office OS still works. The science layer is a separate concern from the coordination layer.
