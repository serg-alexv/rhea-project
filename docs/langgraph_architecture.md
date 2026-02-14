# Rhea — LangGraph Architecture
> Status: DESIGN PHASE — no code yet, skeleton for incremental scaffolding
> Last updated: 2026-02-13 | ADR-010 (Memory Budget) applies

## 1. Overview

Rhea's behavior modeled as a directed graph of states and agents.
LangGraph (https://github.com/langchain-ai/langgraph) provides:
- State management with typed state objects
- Conditional routing between nodes
- Built-in checkpointing (integrates with Entire.io episodic memory)
- Human-in-the-loop breakpoints

## 2. State Schema

```python
from typing import TypedDict, Literal

class RheaState(TypedDict):
    # Core state vector (from mathematical framework)
    energy: float          # E_t [0,1]
    mood: float            # M_t [0,1]
    cognitive_load: float  # C_t [0,1]
    sleep_debt: float      # S_t hours
    obligations: list      # O_t structured list
    recovery: float        # R_t [0,1]

    # Memory & metrics
    discomfort_level: Literal["comfort", "warning", "overload"]
    current_D: float
    active_sprint: bool

    # Session context
    current_agent: str
    messages: list
    last_checkpoint_id: str
```

## 3. Graph Nodes (Agents)

### Core Operational Nodes
| Node | Agent | Default Tier | Purpose |
|------|-------|-------------|---------|
| `router` | Rhea (Root) | cheap | Route incoming request to appropriate agent |
| `chronos` | Chronos | cheap | Time awareness, schedule, rhythm detection |
| `gaia` | Gaia | cheap | Body state, HRV, interoception signals |
| `hypnos` | Hypnos | cheap | Sleep analysis, debt calculation |
| `athena` | Athena | balanced→expensive | Strategy, planning, deep reasoning |
| `hermes` | Hermes | cheap | Communication, user interaction |
| `hephaestus` | Hephaestus | balanced→expensive | Build, code generation, technical work |
| `hestia` | Hestia | cheap | Safety checks, constraint enforcement |
| `apollo` | Apollo | cheap→reasoning | Insight synthesis, pattern detection |

### Meta Nodes (System)
| Node | Purpose |
|------|---------|
| `metrics_check` | Evaluate discomfort function D, decide if sprint needed |
| `archivist` | Reflexive Sprint — summarize, compact, archive |
| `oracle_query` | Compose query for Atlas (ChatGPT) or Castor (Gemini) |
| `oracle_integrate` | Integrate oracle response into docs/code |
| `checkpoint` | Create Entire.io + git checkpoint |
| `error_recovery` | Handle failures, rollback if needed |

## 4. Graph Edges (Transitions)

```
START → router
router → {chronos, gaia, hypnos, athena, hermes, hephaestus, apollo}  # conditional on request type
any_agent → hestia  # safety check before action
hestia → checkpoint  # if action approved
hestia → error_recovery  # if action rejected

checkpoint → metrics_check
metrics_check → router  # if D < T1 (comfort)
metrics_check → archivist  # if D >= T2 (overload → Reflexive Sprint)

archivist → checkpoint → router  # after sprint, return to normal

# Oracle flow (human-mediated)
any_agent → oracle_query  # when agent needs external model
oracle_query → HUMAN_BREAKPOINT  # wait for human to paste oracle response
HUMAN_BREAKPOINT → oracle_integrate → checkpoint → router
```

## 5. Memory Flow

```
                    ┌─────────────────────┐
                    │   Episodic Memory    │
                    │  .entire/snapshots/  │
                    │  + Entire.io cloud   │
                    └────────┬────────────┘
                             │ read/write
                    ┌────────▼────────────┐
                    │    RheaState         │
                    │  (LangGraph state)   │
                    └────────┬────────────┘
                             │ flows through
                    ┌────────▼────────────┐
                    │   Agent Nodes        │
                    │  (read state, act,   │
                    │   update state)      │
                    └────────┬────────────┘
                             │ persists to
                    ┌────────▼────────────┐
                    │  Structured Memory   │
                    │  docs/*.md           │
                    │  metrics/*.json      │
                    │  data/*.yaml         │
                    └─────────────────────┘
```

## 6. Checkpoint Integration

Dual checkpoint system:
1. **LangGraph native** — automatic state snapshots at each node transition
2. **Entire.io** — named episodic snapshots at meaningful milestones

Integration rule: LangGraph checkpoints are ephemeral (session-scoped).
Entire.io checkpoints are persistent (repo-scoped, pushed to GitHub).

At each `checkpoint` node:
1. LangGraph saves internal state automatically
2. Our code creates `.entire/snapshots/` JSON with context
3. Git commit with `Entire-Checkpoint` trailer (when entire CLI available)

## 7. Implementation Roadmap

| Phase | What | When |
|-------|------|------|
| 0 (current) | This design doc | Now |
| 1 | `langgraph/state.py` — RheaState definition | Next session |
| 2 | `langgraph/graph.py` — basic router + 2 agents | After phase 1 |
| 3 | Add metrics_check + archivist nodes | After D approaches T1 |
| 4 | Oracle query/integrate nodes | When multi-model flow needed |
| 5 | Full 9-agent graph with all transitions | When core memory stable |

## 8. Design Decisions

- **Cheap-first routing** (ADR-008): Router always starts with cheap tier
- **Human-in-the-loop for oracles** (Section 8 of system prompt): No direct ChatGPT/Gemini calls
- **Reflexive Sprint as graph subflow**: Not a separate system — it's a path through the same graph
- **No PWA coupling**: Graph operates independently; PWA is a future view layer (see ui_pwa_vision.md)

## 9. Self-Evaluation Nodes (ADR-011)

The graph includes self-improvement capabilities as subflows:

### Reflexion Subflow
```
agent_output → self_evaluate → {pass: checkpoint, fail: revise → agent (retry, max 3)}
```

### Tribunal Subflow
```
router → [model_1, model_2, model_3] → synthesize → checkpoint
```

### Eval Runner Node
```
eval_trigger → load_task(eval/tasks/*.yaml) → run_against_model → score → log(eval/results/)
```

### Failure Memory Lookup
```
any_agent(before_action) → check(docs/reflection_log.md) → {match: inject_lesson, no_match: proceed}
```
