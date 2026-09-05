# Start here — Trae Stage 01

Open this directory as the IDE workspace:

`/Users/sa/Documents/Codex/rhea-v2-workspace/v2`

Git root is the parent directory. The branch is `rhea-project-v2`.
Do not run `git init` inside v2: it already belongs to that branch.
The repository metadata/object store is in `/Users/sa/Documents/Codex/rhea-project`.
Keep that repository while this linked worktree is in use.

## Current admission

DESIGN_ONLY. Only Stage 01 contract preparation is admitted. All 55 proof gates
remain NOT_EXECUTED; Stage 02 through Stage 08 implementation remains LOCKED.
Scaffold preparation and its Git commit are not contract or product qualification.

Read `AGENTS.md`, `01_contracts/AGENTS.md`,
`01_contracts/ACCEPTANCE_GATES.md`, and `ARCHITECTURE.txt` first.

## Stage 01 inputs and next work

- `01_contracts/evidence/rhea_semantic_core.json`: the structural dictionary.
- `01_contracts/evidence/recomb1.md`: the adversarial review.
- `01_contracts/evidence/source_registry.json`: source locations and identities.
- `01_contracts/evidence/evidence/`: bundled local evidence receipts and reports.
- `01_contracts/evidence/extraction_manifest.json`: expanded extraction inventory.
- `03_omnia_lit/SOURCE.json`: actual verified local Omnia source location.

Prepare the bounded OMNIA-LIT-001 contract. Reconcile the detailed
`OMNIA-LIT-001_HANDOFF.md` and `OMNIA-LIT-001_ACCEPTANCE.json` referenced by
recomb1.md before declaring CON-02 or the contract freeze passed. Those two
normative attachments are not supplied in this scaffold; do not invent their
canonical byte format or silently mark the prerequisite complete.

Do not start production implementation, legacy entrypoints, UI, models, routing,
provider integration, replication, eviction or symlink mutation during Stage 01.
The later Rust implementation remains additive inside Omnia supervisor in a
separate worktree from f5995536fede02d403f0525ff9093996457efecb.

## Scaffold script

`scaffold-v2.sh` was extracted from the user's tad1.md. Its Python SHA-256 and
fixed-record-count preflight block was removed as requested. It retains basic
readable/nonempty-file checks, Git baseline checks and manifest generation.
It is an audit/reproduction artifact; rerunning against this existing destination
will refuse to overwrite it.

This preparation is local only. No remote push or product build was performed.
