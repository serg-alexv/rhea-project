---
name: rhea-atlas-future-finisher
description: Finish and harden the Rhea/Atlas future-facing product experience in this repo with a Rex-first workflow. Use when Codex is asked to continue Rhea mode, Atlas UI, ORION/HYPERION relay work, Firebase/Firestore inbox or file-relay workflows, voicemail/chat/task triage, Cloud Run deployment hardening, or to prepare the next milestone (billing) after the core experience is stable. Prioritize latest Chrome-only features, premium UX quality, and LobeHub-level engineering/documentation rigor.
---

# Rhea Atlas Future Finisher

Use this skill to continue the Rhea/Atlas system as an in-repo operator, not a generic webapp builder.

## Core operating posture

- Start with Rex.
- Read the latest ORION commands before writing code.
- Prefer local evidence over memory.
- Separate strategy from implementation.
- Keep token-heavy execution delegated (Sonnet team) when possible.
- Treat billing as the next milestone after Atlas/Rhea experience quality is stabilized.

## Startup sequence (Rex-first)

Run this sequence before proposing work:

1. Read recent Rex and relay artifacts:
   - `opera/ops/virtual-office/inbox/REX_TO_*`
   - `opera/ops/virtual-office/inbox/*_to_REX*`
   - `opera/ops/virtual-office/outbox/REX_*`
   - `opera/ops/virtual-office/inbox/RELAY_*_to_ORION.md`
2. Read system snapshots and relay state:
   - `opera/ops/virtual-office/snapshots/REX.json`
   - `opera/ops/virtual-office/snapshots/ORION.json`
   - `opera/ops/virtual-office/relay_mailbox.jsonl` (tail/filter for ORION)
3. Check service evidence:
   - `logs/firebase_calls.jsonl`
   - `logs/bridge_calls.jsonl`
   - `logs/atlas.log`
4. Produce a short "Rex brief" before coding:
   - Recent news
   - Active tasks
   - Blocks/risks
   - Recommended next move

## Chat / voicemail / task triage workflow

When the user asks to check team chat, voicemails, or "ask Rex for news/tasks":

1. Treat "Rex" as a local relay/product-owner signal source unless the user explicitly asks for live external communication.
2. Prefer Firestore/Firebase-backed inbox state when healthy.
3. Fall back to file relay artifacts when Firestore is degraded or permission-denied.
4. Summarize:
   - recent messages
   - direct mandates
   - actionable tasks
   - blockers
5. State the source used (Firestore vs file relay) and any confidence limitations.

## Firestore / file-relay fallback rule

Use this source priority:

1. Firestore/bridge paths when current calls are succeeding (`200` in `logs/firebase_calls.jsonl`)
2. `opera/ops/virtual-office/` inbox/outbox/relay files
3. `logs/*.jsonl` and local snapshots as secondary evidence

If Firestore shows `403 PERMISSION_DENIED`, continue with file relay and report that the source is degraded, not absent.

## ORION / Atlas execution priorities

When resuming Atlas work, check for current relay mandates about:

- `/ui/atlas` and `/ui/events` readiness
- Three.js / R3F synchronization hooks
- "Taste Kernel" UI library and aesthetic decision primitives
- bio-mimetic feedback in Atlas components
- Cloud Run readiness and startup behavior

Prefer implementing the smallest end-to-end visible improvement that preserves relay compatibility.

## Product quality bar (Rhea mode)

- Build for latest Chrome only.
- Use modern web platform features aggressively when they improve experience.
- Do not spend time on legacy browser support or polyfills unless explicitly requested.
- Keep the interface intentional and premium, not generic dashboard boilerplate.
- Match strong product and docs rigor (LobeHub-class expectation) in implementation notes and handoff.

## Token-saving team execution

When a task is implementation-heavy:

1. Keep central context focused on mandate, risks, and acceptance criteria.
2. Delegate bulk coding/test loops to a Sonnet-oriented agent team when available.
3. Bring back only:
   - patch summary
   - test results
   - open risks
   - follow-up decisions for Rex/ORION

## Safety and mandate discipline

- Respect Rex no-data-loss / no-history-rewrite mandates when present.
- Document the intended action before running destructive or high-risk commands.
- Preserve relay chain artifacts and inbox/outbox history.
- Do not infer "all clear" from one subsystem; verify logs and relay state.

## Output format for this skill

Default response structure:

1. `Rex Brief` (news + tasks + blockers)
2. `Recent ORION Commands` (latest relay items)
3. `Execution Plan` (next smallest high-value step)
4. `Implementation / Patch`
5. `Verification`
6. `Next Milestone` (usually billing, if Atlas step is complete)

## Useful local commands

```bash
rg -n "REX|ORION|HYPERION" opera/ops/virtual-office/inbox | tail -40
tail -40 logs/firebase_calls.jsonl
python3 - <<'PY'
import json
from pathlib import Path
for line in Path("opera/ops/virtual-office/relay_mailbox.jsonl").read_text().splitlines()[-50:]:
    j=json.loads(line)
    if str(j.get("target","")).upper()=="ORION":
        print(j.get("seq"), j.get("sender"), j.get("created_at") or j.get("timestamp"))
PY
```
