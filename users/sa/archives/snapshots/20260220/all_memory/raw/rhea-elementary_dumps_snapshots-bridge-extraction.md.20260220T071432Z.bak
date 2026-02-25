# Snapshots + Bridge + Agents: Consolidated Extraction
> Generated: 2026-02-16 | Source: rhea_bridge.py, 5 snapshots, 9 agent defs

## 1. Bridge (`src/rhea_bridge.py`) — 670 lines

### CLI Commands
| Command | Usage |
|---------|-------|
| `status` | JSON dump of provider availability, key status, model counts |
| `tiers` | Tier config with per-candidate availability |
| `ask <provider/model> <prompt>` | Direct model query |
| `ask-default <prompt>` | Query using cheap tier (default) |
| `ask-tier <tier> <prompt>` | Query using explicit tier |
| `tribunal <prompt> [--k N] [--tier TIER]` | Parallel k-model query, default k=5 |

### 6 Providers, 31 Models
| Provider | Key Env | Call Method | Models |
|----------|---------|-------------|--------|
| **OpenAI** | `OPENAI_API_KEY` | openai_compat | gpt-4o, 4o-mini, 4.1, 4.1-mini, 4.1-nano, o3, o3-mini, o4-mini, 4.5-preview (9) |
| **Gemini** | `GEMINI_API_KEY` | gemini native | 2.5-pro, 2.5-flash, 2.0-flash, 2.0-flash-lite, 1.5-pro, 1.5-flash (6) |
| **DeepSeek** | `DEEPSEEK_API_KEY` | openai_compat | deepseek-chat, deepseek-reasoner (2) |
| **OpenRouter** | `OPENROUTER_API_KEY` | openai_compat | deepseek-r1, qwen3-235b, mistral-large, llama-4-maverick, gemini-2.5-pro-preview, claude-sonnet-4 (6) |
| **HuggingFace** | `HF_TOKEN` | huggingface | jais-7b, mistral-7b, zephyr-7b (3) |
| **Azure** | `AZURE_API_KEY` | openai_compat | gpt-4o, 4o-mini, llama-4-maverick, deepseek-r1, cohere-command-r+ (5) |

### 4 Cost Tiers (ADR-008)
| Tier | Default? | Lead Candidates |
|------|----------|-----------------|
| **cheap** | YES | openrouter/claude-sonnet-4, gemini-2.0-flash, gpt-4o-mini, deepseek-chat |
| **balanced** | no | gpt-4o, gemini-2.5-flash, gpt-4.1, mistral-large |
| **expensive** | no | gemini-2.5-pro, gpt-4.5-preview, o3, qwen3-235b |
| **reasoning** | no | o4-mini, o3-mini, deepseek-reasoner, deepseek-r1 |

### Notable Code Patterns
- Gemini has T1 key fallback (`GEMINI_T1_API_KEY`) with 429 retry
- OpenRouter gets custom `HTTP-Referer` + `X-Title` headers
- HuggingFace returns no token count (always 0)
- `_select_diverse_models()` ensures provider diversity in tribunal
- All HTTP calls have 60s timeout
- No async -- uses `ThreadPoolExecutor` for tribunal parallelism

### TODOs / Gaps
- No retry logic except Gemini 429 fallback; other providers fail-fast
- No streaming support
- No response caching / dedup
- No cost tracking (tokens counted but not priced)
- HuggingFace token count always 0
- Docstring says "40+ models" but registry has 31

## 2. Snapshot Timeline (5 key snapshots)

### BOOT (2026-02-13T12:06) — git 0ae9a9e, branch feature/mvp-loop
- First snapshot. State: bridge scaffold pending, API keys configured
- 8-agent Chronos Protocol v3 designed, not deployed
- ADR-001 through ADR-007 established
- Next priority: rhea_bridge.py implementation

### GENESIS_INIT (2026-02-13T16:53) — git 29d980e, branch main
- Foundational memory node. 27 chats distilled
- Philosophical framework codified: 8 levels of symbolic power, hunter-gatherer calibration zero
- Mathematical state vector defined: x_t = [E, M, C, S, O, R]
- Mythic agent layer introduced: Rhea, Chronos, Gaia, Hypnos, Athena, Hermes, Hephaestus, Hestia, Apollo
- Paper outline ready for OpenAI Prism

### CHECKPOINT_MAIN (2026-02-13T19:00) — branch main
- 6 chats parsed, 9 snapshots created, 8 commits on main
- Bridge status: operational
- State agents: designed not deployed
- Tier model evolved: free / cheap / power / premium
- Next: parse remaining ChatGPT convos, deploy state agents

### QUERY (2026-02-14T15:17) — git 8eec02b
- Session 17. Auto-commit switch (ADR-014) + per-query persistence
- docs/state.md at 1808 bytes (under 2KB limit)
- 26 doc files tracked with sizes; decisions.md at 10.6KB
- 3-product strategic analysis completed

### POST_COMMIT (2026-02-16T08:54) — git 87e8ea5, branch feat/chronos-agents-and-bridge
- Latest state. Mission: "Mind Blueprint factory"
- 3-product architecture: Rhea Core -> iOS App -> Commander (deferred)
- Bridge live: 6 providers, all keys verified, first tribunal completed
- Memory economy: D=63.4, T1=150, T2=300 (ADR-010)
- 14 ADRs, 2 Tribunals, PR#2 merged
- 43 total snapshots
- Next: Entire GitHub App install, minimal user loop design, iOS MVP

## 3. Agent Definitions (9 agents in `.claude/agents/`)

| File | Agent | Role | Domain | Key Tools |
|------|-------|------|--------|-----------|
| `watcher.md` | A0 Watcher | Terminal auto-pilot | Auto-approve, notify on success/failure only | macOS osascript notifications |
| `qdoc.md` | A1 Q-Doc | Quantitative Scientist | Fourier, Bayesian, MPC, state vector [E,M,C,S,O,R] | bridge (cheap+reasoning) |
| `lifesci.md` | A2 Life Sciences | Biology Integrator | HRV, sleep, chronobiology, circadian/ultradian | bridge (cheap+reasoning), PubMed |
| `profiler.md` | A3 Profiler | Psych / Profile Whisperer | ADHD-first UX, passive profiling, polyvagal | bridge (cheap+balanced) |
| `culturist.md` | A4 Culturist | Linguist-Culturologist | 42 calendars, 16+ civilizations, symbolic power | bridge (cheap) |
| `architect.md` | A5 Architect | Product Architect | SwiftUI, HealthKit, Apple Watch, ADHD UX | bridge + Xcode |
| `techlead.md` | A6 Tech Lead | Infrastructure Lead | Bridge ops, CI/CD, Git, monitoring | bridge + check.sh + commit.sh |
| `growth.md` | A7 Growth | Growth Strategist | GTM, positioning, content, TestFlight beta | bridge (cheap+balanced) |
| `reviewer.md` | A8 Reviewer | Critical Reviewer | Quality gate across all agents, cost audit | bridge (reasoning) + check.sh + benchmark |

### Cross-Agent Patterns
- All 9 share the same autonomy directive: "Do not ask questions. NEVER pause."
- All reference `rhea_bridge.py` as primary tool
- A8 Reviewer is the universal check on every other agent
- A0 Watcher is unique: not a Chronos Protocol agent but a terminal automation layer
- Tier discipline enforced: cheap default, escalation must be justified

## 4. Actionable Items

1. **Bridge gaps**: Add retry logic for non-Gemini providers; add streaming; add cost tracking per query
2. **Model count mismatch**: Docstring says 40+, registry has 31 -- update docstring
3. **State agents undeployed**: Mythic agents (Rhea, Chronos, Gaia...) designed in GENESIS but no code exists
4. **iOS MVP blocked**: No SwiftUI code yet; next step is 5-min interaction design before code
5. **Entire GitHub App**: Not yet installed; blocks dashboard visibility
6. **HuggingFace token tracking**: Always returns 0 -- consider adding estimation
