# Protocol Discovery

## Operating protocols discovered
- System/developer/user runtime instructions are highest authority in current session.
- Workspace protocol documents detected: `CLAUDE.md`, `prompts/AUTONOMY_WITH_AUDIT_ROOT.md`, `prompts/STICKY_CONTEXT.md`, `protocols/ORION_INCIDENT_ESCALATION.md`, `.windsurf/workflows/review.md`, `.roomodes`, `.roo/mcp.json`, `REDIS_SCHEMA.md`.
- AGENTS governance files found: `.codex/AGENTS.md`, `friends/codex-cli/AGENTS.md` (scoped to their directory trees).

## Authoritative instruction/rule stack (practical)
1. Session runtime directives (system/developer/user prompts).
2. Workspace root protocols: `CLAUDE.md`, root prompt + sticky context in `prompts/`.
3. Mode-specific rules in `.roomodes` and workflow constraints in `.windsurf/workflows/review.md`.
4. Directory-scoped AGENTS files for subtrees only.

## Modes/orchestrators currently available
- Custom mode slugs detected in `.roomodes`: rhea-project, rheakit, rhea-balancer, rheacli, rheacockpit, rheaconnectors, project-research, devops, google-genai-developer, documentation-writer, rhea-memory.
- Chronos/tribunal/orchestration references present across prompts and virtual-office docs; relay paths and outbox protocols are defined.

## Existing memory/state/index discipline already implemented
- Compact state discipline: `docs/state.md` size cap and check hooks referenced in root prompts.
- Multi-layer memory model: `MEMORY.md`, `docs/state.md`, `docs/state_full.md`, snapshots (`.entire/`), relay outbox/inbox protocols.
- Redis keyspace schema in `REDIS_SCHEMA.md` establishes structured state keys and TTL conventions.
- Naming conventions visible: `rhea:*` Redis keys, outbox file patterns, protocol docs versioning.

## Resume/checkpoint conventions detected
- Checkpoint cadence explicitly defined in `prompts/AUTONOMY_WITH_AUDIT_ROOT.md` (micro/task/consolidation).
- Evidence-first and artifact-based continuity enforced by sticky context + office protocol references.

## Adaptation for this run
- Adapted to existing protocol stack; no override performed.
- Read-first, artifact-writing workflow used; outputs constrained to `_inventory/`.
- Secrets are redacted in generated summaries; credential-bearing config values are not reprinted.

## Execution topology available now
- Local terminal execution + file system write access in workspace.
- MCP topology configured for context7/filesystem/sequentialthinking/fetch/sqlite/redis-cloud/firebase (+ qdrant configured but disabled).
- Multi-mode orchestration available through `.roomodes` (project, devops, memory, connectors, etc.).
