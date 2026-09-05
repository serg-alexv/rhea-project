## Verdict

**Accept the Master Plan’s architectural direction. Proceed with one bounded Omnia implementation slice—not a system-wide consolidation.**

The strongest conclusion survives adversarial review: **the supplied evidence does not establish an existing universal runtime center.** The proposed transition boundary identifies a missing responsibility; it does not discover a hidden implementation, prove a unique architecture, or justify routing every subsystem through one global kernel.

The next task should be **`OMNIA-LIT-001`: publish captured immutable bytes, atomically advance a local revision head, persist the corresponding receipt, and recover/read those bytes under specified failures.** No eviction, symlink replacement, provider integration, model execution, or live user-file mutation belongs in this first slice.

**Execution packet:** :chatgpt-content-reference{index="7"} · :chatgpt-content-reference{index="8"} · :chatgpt-content-reference{index="9"}

### Evidence disposition

| Category | Treatment in this review |
|---|---|
| Supplied semantic observations | Accepted as the **reported, source-bound baseline**, with their stated limits. Source references below use your semantic IDs and registry line ranges. |
| D01–D12 and proposed topology | Design proposals supported by the identified conflicts—not implemented mechanisms. |
| Reported 18-check review | Architecture/provenance/model-review evidence within its disclosed scope. Not runtime qualification; not independently rerun here. |
| Original artifact SHA-256 values | Preserved as reported identities. The pasted compact representations are not asserted to reproduce the original file bytes. |
| Product acceptance | V01–V12 remain `NOT_EXECUTED`. The new, narrower LIT gates also start `NOT_EXECUTED`. |

## 1. Source-bound adversarial review

### A. The centrality conclusion is sound; its scope must remain narrow

The selected observations support several distinct coordination points, not an established universal authority. Omnia’s event store, supervisor metadata and mock presentation state are different mechanisms; they are **not three implementations of an existing canonical head**. The head contract is precisely what is missing from the inspected path. **Evidence:** `OMN.001–004`, `OMN.006`, `OMN.012`, `OMN.017`; particularly `SRC.004:24–83` and `SRC.005:30–71`.

The proposed graph’s dominator result is valid **for that graph**. Likewise, “existence plus uniqueness implies one logical owner” states an architectural requirement. Neither result selects Rust, SQLite, a daemon, or a universal middleware layer.

**Refinement:** make the first responsibility specifically **Omnia local revision publication**. Reuse its contract discipline elsewhere only when another domain needs it. Do not make network telemetry, renderer state or dialogue history depend on a new universal transaction service merely to reproduce the diagram.

### B. The first implementation blocker is an unspecified physical commit unit

The plan correctly rejects magical filesystem/database atomicity, but its staging diagram still leaves the implementer a consequential choice: **which exact bytes and records commit together?**

The current source-bound counterexamples are concrete: three separate event-store writes, and filesystem changes followed by supervisor metadata writes whose errors can be discarded. **Evidence:** `OMN.004 → SRC.004:60–83`; `OMN.008–009 → SRC.005:199–305`.

**Proposed first-slice decision:** keep chunk BLOBs, manifests, revisions, the local head and operation receipts in **one SQLite database**, and publish them in **one transaction**. Avoid external object files for this experiment. SQLite’s WAL documentation explicitly distinguishes atomicity within a database from transactions spanning multiple attached databases. 

This is a deliberate reduction in scope, not a permanent storage prescription. It removes the external-filesystem commit problem from the first acceptance boundary.

There is a useful corresponding simplification:

> **Without external pre-commit effects or an asynchronous acceptance promise, this slice does not need a separately durable pre-commit intent state.**

The terminal operation ledger commits with the revision. Incomplete database work recovers as uncommitted; the identical operation can be retried. The richer intent/reconciliation machinery becomes mandatory when external objects or provider effects are introduced—not before.

### C. “Idempotent” needs an explicit ordering rule

Consider this sequence:

**A expects generation 7 → A commits generation 8 → its reply is lost → A retries with its original expected generation 7.**

An implementation that checks the current head before consulting the operation ledger incorrectly returns a conflict for its own successful operation.

The required order is:

**Authorize receipt access → look up the scoped operation ID → compare the stored request digest → return the original receipt or reject ID reuse → only then evaluate a genuinely new publication against the current head.**

The digest must bind the operation’s meaning: owner, workspace, replica, item, expected revision/generation and verified content identity. A receipt from generation 8 must remain the **same historical receipt** after generation 9 exists; it must not be reconstructed from the latest head.

This refines D01/D04/D05 rather than claiming a newly observed implementation bug. The inspected write path does not yet supply this operation protocol. **Evidence:** `OMN.004`, `OMN.007`, `OMN.013`, `OMN.017`.

Two additional distinctions are essential:

**`BUSY` is not `CONFLICT`.** Lock contention says the transaction could not proceed; conflict says the expected state was examined and no longer matches. SQLite documents both write serialization and `BEGIN IMMEDIATE` contention behavior. 

**An ambiguous storage error is not proof of rollback.** Preserve the operation ID and reconcile through database recovery. Until the outcome is established, report `OUTCOME_UNKNOWN`, not an invented success or definitive rejection. SQLite transaction errors require explicit attention to the resulting transaction state. 

### D. “Intact bytes” and “a coherent live-file snapshot” are different claims

A hash establishes the identity of the bytes actually captured. It does not establish that an externally changing file was captured as one coherent point-in-time version.

The first slice should therefore accept an **owned immutable byte buffer**, not open a user-provided path. Its read operation must accept a pinned `RevisionId` and verify the referenced content.

This deliberately excludes filename semantics, directory snapshots, ACLs, extended attributes, resource forks and native projection behavior. Those are separate capture/adapter contracts. The current path-based request and filesystem handlers do not justify combining those guarantees. **Evidence:** `OMN.007–010 → SRC.005:35–45,174–183,199–305`.

**Practical implication:** demonstrate preservation using generated disposable fixtures. Do not “prove safety” by moving, dehydrating or replacing a real file.

### E. New correctness must not inherit the legacy mutation surfaces

A new state library would not repair the existing Node proxy, supervisor handlers, shell interpolation or mock success projection.

The handoff identifies the relevant boundaries: unrestricted path-shaped requests, route composition without an observed universal authorization gate, application-error/HTTP-success confusion, and shell interpolation. **Evidence:** `OMN.011`, `OMN.013`, `OMN.016`; `SRC.006:109–120,192–228,351–424,714–735,808–811`.

**Containment decision:** the test executable must not start those legacy entrypoints. Give the new store one narrow host-owned mutation API; exclude HTTP listeners, raw-path mutations, shells, providers and models.

Conversely, do not require a rewrite of all Rheknel before implementing this boundary. Its frozen callback/judge API is not the missing typed validator, and its emitter does not enforce the judgment sequence. **Evidence:** `RHK.003–005`, `RHK.008`; `SRC.038:79–132`.

The appropriate claim after a successful slice would be **“this new local path passed these tests,”** not “Omnia/Rheknel is now safe.”

### F. Receipt state, projection state and replication state must remain separate

The Master Plan’s prose makes this distinction correctly. Its sequential-looking state diagram could nevertheless become an incorrect single-enum implementation.

A local commit may be complete while projection is pending. A projection can fail without undoing a valid commit. Remote recoverability has its own evidence.

For the first slice, omit projection/replication/eviction fields entirely. Return terminal local receipts and separately scoped observations. Preserve zero, unknown, unavailable and historical state; do not supply success-shaped defaults. **Evidence motivating that discipline:** `OMN.012–014`, `PLAY.010`, `APP.013`.

### G. The validation plan needs partial-coverage accounting

The original roadmap can be overread as requiring all language bindings, legacy callback corrections and desktop packaging before demonstrating one storage transition. That would expand work without first resolving the immediate integrity failure.

For this slice, a Rust target plus an **independently implemented reference encoder and black-box validator** is sufficient. It does **not** complete V03’s C/Rust/Swift/JS coverage, V04’s legacy mediation coverage, or V10’s native-client qualification.

The prior review’s independence is also correctly qualified by its own disclosure: its reviewer contributed MBSD records. That does not invalidate its aggregation review; it prevents treating the receipt as independent assurance of every source interpretation.

**Required refinement:** every new result must identify its tested boundary and map to an original V gate as **partial coverage**, never silently change the parent gate to `PASS`.

## 2. One additional engine-level constraint

This is an **external dependency constraint**, not a new finding about the frozen Omnia runtime.

SQLite’s current documentation identifies a WAL-reset corruption bug fixed in **3.51.3**, with documented backports including **3.44.6 and 3.50.7**. The supplied semantic records do not establish which SQLite engine the eventual Rust build will actually link. Record `sqlite_version()`, `sqlite_source_id()`, compile options and VFS from the tested executable—not just a Cargo dependency version or the system `sqlite3` command. 

The proposed local durability profile is:

| Requirement | Meaning for this slice |
|---|---|
| `journal_mode=WAL`, verified | Use the intended database mode; do not silently accept a fallback. |
| `synchronous=FULL`, verified | Do not use WAL `NORMAL` while promising retention of acknowledged commits through power loss. SQLite distinguishes those durability properties. |
| `foreign_keys=ON`, verified per relevant connection | Do not assume declarations or defaults establish enforcement. Configure before transactions. |
| macOS `fullfsync=ON`, recorded | Request the platform-specific flushing behavior and record the VFS; this is not itself hardware qualification. |
| Host-local, nonsynced test store | Keep the database outside network mounts and cloud/provider roots; preserve its SQLite sidecars. |

These settings and limits follow SQLite’s documented transaction, synchronization and connection behavior; they do not remove the need to test the application’s ordering and error handling. 

**Process termination and power-loss simulation need separate gates.** SQLite’s own testing documentation uses a specialized VFS to simulate I/O failures and loss/reordering of unsynchronized writes. Killing a process without that storage model is not the same experiment. 

## 3. Concrete next slice: `OMNIA-LIT-001`

### The operation

**`PublishItemBytesV1`**

Its request identifies the operation, workspace, replica, item, expected revision/generation and claimed content-manifest identity. Actor identity comes from host-owned context. Submitted bytes must reproduce the claimed identity.

The public read surface is limited to **`GetHead`**, **`GetOperation`** and **`ReadItem(revision_id, item_id)`**.

The attached contract specifies exact canonical encodings, domain-separated manifest/revision identities, empty-file behavior, chunk ordering, parent rules and generation bounds. Those are **new proposed contract choices**, not descriptions of existing code.

### The committing transaction

After bounded input validation and content hashing, the implementation must:

1. Resolve any recorded operation ID before testing a new expected head.
2. Compare both expected revision and generation within the scoped write transaction.
3. Verify the existing and candidate content closure, including reused objects.
4. Insert immutable content/manifests and a revision whose parent is the expected head.
5. Conditionally advance the head and insert its canonical receipt in the same transaction.
6. Emit `LOCAL_COMMITTED` only after successful commit.

An existing object with the same ID but different bytes is **corruption**, not permission to overwrite it. A numerically higher head is insufficient for recovery: it must be a valid descendant of the acknowledged revision.

### Bounded utility

The proposed test profile allows **32 MiB per input**, **4 MiB chunks**, **1,024 items per root**, and **256 MiB retained unique chunk payload**. It limits terminal receipts and prevents generation overflow. These are experimental limits, not product capacity claims.

The root is a flat map of opaque item IDs, not a directory model. There is no garbage collection or history pruning. Exhaustion must reject new work while preserving previous commits.

The deliverable is an additive Rust library/test executable in the existing Omnia supervisor project, built in an isolated local worktree from:

`f5995536fede02d403f0525ff9093996457efecb`

Existing user branches and uncommitted work remain untouched.

## 4. Acceptance gates

**Every gate below is currently `NOT_EXECUTED`.**

| Gate | Required evidence |
|---|---|
| **LIT-01 — Canonical identities** | Independent byte vectors; malformed types/versions rejected; deterministic, non-destructive initialization. |
| **LIT-02 — Pinned content** | Byte-exact reads after restart; updating one item preserves other items and older revisions. |
| **LIT-03 — Real CAS** | Competing connections/processes; at most one distinct publication from the same expected head, plus progress under a controlled fault-free schedule. |
| **LIT-04 — Retry identity** | Identical retries reuse the original receipt; changed requests cannot reuse its ID; lost replies reconcile correctly. |
| **LIT-05 — Process crashes** | Actual process kills around content, head, receipt, commit, acknowledgement and checkpoint boundaries. |
| **LIT-06 — Storage faults** | Write/sync/space errors and uncertain outcomes; no fabricated success or discarded earlier commit. |
| **LIT-07 — Simulated power loss** | A documented storage/VFS fault model, including unsynchronized writes and checkpoint/reopen behavior. |
| **LIT-08 — Corruption detection** | Missing or altered chunks/manifests/parents detected without silent overwrite, rollback or claims of repair. |
| **LIT-09 — New-path authority** | Owner/workspace enforcement; no legacy, network, model, raw-path or shell mutation path. |
| **LIT-10 — Honest observations** | Terminal receipts, historical results, unknown outcomes and unavailable state remain distinguishable. |
| **LIT-11 — Resource limits** | Bounds, disk-full behavior and lock contention preserve all earlier acknowledged revisions. |
| **LIT-12 — Independent evidence** | Frozen contracts, independent fixtures, actual build/runtime identities and tests that detect deliberately faulty variants. |

For LIT-05, an **independent parent process must observe the complete acknowledgement**. A flag emitted by the child saying “I would have acknowledged” is not the oracle.

For every failure schedule:

**Before acknowledgement:** recovery may expose the old or new **complete** state.

**After acknowledgement:** the acknowledged revision and its content remain readable; the head is that revision or a valid descendant. A crash alone cannot erase it.

Artificially corrupting stored data afterward tests detection, not the ability to recover destroyed media.

The packet defines separate qualification levels. A built candidate is not a crash-qualified candidate; process-crash qualification is not storage-model qualification; neither is hardware power-loss or product-release qualification.

## 5. Ready-to-dispatch local handoff

The following is the execution brief. The attached Markdown contract and acceptance JSON contain the normative details.

# OMNIA-LIT-001 — execute the first local intact transition slice

Parent handoff: `rhea-step23-20260905-230a6a1e`.

Implement only the bounded local byte/revision operation specified in `OMNIA-LIT-001_HANDOFF.md`. Use `OMNIA-LIT-001_ACCEPTANCE.json` as the independent acceptance obligation. All gates begin `NOT_EXECUTED`.

## Source and work boundary

Use the existing local `timelabs-npo/omnia-vault` repository at frozen commit `f5995536fede02d403f0525ff9093996457efecb`. Create an additive isolated worktree and local branch. Preserve existing branches, working files and uncommitted changes.

Do not repeat repository extraction. Targeted local inspection of the relevant Rust/dependency files is permitted. Keep raw implementation text local.

Primary evidence: `OMN.001–004`, `OMN.006–014`, `OMN.016–017`, `RHK.003–005/008`, and `CORE.006–007`. Retain the source identities supplied in the packet’s source lock.

No remote push, PR, deployment, external message or new umbrella application task.

## Dispatch

`@codex-contract` — Freeze the public operation, receipt and canonical encoding contract. Emit its hash and independently reviewable public vectors. Do not implement the target or certify execution.

`@codex-validator` — In a separate validation checkout, derive black-box fixtures and expected results from that frozen contract. Do not import production encoders, reducers, hash builders or SQL as the oracle. Prepare concurrency, process-kill, storage-fault and negative-control tests.

`@codex-implementer` — Build one small Rust state library and test-facing executable inside the existing Omnia supervisor project. Contracts and validation artifacts are read-only. Do not alter an oracle to accommodate implementation behavior.

`@codex-reviewer` — Review actual artifacts, source/engine identities, logs, failures and qualification limits. Confirm that deliberately faulty variants are detected. Preserve every required FAIL, SKIP and NOT_EXECUTED result.

Bind these assignments to actual available local workers. These labels alone do not constitute delegation or execution evidence. Record unavailable isolation/tooling honestly.

## Implementation boundary

Implement `PublishItemBytesV1`, `GetHead`, `GetOperation` and revision-pinned `ReadItem`.

Use one SQLite database containing bounded immutable chunks, manifests, revisions, the head and canonical terminal operation receipts. Publish content, head and receipt in one transaction.

Consult the operation ledger before applying a fresh expected-head test. Identical retries return the original recorded receipt; a recorded ID with different request meaning fails. An unresolved commit/storage outcome remains `OUTCOME_UNKNOWN` and is reconciled using the same operation ID.

Emit `LOCAL_COMMITTED` only after successful commit under the verified engine/durability profile. Preserve all previous committed revisions. Detect corruption without silently replacing objects or resetting history.

Input is captured immutable bytes—not a live user pathname.

Do not start the legacy Node router or legacy supervisor mutation routes. Do not add filesystem eviction, symlinks, shell execution, provider integration, cloud upload, models, Redis, firmware work, or production UI wiring.

## Verification and return

Execute LIT-01 through LIT-12 where supported, on disposable generated fixtures only. Record exact source, contract, validator, binary, SQLite engine, platform and fault-model identities.

Independently observe acknowledgements. Test actual competing processes and process termination; do not substitute the parent handoff’s finite model checks. Do not substitute process termination for simulated power loss.

Report partial coverage of original V01–V12 gates without marking the broader obligations complete.

Return the additive patch/local commit identity, build commands, gate table, evidence artifacts, one successful transition trace, the most informative failure/recovery trace and remaining limitations. Raw implementations remain local.

Stop after this slice. A missing required test withholds the corresponding qualification label; it does not justify fabricating PASS or expanding into unrelated work.

The full packet adds the byte-level contract, source lock, detailed fault cases and machine-readable gate mapping. **This chat produced the review and implementation handoff only; it did not launch local agents, modify repositories, build product code or execute product tests.**