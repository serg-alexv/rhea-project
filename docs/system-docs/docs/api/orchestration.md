---
sidebar_position: 2
---

# Orchestration API

The orchestration endpoints expose the 8-agent system (Chronos Protocol v3) via HTTP. Agent A1 (Quantitative Scientist) acts as root manager.

## Agent Registry

| ID | Name | Role | Tier | Domain |
|----|------|------|------|--------|
| A1 | Quantitative Scientist | root_manager | cheap | Fourier analysis, Bayesian inference, MPC |
| A2 | Life Sciences Integrator | researcher | cheap | Polyvagal theory, HRV, chronobiology |
| A3 | Psychologist / Profile Whisperer | profiler | cheap | Passive profiling, ADHD-optimized UX |
| A4 | Linguist-Culturologist | researcher | cheap | 42 calendar systems, 16+ civilizations |
| A5 | Product Architect | builder | cheap | SwiftUI, HealthKit, Apple Watch, iOS MVP |
| A6 | Tech Lead | builder | cheap | Multi-model bridge, API orchestration |
| A7 | Growth Strategist | strategist | cheap | TestFlight, monetization, user acquisition |
| A8 | Critical Reviewer & Conductor | reviewer | balanced | Tribunal consensus, gap analysis, quality gate |

---

## GET /orchestration/agents

List all registered agents.

### Response

```json
[
  {
    "id": "A1",
    "name": "Quantitative Scientist",
    "role": "root_manager",
    "tier": "cheap",
    "domain": "Fourier analysis, Bayesian inference, MPC, mathematical models"
  },
  ...
]
```

### curl Example

```bash
curl http://localhost:8400/orchestration/agents
```

---

## GET /orchestration/agents/status

Get status of all agents including their current state.

### curl Example

```bash
curl http://localhost:8400/orchestration/agents/status
```

---

## GET /orchestration/agents/:agent_id

Get details for a specific agent.

### curl Example

```bash
curl http://localhost:8400/orchestration/agents/A3
```

---

## POST /orchestration/agents/:agent_id/delegate

Delegate a task to a specific agent. The agent processes the task using the Rhea Bridge at the configured tier.

### Request

```json
{
  "task": "Review the polyvagal-interoception bridge in core_context.md",
  "context": "Optional additional context"
}
```

### Response

```json
{
  "agent_id": "A2",
  "agent_name": "Life Sciences Integrator",
  "result": "[A2 RESPONSE] The polyvagal-interoception bridge...",
  "tier": "cheap",
  "elapsed_s": 2.1
}
```

### curl Example

```bash
curl -X POST http://localhost:8400/orchestration/agents/A2/delegate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-bypass" \
  -d '{"task": "Validate HRV references for circabidian hypothesis"}'
```

**Note:** If the Rhea Bridge has no valid API keys, delegation runs in **simulation mode** — returning structured placeholders instead of real LLM responses.

---

## POST /orchestration/flow

Run a predefined orchestration flow (genesis, standard, or custom).

### Request

```json
{
  "flow": "standard"
}
```

Available flows:
- `genesis` — Full initialization: loads knowledge base, delegates to all 8 agents, synthesizes results, saves snapshot
- `standard` — Daily flow: checks state, delegates to A5/A6/A8, saves snapshot

### curl Example

```bash
curl -X POST http://localhost:8400/orchestration/flow \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-bypass" \
  -d '{"flow": "genesis"}'
```

---

## POST /orchestration/snapshot

Create a manual snapshot of the current system state.

### Request

```json
{
  "label": "pre-deploy",
  "note": "Snapshot before fly.io deployment"
}
```

### curl Example

```bash
curl -X POST http://localhost:8400/orchestration/snapshot \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-bypass" \
  -d '{"label": "manual-checkpoint"}'
```

Snapshots are saved to `.entire/snapshots/` as JSON files with format: `{label}-{timestamp}-{git-hash}.json`.

---

## CLI Usage

The orchestration system can also be used directly via the Python CLI:

```bash
# Full genesis initialization
python3 scripts/rhea_orchestrate.py genesis

# Show agent status + snapshot inventory
python3 scripts/rhea_orchestrate.py status

# Delegate to a specific agent
python3 scripts/rhea_orchestrate.py delegate A3 "profile task description"

# Run standard daily flow
python3 scripts/rhea_orchestrate.py flow

# Create manual snapshot
python3 scripts/rhea_orchestrate.py snapshot "pre-deploy"
```
