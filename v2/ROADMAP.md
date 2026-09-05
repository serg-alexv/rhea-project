# Roadmap — Alpha → v1 → v2

**Planning status: DESIGN_ONLY. No milestone is qualified.** The branch name `rhea-project-v2` describes this architecture workstream. Alpha, v1, and v2 below are future qualification and release milestones; they are not version claims for existing legacy modules.

The sequence follows [ASSEMBLY.json](ASSEMBLY.json) and each stage's acceptance gates. Dates will follow evidence and capacity estimates after contract freeze. Later research must not become a prerequisite of the bounded local storage slice.

## First Alpha build — immutable local publication

**Scope: Stage 01 → Stage 02 → Stage 03.** Demonstrate OMNIA-LIT-001 against owned immutable byte buffers in a disposable, host-local, nonsynced store.

The local content-addressed store retains chunk BLOBs, manifests, revisions, the local head, and terminal publication receipts in one SQLite database. Publication uses a qualified WAL transaction, expected revision plus generation comparison, and stable operation identity. Alpha exposes the library and private framed test protocol; it adds no public listener, UI, live filesystem capture, or cloud effects.

| Step | Required result |
| --- | --- |
| [01_contracts](01_contracts/ACCEPTANCE_GATES.md) | CON-01–05 pass: reconcile the two missing normative attachments, freeze canonical bytes, bounds, receipt semantics and public vectors |
| [02_validation](02_validation/ACCEPTANCE_GATES.md) | VAL-01–06 pass: independently implemented encoders, black-box harness, fault fixtures and negative controls are `ORACLE_READY` |
| [03_omnia_lit](03_omnia_lit/ACCEPTANCE_GATES.md) | LIT-01–12 pass against the actual target and deliberate mutants, with complete evidence identities |

Alpha must establish pinned byte-exact reads across restart, at most one distinct publication from one expected head, historical same-ID receipts after later commits, and recovery that preserves every acknowledged revision. It must distinguish contention, conflict, unknown commit outcome, and unavailable state. Actual process kills, injected I/O errors, a qualified storage/VFS power-loss model, deliberate corruption, resource bounds, and the linked SQLite runtime identity are required by LIT-01–12.

**Exit:** an independent controller accepts every required gate for each claimed platform/engine/VFS/fault profile and an immutable evidence manifest identifies the tested artifact. Unsupported LIT-07 withholds Alpha qualification and Stage 04 admission. Successful compilation or process-crash tests alone are narrower results. A storage-model pass is not physical hardware power-loss certification.

## Version 1.0 — stable local desktop system

**Scope: qualified Alpha + Stage 04 → Stage 05.** Provide a local host and native macOS/Windows clients without weakening the data-plane proof boundary.

- [04_local_host](04_local_host/ACCEPTANCE_GATES.md): freeze and implement bounded local IPC, verified endpoint identity, workspace admission, and explicit policy revocation semantics. Proposed transports are macOS XPC and local-only Windows named pipes. The host is the sole application admission boundary to the qualified storage library.
- Isolated supervisor stability: exercise bounded queues and memory, cancellation, disconnects, service restart, request storms, and lost acknowledgements. No legacy HTTP router, model, shell, or routing effect may enter the storage path. The original scoped OperationId survives retry and reconciliation.
- [05_rhea_play](05_rhea_play/ACCEPTANCE_GATES.md): build native macOS and Windows clients through one typed interface. Show verified application receipts, conflict, busy, unknown, unavailable, stale and zero accurately. Pin revision reads and prevent delayed responses from overwriting newer workspace views.

**Exit:** HOST-01–06 and PLAY-01–06 pass independently on each claimed desktop profile, with all applicable LIT regressions intact. The release package must also supply platform-specific installation, signing/distribution, upgrade, and operational recovery evidence; those release checks must be specified and reviewed before calling v1 shipped. Passing architecture gates alone does not distribute a product.

**Scope boundary:** v1 is the qualified local desktop slice. Cleanup, provider dehydration, arbitrary folder capture, symlink/junction mutation and cross-device synchronization remain separate future qualifications. No cleanup or sync promise is inferred from immutable byte publication. iOS remains deferred.

## Version 2.0 — multimodal and cross-node composition

**Scope: qualified v1 + Stage 06 → Stage 07 → Stage 08.** Integrate the full multimodal workflow as observations → advisory proposals → independent admission → domain-owned effects → separate receipts → presentation.

| Stage | Planned capability | Required evidence |
| --- | --- | --- |
| [06_advisory_runtime](06_advisory_runtime/ACCEPTANCE_GATES.md) | Qualify actual native OpenBSD `mbsd/ollama+rheknel` execution in an unprivileged worker; define modality envelopes, model identities and resource budgets | AI-01–06; actual target/model-count evidence, hostile-output denial and timeout/OOM isolation |
| [07_network_executor](07_network_executor/ACCEPTANCE_GATES.md) | Separate privileged helper with fixed typed operations, scoped capabilities, durable intent, fencing and actual-state reconciliation | NET-01–06; disposable native OS tests, drift detection, per-primitive atomicity limits and crash reconciliation |
| [08_remote_bridge](08_remote_bridge/ACCEPTANCE_GATES.md) | Authenticated cross-node RPC and bounded observation/proposal relay; proposed TLS 1.3 mutual authentication with gRPC | RPC-01–08; role mapping, replay/partition/backpressure tests, separate domain receipts and desktop/node regressions |

The combined OpenBSD binary is a research target, not an observed existing capability. A model or a policy function in its address space cannot authorize a mutation. A node certificate is not a desktop owner grant. The bridge may carry only separately frozen, admitted methods; it cannot expose a generic tunnel into local APIs.

Each claimed input modality requires a frozen schema, capture/consent boundary where applicable, resource limits, and negative tests before activation. Multimedia input does not extend LIT to live paths or streams. Broad NDI, RAM/SWAP inspection, Redis/Valkey, iOS, provider replication/eviction, and hardware enablement are optional workstreams with new contracts and gates.

**Exit:** all AI, NET, and RPC gates pass for the exact claimed native and desktop profiles, the multimodal composition has reviewed modality-specific evidence, earlier qualifications remain valid, and release/distribution evidence exists. File and network results retain distinct operation IDs and receipts. There is no distributed all-or-nothing transaction: unresolved external effects stay explicit and compensation is a new authorized operation.

## Promotion and change control

The current baseline has **55 `NOT_EXECUTED` gates**. Only Stage 01 preparation may begin now. `FAIL`, `SKIP`, missing evidence, unsupported required mechanisms, and stale identities withhold promotion. Stage 02 readiness does not assert LIT has passed.

Contracts, independent validators, and production targets have separate ownership. A trusted controller must verify source, contract, validator, binary, engine, platform and fault-model identities, commands, exit statuses, logs, and predecessor receipts. A changed contract or artifact invalidates its affected qualification closure. Future IPC/network freezes are performed before their own stages and do not delay Alpha by expanding LIT.

See the [technical index](docs/INDEX.md) and [LIT-001 draft](docs/TECH_SPEC_LIT_001.md) for source traceability and unresolved freeze inputs.
