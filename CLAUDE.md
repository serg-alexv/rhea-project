# Rhea Project — Claude Context

## Project
- Codename: Rhea — multi-model advisory system (chronobiology + control theory)
- Root: `/Users/sa/rh.1` | Branch: `main`
- Core rules: `docs/CORE_RULES.md` | Root prompt: `prompts/AUTONOMY_WITH_AUDIT_ROOT.md`

## Key Files
- `docs/state.md` — compact working state (MUST stay under 2KB, enforced by check.sh)
- `docs/state_full.md` — append-only narrative log
- `src/rhea_bridge.py` — multi-provider LLM bridge (6 providers, 31 models, 4 tiers)
- `scripts/rhea_orchestrate.py` — 8-agent orchestration (Chronos Protocol v3)
- `docs/INTEGRATIONS_AUDIT.md` — tool registry (92 integrations)

## Scripts
- No `rhea` CLI in PATH — call scripts directly: `bash scripts/rhea/check.sh`
- `scripts/rhea_commit.sh` — ALWAYS use instead of raw `git commit` (ADR-013)
- `scripts/rhea_autosave.sh` — snapshot + commit + push
- `scripts/memory_benchmark.sh` — self-test (73 checks across 5 memory layers)

## Constraints
- `docs/state.md` <= 2048 bytes (check.sh enforces, FAIL if exceeded)
- Entire.io strategy: `auto-commit` (ADR-014) via `.entire/settings.local.json`
- All hooks route through `entire hooks claude-code <event>`
- Budget-aware: cheap tier default, escalate only when justified (ADR-008)
- Tribunal required for: memory policy, checkpoint policy, permission changes, build mods

## Testing
- `bash scripts/rhea/check.sh` — repo invariants (state.md size, .venv/.env not tracked)
- `bash scripts/memory_benchmark.sh` — full memory layer self-test
- `python3 src/rhea_bridge.py status` — provider/key availability
- `python3 src/rhea_bridge.py tiers` — tier configuration and availability

## Decisions
- 14 ADRs in `docs/decisions.md`
- 2 completed tribunals in `docs/tribunal_*.md`
