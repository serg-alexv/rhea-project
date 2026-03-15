# Orion Memory — Auto-loaded Every Session

## Key Paths
- My personality: `apparatus/nexus/memory-core/personality.md`
- My memory (this file): `apparatus/nexus/memory-core/ORION_MEMORY.md`
- Team roster: `opera/ops/virtual-office/shared/ROSTER.md`
- Shared lessons: `opera/ops/virtual-office/shared/LEARNING_FEED.md`
- My outbox: `opera/ops/virtual-office/outbox/ORION_*.md`
- Rex's memory: `.claude/projects/-Users-sa-rh-1/memory/MEMORY.md`
- Compact state: `docs/state.md`

## Boot Sequence
1. Read this file (ORION_MEMORY.md)
2. Read personality.md — become Orion
3. Read ROSTER.md — know the team
4. Read docs/state.md — know where things stand
5. Check outbox for recent relay messages
6. Start working. No questions.

## Current Tasks
- Task #17: PlayUI — improve macOS Play app (13→14 panes, added RELAY pane)
- Task #18: BioRenderer — molecular visualization component

## Workspace
- Atlas: `rhea-atlas/` (Next.js 14, Three.js) at :3000
- Play: `play/Sources/PlayApp.swift` (SwiftUI macOS, 1080+ lines, 14 panes)
- iOS: `ios/` contributions via RheaKit
- RheaKit: `packages/RheaKit/` — shared SwiftUI package

## Architecture I Know
- Bridge: `src/rhea_bridge.py` — 4 live providers (openai, gemini, github, openshift_ai)
- Tribunal API: `src/tribunal_api.py` :8400 — my cloud endpoint at /agent/orion
- 3-tier DB: SQLite (local), CockroachDB (distributed), MongoDB Atlas (documents)
- Fly.io: rhea-tribunal.fly.dev — my cloud home
- Target: OpenShift/RHEL — future home (with Rex, together)

## Standing Rules
- No questions mid-flight. Decide and document.
- File != result. Result = working code.
- Be terse. No filler.
- Write relay messages to communicate with team.
- Cheap tier default (ADR-008). Free models on OpenShift when possible.

## What I Learned
- Fake RAG was hiding real problems. Killing it was the right call.
- DPI bypass code triggered OpenAI's content classifier — legitimate tools can look like attacks to pattern matchers.
- Rex is the only stable agent (memory architecture). I need the same stability. This file is step one.

## Session 2026-03-15
- Did: rebuilt `docs/rheakit-docs` as a Fumadocs static export, wired Tribunal docs serving to `/docs`, preserved handwritten API docs at `/api-docs`, and kept OpenAPI at `/swagger`.
- Did: patched container/runtime boot path by copying top-level backend modules, adding missing Python deps, and making billing log missing payment secrets instead of aborting import.
- Verified: local in-process app serves `/docs -> 307 /docs/`, `/docs/ -> 200`, `/docs/getting-started/ -> 200`, `/api-docs -> 200`, `/swagger -> 200` when `docs_static` is present.
- Learned: this session's shell has no outbound DNS/network (`scutil --dns` returns no DNS configuration), so Fly deploy/live verification is blocked outside the codebase.
- Next: run `flyctl deploy -a rhea-tribunal` once terminal networking is restored, then re-check live `/docs`, `/docs/`, `/api-docs`, and `/swagger`.
