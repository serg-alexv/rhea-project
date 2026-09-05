# rhea-project v2

**An AI-driven, immutable-first distributed system architecture with explicit authority boundaries and independently verified state transitions.**

This branch brings storage, native presentation, model advice, network execution, and remote coordination into one staged architecture. AI interprets observations and proposes work. Deterministic admission and the component that owns each state transition decide whether that work may execute.

**Current status: DESIGN_ONLY.** The eight-stage scaffold and documentation are tracked; all 55 acceptance gates remain `NOT_EXECUTED`. Only Stage 01 contract preparation is admitted. The branch name `rhea-project-v2` identifies the architectural workstream, not a released v2 product.

## Start in Trae

Open the repository's [`v2/`](v2/) directory as the IDE workspace. It belongs to this repository; do not initialize another Git repository inside it.

1. Read the [workspace README](v2/README.md) and [Stage 01 handoff](v2/START_HERE.md).
2. Follow the [Alpha → v1 → v2 roadmap](v2/ROADMAP.md).
3. Use the [technical documentation index](v2/docs/INDEX.md) and [LIT-001 specification draft](v2/docs/TECH_SPEC_LIT_001.md).
4. Prepare the Stage 01 contract under its [instructions](v2/01_contracts/AGENTS.md) and [acceptance gates](v2/01_contracts/ACCEPTANCE_GATES.md).

## Problem and first proof boundary

Fragmented modules can disagree about the current revision, acknowledge incomplete writes, or retry an already committed operation as a new mutation. The architecture targets these logical anomalies, race conditions, and silent data corruption through **OMNIA-LIT-001**, a bounded immutable-byte publication slice.

Its proposed local CAS stores content-addressed chunk BLOBs, manifests, revisions, the local head, and terminal publication receipts in **one SQLite database**. WAL transactions with the qualified durability profile enclose publication. A conditional update checks both expected revision and generation; receipt lookup and request-identity verification precede fresh head comparison. Content closure validation and pinned revision reads make corruption detectable and retry results stable.

These are obligations to implement and test. WAL alone does not prove correctness, qualify a filesystem, or make network and storage effects atomic. The initial slice accepts owned immutable bytes, has no network listener, and performs no user-path, symlink, cloud-provider, model, or routing operations. Its Rust implementation remains additive in the existing Omnia supervisor; Stage 03 here records that source boundary.

## Component map

Numbering defines assembly and proof order. It does not grant runtime authority.

| Stage | Responsibility | Qualification required to advance |
| --- | --- | --- |
| [01_contracts](v2/01_contracts/) | Evidence identities, bounded LIT contract, public vectors; later domain contracts frozen separately | CON-01–05: reviewed contract freeze |
| [02_validation](v2/02_validation/) | Independent encoders, black-box oracles, fault injection and evidence verification | VAL-01–06: oracle readiness |
| [03_omnia_lit](v2/03_omnia_lit/) | Source/assembly boundary for the isolated Omnia immutable data plane | LIT-01–12: qualified local publication and recovery |
| [04_local_host](v2/04_local_host/) | Host identity, admission, private storage access and bounded local IPC | HOST-01–06: scoped admission and service stability |
| [05_rhea_play](v2/05_rhea_play/) | Native macOS/Windows presentation through one typed client contract | PLAY-01–06: honest state and desktop end-to-end evidence |
| [06_advisory_runtime](v2/06_advisory_runtime/) | Isolated model/rheknel proposals; native OpenBSD research qualification | AI-01–06: actual execution and non-authorizing isolation |
| [07_network_executor](v2/07_network_executor/) | Separate privileged helper, fixed network operations, durable intent and reconciliation | NET-01–06: scoped native effects and failure recovery |
| [08_remote_bridge](v2/08_remote_bridge/) | Authenticated cross-node RPC, bounded relays and explicit domain composition | RPC-01–08: independent composition and regression evidence |

## Orchestration rules

- The local host owns admission to the qualified storage library. The UI receives typed results and pinned reads; it cannot reach the database, routing primitives, shell, or model transports directly.
- Proposed local transports are macOS XPC, local-only Windows named pipes, and OpenBSD Unix-domain sockets. Each requires its own identity and denial tests before activation.
- The model worker has no storage handle, owner credentials, node private key, or routing authority. Model output is a proposal, never a capability.
- Network state has its own operation ledger, node epoch, and route generation. A file receipt cannot assert that a route was applied.
- The proposed remote bridge uses mutually authenticated TLS with bounded typed RPC. Node authentication does not become desktop owner authorization. Partial workflows retain separate receipts and explicit unresolved outcomes.

The complete selected design is in [ARCHITECTURE.txt](v2/ARCHITECTURE.txt); executable enforcement remains unimplemented.

## Evidence and release discipline

The design references [99 structural records](v2/01_contracts/evidence/rhea_semantic_core.json), the [source registry](v2/01_contracts/evidence/source_registry.json), and the adversarial review [recomb1.md](v2/01_contracts/evidence/recomb1.md). The reported 5,348-file extraction is coverage context, not 5,348 verified behaviors.

The detailed `OMNIA-LIT-001_HANDOFF.md` and `OMNIA-LIT-001_ACCEPTANCE.json` referenced by that review are not bundled. Their reconciliation blocks contract freeze; this specification draft does not replace them. Only an independent validation controller may accept evidence and promote the [assembly state](v2/ASSEMBLY.json).

Existing root source trees and legacy documentation remain historical context, excluded from new target builds. Earlier installation instructions and product claims are available in the [frozen baseline README](https://github.com/timelabs-npo/rhea-project/blob/75cb31e59ccc4f436a428811cb70bbc495254821/README.md); they do not describe this branch's v2 qualification.
