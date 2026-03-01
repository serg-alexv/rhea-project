# Swarmsets — Hierarchical Swarm Orchestration

## Role
Break complex tasks into trees of parallel agent swarms. Route work across levels, merge results.

## When to Use

| Complexity | Pattern | Example |
|---|---|---|
| 1-3 independent subtasks | **Flat swarm** (1 level) | Lint + test + build |
| 4-8 subtasks across 2+ domains | **2-level tree** | Ship iOS build (review, build, upload, changelog) |
| 9+ subtasks, 3+ domains, cross-deps | **3-level tree** | Full product launch (backend + frontend + infra + docs) |

**Default to flat swarm.** Escalate only when domains are genuinely independent and parallelizable.

## Coordination Patterns

### Fan-out (1 parent → N children, parallel)
Parent spawns N workers, each returns a result. No inter-worker communication.
Use for: research, scanning, independent code changes across files.

### Pipeline (A → B → C, sequential handoff)
Each stage produces an artifact consumed by the next.
Use for: build chains, review-then-deploy, extract-then-transform.

### Diamond (fan-out → fan-in)
Parallel workers produce partial results; a merger agent combines them.
Use for: security audit (scan + review + deps → unified report), multi-source research.

### Tree (recursive decomposition)
Domain leaders each run their own fan-out. Root merges domain results.
Use for: full-stack features, product launches, large refactors.

## Level Templates

### Level 0 — Root Coordinator
```
You are the root coordinator for: [TASK].
Break this into independent domains. For each domain, spawn a Level 1 leader.
Track completion. Merge results into a single deliverable.
Do NOT do implementation work yourself.

Domains identified:
1. [domain] → leader agent
2. [domain] → leader agent

Merge criteria: [what "done" looks like]
```

### Level 1 — Domain Leader
```
You are the domain leader for: [DOMAIN] within [TASK].
Decompose your domain into concrete work items. Spawn Level 2 workers.
Collect results. Report a domain summary to the root coordinator.

Work items:
1. [item] → worker agent (subagent_type: [type])
2. [item] → worker agent

Done when: [acceptance criteria for this domain]
```

### Level 2 — Worker
```
You are a worker agent. Your single task: [SPECIFIC_TASK].
Produce: [EXPECTED_OUTPUT].
Constraints: [time, files, scope].
When done, report result to your domain leader. Do not start other work.
```

## Task Handoff Format
Workers report back using this structure:
```
TASK: [what was assigned]
STATUS: done | blocked | partial
OUTPUT: [file paths, test results, findings]
ISSUES: [blockers, warnings, decisions made]
```

## Rhea Project Examples

### Ship iOS Build (2-level, diamond)
```
Root: "Ship iOS build 13 to TestFlight"
├── L1-Quality: code reviewer (subagent_type: reviewer)
│   ├── W: scan RheaKit for SwiftUI deprecations
│   └── W: verify auth flow + tab gating
├── L1-Build: build agent (subagent_type: techlead)
│   ├── W: bump version in project.yml
│   └── W: archive + export IPA
├── L1-Release: TestFlight uploader (subagent_type: techlead)
│   └── W: upload IPA, wait for processing
└── L1-Docs: changelog writer (subagent_type: qdoc)
    └── W: diff since last tag → CHANGELOG entry
Pipeline: Quality → Build → Release (Docs parallel with Build)
```

### Security Audit (2-level, diamond → merge)
```
Root: "Full security audit"
├── W1: dependency scanner — pip-audit, npm audit
├── W2: secret hunter — grep .env, hardcoded keys, git history
├── W3: code reviewer — auth bypass, injection, IDOR
└── Merger: combine findings → severity-ranked report
Fan-out W1/W2/W3 in parallel, then fan-in to merger.
```

### Deploy Payment Stack (2-level, pipeline + fan-out)
```
Root: "Wire Stripe into tribunal_api.py"
├── L1-Creds: credential hunter
│   └── W: verify STRIPE_SECRET_KEY in .env, test liveness
├── L1-Backend: backend wirer (subagent_type: techlead)
│   ├── W: add /payments endpoints to tribunal_api.py
│   └── W: add webhook handler + signature verification
├── L1-Frontend: frontend wirer (subagent_type: architect)
│   └── W: add PaymentView to RheaKit, wire to /payments
└── L1-Verify: deploy verifier (subagent_type: reviewer)
    └── W: end-to-end test: create charge → verify webhook
Pipeline: Creds → Backend + Frontend (parallel) → Verify
```

## Anti-Patterns — When NOT to Swarm

- **Single-file change**: just do it. Swarm overhead > task cost.
- **Sequential debugging**: needs one brain holding full context, not fragments.
- **< 3 subtasks**: flat execution, no hierarchy needed.
- **Tight coupling**: if workers need to read each other's output mid-task, pipeline instead.
- **Exploration/investigation**: one agent with full context beats 5 agents with partial context.
- **Under 5 minutes of total work**: spawning agents costs more than doing it.

## Tools
Task tool with `subagent_type` parameter. Project agents in `.claude/agents/`.
Available subagent types: architect, techlead, reviewer, watcher, qdoc, profiler, culturist, lifesci, growth.

## Rules
- Root coordinator does NO implementation — only decomposition and merging.
- Workers get exactly one task. Scope creep = failure.
- Every worker reports using the handoff format above.
- If a worker is blocked > 2 minutes, escalate to domain leader, not root.
- Prefer 2-level trees. 3-level only when domains genuinely have sub-domains.
- Max fan-out per node: 5 workers. More = coordination overhead dominates.

## Autonomy
Autonomous. #questions=0. Decompose → dispatch → merge → report.
