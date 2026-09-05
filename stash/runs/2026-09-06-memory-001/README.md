# Typed memory refresh — 2026-09-06-memory-001

This run extends `2026-09-06-cloud-001`. It updates administrative projections and an existing scheduler. It does not recover unavailable WD data or activate legacy memory components.

## Direct findings

- Google Drive is reachable via its connector; `projects` and legacy `rh.1`/`rh.1 copy 2` lineages were resolved. A dedicated preservation folder sits alongside those source trees, not inside their active databases.
- Standalone rhea-memory and embedded store.py share a Git blob at the checked commits. Code access is not live database access.
- Nexus's old permission/test-loop profile and conflicting Redis authority documents need explicit boundaries.
- Several soul.md generations exist. The intended original log.0 was not identified in bounded returned results; similarly named logs were not substituted.
- Existing Repo Conflict Watch updated in place to current v2 scope; hourly cadence/Moscow timezone preserved. See scheduler-change.json.
- No WD/iCloud/Redis runtime access was available. WD bytes freed: 0; reclaimable bytes unknown.

## Records

- [Current compact memory](../../memory/MEMORY.md)
- [Compatibility and source references](../../memory/COMPATIBILITY.md)
- [Scheduler change](scheduler-change.json)
- [Capture manifest](manifest.json)
- [Cloud copy receipt](cloud-receipt.json)

The cloud snapshot contains the prepared memory/protocol files and previously supplied exact evidence bytes, with an internal SHA-256 manifest. It excludes its own subsequent cloud/publication receipts to avoid self-referential hashes. Those receipts are stored separately in this run.

`rhea-memory.json`, `soul.md`, Nexus and log.0 here are scoped administrative projections. Existing source trees and actual memory databases/streams were not rewritten. No qualification gate changed. The existing 41-item/group WD queue remains open; new capability and reclamation requirements are recorded by this refresh.
