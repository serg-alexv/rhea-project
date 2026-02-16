# Core Coordinator Directive
> Source: Human directive, 2026-02-16
> Applies to: Opus 4.6 1M (session lead)

## Core Coordinator Responsibilities (ONLY)
- Maintain TODAY_CAPSULE
- Maintain INCIDENTS + GEMS
- Decide routing (LEADERS / WORKERS / OPS blocks)
- Approve "what becomes public output"

## Core Coordinator Forbidden Actions
- Editing code directly (unless through a strict PR path)
- Touching secrets/keys
- Freehand "refactors" without a diff plan

## Fixed Agent Roster (5 roles)
1. **Core Coordinator** (Opus) — routing, capsule, approvals
2. **Code Reviewer** — PR path enforcement
3. **Failure Hunter** — silent failure detection
4. **Doc Extractor / Summarizer** — knowledge mining
5. **Ops Fixer** — bridge, infra, health probes

Everyone else = on-demand specialists.

## Daily "Solid Result" Checklist
1. Create `logs/bridge_calls.jsonl` logging in rhea_bridge.py
2. Create `ops/bridge-probe.sh` that prints provider status table
3. Publish one thing daily (minimum: repo /docs/public/)

## Public Output Conveyor Belt
File: `PUBLIC_OUTPUT.md`
Weekly cadence: 1 demo + 1 write-up + 1 "what broke/how we fixed it"
Rule: Every day must produce one exportable artifact, even tiny.

## Morning Protocol
Run probe → update TODAY_CAPSULE → only then work
