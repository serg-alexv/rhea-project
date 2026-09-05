# OMNIA-LIT-001 — Local Immutable Publication

**Status: DRAFT / DESIGN_ONLY.** This document describes the first bounded
implementation slice. It records no executed product tests and confers no
qualification. Every LIT gate remains `NOT_EXECUTED`.

The controlling review is [recomb1.md](../01_contracts/evidence/recomb1.md),
especially sections 1.B–1.G and 2–4. The stage-specific obligations are
[contract freeze](../01_contracts/ACCEPTANCE_GATES.md),
[independent validation](../02_validation/ACCEPTANCE_GATES.md), and
[LIT qualification](../03_omnia_lit/ACCEPTANCE_GATES.md).

The review references `OMNIA-LIT-001_HANDOFF.md` and
`OMNIA-LIT-001_ACCEPTANCE.json`; neither is included in the scaffold evidence.
Those inputs must be retrieved and reconciled, or explicitly replaced by a
reviewed frozen contract, before CON-02 and contract freeze can pass. This draft
does not substitute invented byte layouts for the missing attachments.

## 1. Objective and scope

Publish an owned immutable byte buffer into a local content-addressed store
(CAS), atomically advance one local revision head, persist the corresponding
terminal operation receipt, and recover or read the published content under
specified failure schedules.

The physical commit unit is **one SQLite database transaction** containing
chunk BLOBs, manifests, revisions, the local head and the operation receipt.
Content-addressed storage is logical inside this database; the initial slice
has no external object files or separate filesystem publication step.

The logical head authority is scoped to a workspace and replica. This is a
local publication boundary, not a global distributed transaction service.
The retained root is a flat map of opaque item identifiers. It supplies no
directory, filename, ACL, extended-attribute or resource-fork semantics.

An owned buffer proves which captured bytes were published. It does not prove
that a changing live file was captured at one coherent instant. Fixtures must
be generated, disposable data rather than live user paths.

Excluded from this slice:

- HTTP or socket listeners, legacy Node and supervisor mutation entrypoints,
  shell execution and caller-supplied filesystem paths.
- External CAS files, symlink replacement, native projection, provider upload,
  dehydration, eviction, garbage collection and history pruning.
- Models, Rheknel, OpenBSD routing, UI, Redis, replication and remote RPC.
- Projection, replication or eviction fields inside the local receipt state.

The implementation is an additive Rust library and test-facing executable in
an isolated worktree of the existing Omnia supervisor project, rooted at
`f5995536fede02d403f0525ff9093996457efecb`.
[03_omnia_lit](../03_omnia_lit/AGENTS.md) owns the assembly manifest here; it
does not relocate the storage implementation into this umbrella repository.
The validator communicates over a private framed stdin/stdout test protocol.
Its exact framing must be frozen before use. Stages 04–08 are never build or
runtime dependencies of this target.

## 2. Contract surface and authority

| Operation | Meaning and constraints |
| --- | --- |
| `PublishItemBytesV1` | Accept owned bytes, an operation identifier, workspace, replica, item, expected revision and generation, and claimed content-manifest identity. Verify that the submitted bytes reproduce the claimed identity. |
| `GetHead` | Return an authorized, scoped observation of the local head. An observation is not a publication receipt. |
| `GetOperation` | Authorize receipt access, then return the recorded historical outcome for the scoped operation, if one is established. |
| `ReadItem(revision_id, item_id)` | Read from an explicitly pinned retained revision and verify the referenced content. Do not silently substitute the current head. |

Actor identity comes from trusted host-owned context; a request cannot select
an owner by setting a field. Authorization is required before disclosing an
operation receipt, head or item bytes. Stage 04 will separately qualify OS
identity, IPC admission and policy-revocation mechanics; they are not assumed
to exist in this library or its isolated test harness.

`ChunkId`, `ManifestId`, `RevisionId`, `OperationId` and `Generation` are distinct
types. Transport serialization does not define content identity. Exact
canonical encoding, hash algorithm/domain separators, field widths and
serialization rules remain subject to the missing normative contract.

The request digest must bind the operation's meaning: owner, workspace,
replica, item, expected revision and generation, and verified content
identity. The exact operation-key scope and digest byte representation must
be frozen. A digest of an unverified caller claim is insufficient.

## 3. Logical data model and invariants

This is a logical model, not an approved table schema or migration.

| Record family | Required property |
| --- | --- |
| Chunk BLOBs | Immutable bytes addressed by the frozen chunk identity. Reuse requires verification; a matching identifier with different bytes is corruption. |
| Manifests | Immutable, canonically identified content descriptions with validated ordered references. Exact empty-input and chunk-order rules await freeze. |
| Revisions | Immutable root descriptions with valid parent relationships and content closure. Updating one item preserves the other items and older retained revisions. |
| Local head | One authoritative revision and generation for the workspace/replica scope; new publication compares both expected values. |
| Terminal operation ledger | Scoped operation identity, bound request meaning and canonical historical receipt, committed with the published revision. |

Let `H` be a scoped head, `r` a revision, and `closure(r)` its valid referenced
manifests and bytes. The target invariants are:

```text
One logical head authority exists per workspace/replica scope.

distinct successful publications from the same expected (revision, generation)
    <= 1

published(r) => complete and valid closure(r)

ACK(r) => readable(r) and head is r or a valid descendant of r

retry(scoped OperationId, same request meaning)
    => the original historical receipt

retry(scoped OperationId, different request meaning)
    => reject operation-ID reuse
```

Publication linearizes at successful commit of the transaction containing the
conditional head update and receipt. The conditional update alone is not an
externally acknowledged publication. A process-local mutex alone cannot prove
the competing-process compare-and-swap obligation.

## 4. Write transaction model

The review establishes the order below. `BEGIN IMMEDIATE` is a proposed SQLite
mechanism for acquiring serialized write access; this draft does not freeze
SQL statements, table layouts, retry timing or error-code mappings. Whatever
mechanism is selected must satisfy the same observable ordering and gates.

1. **Validate and authorize.** Establish host identity and requested scope;
   enforce bounded, well-typed input and receipt-access authorization. Capture
   owned immutable bytes, compute the contract-defined content identity,
   verify the claimed identity, and derive the request digest. Do not perform
   external effects or emit durable acceptance.
2. **Acquire a scoped write decision inside a database transaction.** The
   operation-ledger decision and fresh expected-head decision must share the
   serialized transaction context. A prior read-only lookup is only an
   optimization and cannot authorize a new write without rechecking.
3. **Resolve the scoped operation ID first.** If a record exists, compare its
   stored request digest. On equality return the exact recorded historical
   receipt after safely ending the lookup transaction. On mismatch reject ID
   reuse. Neither branch performs a new publication or reevaluates the old
   request as a fresh expected-head compare-and-swap.
4. **Evaluate the fresh expected head.** For an unrecorded operation, compare
   both expected revision and expected generation against the authoritative
   scoped head in this transaction. A confirmed mismatch is `CONFLICT`.
5. **Validate closure and capacity.** Verify the existing and candidate
   content closure, including reused chunks, manifests and parents. Apply
   root, payload, receipt and generation bounds for the new work. Do not let
   new-work quota checks invalidate the historical-retry path in step 3.
6. **Insert immutable publication records.** Insert the necessary chunks,
   manifests and revision under the frozen identity and parent rules. The
   revision's parent is the expected head. Never overwrite an existing object
   whose identifier has incompatible bytes; report corruption.
7. **Advance head and record the receipt together.** Conditionally update the
   scoped head using both expected values. Verify that the expected update
   occurred. Insert the canonical terminal receipt for this operation in the
   same transaction. Its fields describe this operation's historical result,
   not a later `GetHead` observation.
8. **Commit.** All content records, the head transition and terminal receipt
   commit together or are not published together. Database errors require
   inspection and recovery of actual transaction state; an ambiguous error
   does not establish rollback.
9. **Acknowledge only after successful commit.** Emit `LOCAL_COMMITTED` only
   after commit success under the verified engine and durability profile.
   The independent parent must receive the complete acknowledgement for the
   post-ACK oracle to apply.

For illustration, a successful operation may expect generation 7 and publish
generation 8, then lose its reply. A retry with its original expected
generation 7 returns the stored generation-8 receipt, even when another
operation has since published generation 9. Returning a conflict or rebuilding
the receipt from generation 9 would violate retry identity.

There are no external pre-commit effects and no asynchronous durable
`ACCEPTED` promise. Consequently this slice needs no separately durable
pre-commit intent ledger. Future external-object or provider effects require
a separately reviewed intent/reconciliation contract.

## 5. Receipts, errors and uncertain outcomes

The successful receipt is generated from the transaction's validated
historical publication result and persisted with it. Insertion inside an
uncommitted transaction does not authorize emission of `LOCAL_COMMITTED`.
The exact canonical receipt layout and serialization await contract freeze.

| Result or observation | Required interpretation |
| --- | --- |
| `LOCAL_COMMITTED` | The local publication and its receipt committed successfully under the qualified profile. It makes no projection, remote-recoverability or hardware claim. |
| Historical receipt | Return the original record for an authorized identical retry, even after later head changes. Do not reconstruct it from current state. |
| `BUSY` | Lock contention prevented the required write decision. This does not prove an expected-head mismatch. |
| `CONFLICT` | The expected revision/generation was examined in the required transaction context and did not match. |
| `OUTCOME_UNKNOWN` | A storage, commit or response failure leaves the operation's result unresolved. Preserve the original operation ID and reconcile. |
| Unavailable state | A requested observation could not be established. Do not replace it with zero, an empty success object or an invented rejection. |
| Corruption detected | Stored identity, references or bytes are inconsistent. Do not overwrite the evidence, reset history, silently roll back or claim repair. |

These are semantic distinctions, not a frozen response union. This draft does
not decide whether rejected operations receive durable terminal records, their
retention behavior, or their exact response codes. Those details must be
reconciled with the missing contract and acceptance attachment.

For an ambiguous outcome:

1. Preserve the same scoped operation ID and original request meaning.
2. Establish the database's recovered, usable transaction state using the
   tested engine and fault profile.
3. Authorize and consult the operation ledger. If the result is established,
   return the original receipt. If recovery establishes that the operation
   did not publish, an identical retry can enter the normal transaction path.
4. If the state cannot be established, retain `OUTCOME_UNKNOWN`. An error,
   failed connection or incomplete read is not proof that a receipt is absent.

A successful process exit, transport delivery, checkpoint or current head
observation cannot replace a terminal operation receipt. A lost reply does
not authorize minting a new operation ID.

## 6. Recovery and read oracles

The independent validator, not the target's own marker, determines whether a
complete acknowledgement was received. A partial or truncated frame does not
count as an ACK. Fault schedules exercise content, manifest, head, receipt,
commit, acknowledgement and checkpoint/reopen boundaries.

| Boundary or fault | Required oracle |
| --- | --- |
| No complete ACK observed | Recovery may expose the old or new **complete** publication state for the tested transition. No dangling head, missing committed receipt or incomplete content closure is permitted. |
| Complete ACK observed | The acknowledged revision and bytes remain readable. The head is that revision or a valid descendant established through valid parent relationships. |
| Later successful publications | Older pinned revisions remain readable and item updates preserve unrelated root entries. |
| Lock contention or capacity exhaustion | Preserve all earlier acknowledged revisions; distinguish retryable contention from examined state conflict. |
| Process termination | Test actual process death and restart. This establishes only the corresponding process-crash behavior. |
| Write, sync, I/O or disk-full fault | Do not fabricate success or rollback. Reconcile uncertain outcomes while preserving earlier acknowledged data within the qualified fault model. |
| Simulated power loss | Use a documented storage/VFS model covering loss or reordering of unsynchronized writes and checkpoint/reopen behavior. A process kill is insufficient. |
| Deliberate stored-data corruption | Detect missing or altered chunks, manifests, parents and reused objects. This is a detection oracle, not a promise to restore destroyed media. |

In concurrent tests, each distinct publication must fit a valid serial history
under the scoped compare-and-swap rule. Recovery may include valid later
publications; a larger generation number by itself never proves ancestry.
Pinned reads verify the referenced content rather than trusting identifiers
without examining the bytes required by the frozen validation contract.

## 7. SQLite engine and durability profile

These requirements are imported from section 2 of `recomb1.md`. Their presence
in a configuration file is not evidence that the running target applied them.

| Requirement | Required evidence from the tested target |
| --- | --- |
| `journal_mode=WAL` | Read back the intended database mode; reject a silent fallback. |
| `synchronous=FULL` | Verify the relevant connection's setting. WAL `NORMAL` cannot support this slice's intended acknowledged-commit retention promise. |
| `foreign_keys=ON` | Enable before transactions and verify on each relevant connection. Declarations and defaults alone are insufficient. |
| macOS `fullfsync=ON` | Record the requested and observed profile together with VFS identity; it does not establish hardware power-loss qualification. |
| One host-local, nonsynced test store | Use disposable storage outside network mounts and cloud/provider roots; preserve SQLite sidecars through recovery. |
| Actual engine fingerprint | Capture `sqlite_version()`, `sqlite_source_id()`, compile options and VFS from the tested executable. Cargo metadata and the system SQLite CLI do not establish the linked engine. |
| Review-required WAL-reset fix | Qualify an engine containing the fix identified by the review, which cites 3.51.3 and documented backports 3.44.6 / 3.50.7. Reconcile the actual engine against that dependency constraint; this draft is not a new engine audit. |

The one-database choice removes external-filesystem publication from the
atomic commit boundary. WAL and settings still require evidence for the
application's ordering, error handling, selected VFS and failure schedules.
They do not prove that hardware honors flush requests or that arbitrary
distributed effects commit atomically.

## 8. Experimental resource bounds

| Resource | Review-established bound |
| --- | --- |
| Owned byte input | 32 MiB per input |
| Chunk size | 4 MiB; exact final and empty-chunk rules require freeze |
| Root entries | 1,024 opaque items |
| Retained unique chunk payload | 256 MiB |
| Terminal operation receipts | Finite limit required; exact value and accounting await the normative contract |
| Generation | Overflow must be prevented; representation and maximum await the normative contract |

These are experimental limits, not product capacity claims. The unique-payload
bound is not a bound on total SQLite file, metadata or WAL size. Disk-full
behavior must be tested independently. There is no garbage collection or
history pruning to recover capacity in this slice. Reject new work on
exhaustion while preserving previous commits and their historical receipts.

## 9. Qualification and proof gates

Stage 01 must pass CON-01–CON-05 before Stage 02 implements its oracle. Stage 02
passes VAL-01–VAL-06 to establish `ORACLE_READY` only and never claims
`LIT_PASSED`. Stage 03 then runs the independent oracle against the actual
implementation and deliberately faulty variants.

| Gate | Minimum proof obligation | Current state |
| --- | --- | --- |
| LIT-01 | Independent canonical vectors, malformed type/version and overflow rejection, deterministic non-destructive initialization. | `NOT_EXECUTED` |
| LIT-02 | Byte-exact pinned reads after restart, preservation of other items and older revisions, complete closure validation. | `NOT_EXECUTED` |
| LIT-03 | Competing connections/processes yield at most one distinct publication from the same expected revision and generation, with controlled fault-free progress. | `NOT_EXECUTED` |
| LIT-04 | Identical retry returns its original historical receipt; changed meaning cannot reuse its ID; lost replies reconcile. | `NOT_EXECUTED` |
| LIT-05 | Actual process kills around publication and checkpoint boundaries, with complete ACKs observed by an independent parent. | `NOT_EXECUTED` |
| LIT-06 | Write, sync, I/O and disk-full faults, including ambiguous commit; no invented success/rollback or lost earlier acknowledged data. | `NOT_EXECUTED` |
| LIT-07 | Documented and executed VFS/storage power-loss model, including unsynchronized writes and checkpoint/reopen. | `NOT_EXECUTED` |
| LIT-08 | Detect missing/altered content, manifests, parents and reused objects without overwrite, silent rollback, history reset or repair claims. | `NOT_EXECUTED` |
| LIT-09 | Owner/workspace and receipt-access enforcement; no legacy entrypoint or excluded mutation surface. | `NOT_EXECUTED` |
| LIT-10 | Distinct historical receipts, `BUSY`, `CONFLICT`, `OUTCOME_UNKNOWN`, unavailable observations and zero. | `NOT_EXECUTED` |
| LIT-11 | Frozen resource bounds and overflow checks preserve prior acknowledged revisions under exhaustion and contention. | `NOT_EXECUTED` |
| LIT-12 | Independent target and mutant validation, reproducible contract/source/build/runtime evidence, and verified SQLite profile and required fix. | `NOT_EXECUTED` |

Evidence must bind the source, frozen contract, validator, executable, actual
SQLite engine, platform and fault-model identities to executable commands,
exit status, logs, fault schedules and observed acknowledgements. Validation
must not import production encoders, reducers, hash builders or SQL as the
expected-output oracle. Implementation workers cannot modify the reviewed
vectors or accepted evidence used to authorize promotion.

All twelve LIT gates must pass before Stage 04 admission. An unsupported
LIT-07 remains `NOT_EXECUTED` and withholds that promotion. A built candidate,
a process-crash-qualified candidate and a storage-model-qualified candidate
are different results. None alone establishes hardware power-loss or product
release qualification. Any mapping to the broader V01–V12 obligations remains
partial coverage unless those obligations are independently completed.

## 10. Contract-freeze questions

Before implementation is admitted, CON-02/CON-03 must resolve:

1. The missing handoff and acceptance attachments, their identities and their
   reconciliation with this review and the scaffold gates.
2. Canonical bytes, domain separation and identity algorithms; exact types,
   integer widths, empty input/root behavior, ordered chunks, initialization,
   parent rules and generation bounds.
3. Operation scope, request-digest encoding, canonical receipt fields and
   serialization, terminal-receipt limits and accounting.
4. Exact response variants and whether, how and for how long rejections such
   as conflict or operation-ID reuse are durably recorded.
5. Transaction error/unknown-outcome handling, bounded contention policy and
   test-facing framing, including how a complete acknowledgement is identified.
6. Independent vectors, precise fault cases, supported engine/VFS identities,
   evidence format and the controller's promotion checks.

Draft documentation can be reviewed now. It cannot supply the missing
normative inputs, change a gate result, or authorize Stage 03 implementation.
