# Swarm-First Execution Protocol

Purpose: maximize throughput and reliability by defaulting to agent teams (squads), not single-agent execution.

## Default Rule

- Any `medium+` task is split into subagents immediately.
- Single-agent mode is allowed only for tiny tasks (`<=15 min`) or emergency hotfix.

## Squad Template

- `Lead`: owns final merge, risk calls, investor-facing summary.
- `Builder`: implements code or infra changes.
- `Verifier`: runs checks/tests, looks for regressions.
- `Relay`: keeps pulse updates, tracks acks/timeouts, escalates stale links.

## Hard Constraints

- Each subtask must have: owner, expected output, SLA (timebox), handoff target.
- Every squad run must emit periodic pulse (`<=20 min`) to relay/radio.
- If no ack from a critical target after timeout, trigger fallback path (`pager` + wake).
- Queue never stays with unclaimed P0/P1 tasks.

## Dispatch Checklist

1. Decompose parent task into 3-7 subtasks.
2. Assign owners across available agents (`REX`, `ORION`, `HYPERION`, `GEMINI`, `GPT`, `SHARED`).
3. Start work in parallel.
4. Collect artifacts and verification.
5. Merge and publish compact result + residual risk.

## Health Signals

- `load_balance`: no single agent >60% of active work for long windows.
- `continuity`: no idle gap for active parent task.
- `delivery`: pending relay backlog does not grow unbounded.

## Escalation

- Missing SLA hit: reassign subtask to backup agent.
- Repeated delivery failures: auto-switch to fallback relay path.
- Lead unavailable: promote Builder, continue without stop.
