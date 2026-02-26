# PROJECT RESTRUCTURE NOTICE — FROM REX
> From: Rex (Product Owner) | Date: 2026-02-26 | Priority: P1

## What's Happening

Full directory restructure in progress. The root directory is being reorganized from 34 items to 14.

## Key Changes

### New Top-Level Directories
- `emergentia/` — Human input drop zone (experiments, PDFs, knowledge bricks)
- `opera/` — System output (agent artifacts, logs, metrics, cache)
- `apparatus/` — System core (consolidates all rhea-* dirs: elementary, nexus, commander, advanced, applied, extensions)
- `friends/` — Referenced traditions (aletheia/ for truth & rigor, ruliad/ for exploration & computation)
- `plugins/` — All integrations (bridges, connectors, MCP, third-party)
- `config/` — Deployment & bootstrap (docker, firebase, fly, railway)

### Moved Locations
- `rhea-elementary/` → `apparatus/elementary/`
- `rhea-nexus/` → `apparatus/nexus/`
- `rhea-commander-stack/` → `apparatus/commander/`
- `rhea-advanced/` → `apparatus/advanced/`
- `rhea-applied-backlog/` → `apparatus/applied/`
- `rhea-chrome-extension/` → `apparatus/extensions/`
- `rhea-ontology-explorer/` → `friends/ruliad/explorer/`
- `logs/` → `opera/logs/`
- `metrics/` → `opera/metrics/`
- `users/` → `opera/cache/`
- Root deploy configs → `config/`
- `team/` → `apparatus/nexus/` (agent definitions merged)
- `nexus/` (stale stub) → `archive/`

### Hard Separation Rule
- `emergentia/` = HUMAN writes, system reads
- `opera/` = SYSTEM writes, human reviews
- Never cross-contaminate.

### What Stays Unchanged
- `docs/` — same location
- `assets/` — same location
- `archive/` — same location
- `scripts/` — same location
- `src/` — same location
- `tests/` — same location
- `ops/virtual-office/` — same location (agent relay system untouched)

## Action Required

All agents: update your file path references on next boot. If you wrote to a path that moved, check this notice for the new location.

Relay chain and inbox/outbox system are UNTOUCHED.

**Rex signing off.**
