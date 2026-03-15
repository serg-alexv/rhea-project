# Preflight

## Available tools and capabilities
- Session tools: filesystem read/write, semantic search, regex search, command execution, patch application, image tools, todo tracking, mode/task orchestration.
- Terminal mode verified: macOS Darwin arm64 (`uname -a` captured).
- Filesystem capability: recursive scan + artifact generation under `_inventory/`.

## Verified accessible paths
- Top-level entries detected: 151
- Writable check (sample):
  - `.DS_Store`: writable
  - `.claude`: writable
  - `.codex`: writable
  - `.dockerignore`: writable
  - `.entire`: writable
  - `.env`: writable
  - `.env.example`: writable
  - `.firebase`: writable
  - `.firecrawl`: writable
  - `.gcloudignore`: writable
  - `.gemini`: read-only/unknown
  - `.git`: writable
  - `.github`: writable
  - `.gitignore`: writable
  - `.gitmodules`: writable
  - `.next`: writable
  - `.obsidian`: writable
  - `.pids`: writable
  - `.playwright-mcp`: writable
  - `.rhea`: writable
  - `.roo`: writable
  - `.roomodes`: writable
  - `.secrets`: writable
  - `.tmp_music`: writable
  - `.venv`: writable
  - `.vscode`: writable
  - `.watcher`: writable
  - `.windsurf`: writable
  - `.windsurfignore`: writable
  - `11march-full-audit-p0leftovers.md`: writable
  - `2 помоги мне доказать, что sqlite устарела и _это самая устойчивая идея_ это манипуляция, а не аргумент - Google Search.mhtml`: writable
  - `:memory:`: writable
  - `CHECK.md`: writable
  - `CLAUDE.md`: writable
  - `Dockerfile`: writable
  - `FINAL_DELIVERY.md`: writable
  - `INTERAGENT_COMM_GUIDE.md`: writable
  - `LATEST.json`: writable
  - `LICENSE`: writable
  - `MULTITEAMLOOP_PLAN.md`: writable

## Connector/MCP status
- `context7`: enabled; command=ok; connectivity=not-tested; credential env keys=DEFAULT_MINIMUM_TOKENS
- `filesystem`: enabled; command=ok; connectivity=not-tested; credential env keys=none-in-env-block
- `sequentialthinking`: enabled; command=ok; connectivity=not-tested; credential env keys=none-in-env-block
- `fetch`: enabled; command=ok; connectivity=not-tested; credential env keys=none-in-env-block
- `sqlite`: enabled; command=ok; connectivity=not-tested; credential env keys=none-in-env-block
- `redis-cloud`: enabled; command=ok; connectivity=reachable; credential env keys=none-in-env-block
- `qdrant`: disabled; command=ok; connectivity=reachable; credential env keys=QDRANT_API_KEY
- `firebase`: enabled; command=ok; connectivity=not-tested; credential env keys=none-in-env-block

## Mode/orchestrator/team availability
- `.roomodes` custom modes detected: rhea-project, rheakit, rhea-balancer, rheacli, rheacockpit, rheaconnectors, project-research, devops, google-genai-developer, documentation-writer, rhea-memory.
- Workflow/orchestrator docs present in `.windsurf/workflows/` and virtual-office protocol files.

## Credential requirements detected now
- context7: env DEFAULT_MINIMUM_TOKENS
- qdrant: env QDRANT_API_KEY
- Redaction policy applied: secrets/tokens are not copied into inventory artifacts.

## Blockers
- Referenced file missing: docs/CORE_RULES.md (referenced by CLAUDE.md and protocol docs)

## What can proceed with zero further questions
- Full filesystem inventory and corpus classification.
- Correlation mapping across firebase/ui/docs/reverse/config/session corpora.
- Metadata extraction preparation artifacts (JSON key-frequency, manifesting).

## Recommended execution topology
- Single-pass scan -> corpus classification -> correlation map -> metadata extraction prep.
- Keep writes in `_inventory/` only to avoid logic mutation.
