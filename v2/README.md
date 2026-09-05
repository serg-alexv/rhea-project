# rhea-project v2 workspace

**An AI-driven, immutable-first distributed system architecture.** This is the active workspace for the `rhea-project-v2` branch. The [repository overview](../README.md) contains the full vision and component map.

The first task is to make immutable byte publication, local head advancement, and its terminal receipt one qualified SQLite WAL transaction in OMNIA-LIT-001. That bounded proof addresses concurrent publication, ambiguous responses, and detectable content corruption before UI, inference, routing, or remote coordination can depend on it.

**Status: DESIGN_ONLY.** All 55 gates are `NOT_EXECUTED`. Only Stage 01 contract preparation is admitted; Stage 02–08 implementation is locked. A documentation commit or successful push changes none of those states.

## Reading order

1. [START_HERE.md](START_HERE.md) — local Trae paths, Git arrangement, and the immediate handoff.
2. [AGENTS.md](AGENTS.md) and [Stage 01 instructions](01_contracts/AGENTS.md) — work boundaries.
3. [ROADMAP.md](ROADMAP.md) — Alpha, v1, and v2 scope and evidence requirements.
4. [docs/INDEX.md](docs/INDEX.md) — technical reading map and outstanding specifications.
5. [docs/TECH_SPEC_LIT_001.md](docs/TECH_SPEC_LIT_001.md) — draft publication, receipt, and recovery model grounded in [recomb1.md](01_contracts/evidence/recomb1.md).

## Assembly sequence

| Stage | Owns | Exit gate family |
| --- | --- | --- |
| [01_contracts](01_contracts/) | Contract identities and public vectors | CON-01–05 |
| [02_validation](02_validation/) | Independent oracles and fault models | VAL-01–06 |
| [03_omnia_lit](03_omnia_lit/) | Omnia source binding and local immutable publication qualification | LIT-01–12 |
| [04_local_host](04_local_host/) | Local admission and IPC | HOST-01–06 |
| [05_rhea_play](05_rhea_play/) | Typed native desktop presentation | PLAY-01–06 |
| [06_advisory_runtime](06_advisory_runtime/) | Isolated model proposals and OpenBSD research | AI-01–06 |
| [07_network_executor](07_network_executor/) | Independently authorized native network effects | NET-01–06 |
| [08_remote_bridge](08_remote_bridge/) | Authenticated, bounded cross-node composition | RPC-01–08 |

The order is a selected engineering design, not a demonstrated unique global optimum. [ARCHITECTURE.txt](ARCHITECTURE.txt) distinguishes proof dependencies from scheduling choices and proposed transports. Later stages are never dependencies of the initial LIT implementation.

## Stage 01 deliverable

Reconcile the missing `OMNIA-LIT-001_HANDOFF.md` and `OMNIA-LIT-001_ACCEPTANCE.json`, freeze the exact bounded contract, and submit its identity and public vectors for independent review under [CON-01–05](01_contracts/ACCEPTANCE_GATES.md). The technical draft records unresolved canonical encodings and bounds; it is not authority to invent them or declare freeze.

The real Rust LIT code will stay additive in an Omnia supervisor worktree from commit `f5995536fede02d403f0525ff9093996457efecb`, as recorded by [03_omnia_lit/SOURCE.json](03_omnia_lit/SOURCE.json). This workspace does not migrate that implementation or activate existing legacy entrypoints.

`ASSEMBLY.json`, stage `STATUS.json` files, and acceptance documents must remain consistent. The independent controller verifies executable evidence before promotion; instructions and folder boundaries alone provide no runtime isolation.
