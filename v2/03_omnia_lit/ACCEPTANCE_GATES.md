# ACCEPTANCE_GATES — 03_omnia_lit
Prerequisites: CON-01..05, VAL-01..06. Code remains additive in Omnia supervisor.
LIT-01: Independent canonical vectors; reject malformed type/version and
overflow; deterministic initialization preserves existing stores.
LIT-02: Pinned byte-exact reads survive restart; one item update preserves all
other items and retained older revisions; verify complete content closure.
LIT-03: Real competing connections/processes from one expected revision AND
generation yield at most one distinct publication; demonstrate fault-free
progress. A process mutex or sequential reference model alone is insufficient.
LIT-04: Identical retries return the exact historical receipt after later
commits; changed request cannot reuse its ID; lost replies reconcile.
LIT-05: Kill actual processes at chunk/manifest/head/receipt/commit/ack and
checkpoint boundaries. An independent parent records complete received ACKs.
LIT-06: Inject write/sync/I/O/disk-full errors, including ambiguous commit;
never invent rollback/success and never discard earlier acknowledged data.
LIT-07: Document and run a storage/VFS power-loss model covering unsynchronized
writes and checkpoint/reopen. Process termination does not satisfy this gate.
LIT-08: Detect missing/altered chunks, manifests, parents and reused objects;
do not overwrite, reset, silently roll back or claim repair of destroyed media.
LIT-09: Enforce owner/workspace scope and receipt authorization. Prove the new
target starts no legacy entrypoint and has no listener/model/shell/provider/
user-path/symlink/eviction/replication mutation surface.
LIT-10: Preserve terminal historical receipt, BUSY, CONFLICT, OUTCOME_UNKNOWN,
unavailable and zero distinctly; HTTP/process success cannot replace a receipt.
LIT-11: Enforce 32 MiB input, 4 MiB chunks, 1,024 root items, 256 MiB retained
unique payload, frozen receipt/generation bounds; no GC or history pruning.
Resource exhaustion and lock contention preserve all acknowledged revisions.
LIT-12: Independent target/mutant validation and reproducible evidence record
actual sqlite_version(), sqlite_source_id(), compile options and VFS. Verify
WAL, FULL, foreign_keys per connection and macOS fullfsync profile. Qualify an
engine containing the review's required WAL-reset fix; do not infer linked
engine identity from Cargo metadata or the system sqlite3 executable.
Recovery oracle: before ACK old OR new complete state is allowed; after ACK
the acknowledged revision/content stays readable and head is that revision
or a valid descendant. Numerical generation alone is not ancestry proof.
Host-local nonsynced disposable store only; preserve SQLite sidecars.
ALL LIT-01..12 must pass for stage 04. Unsupported LIT-07 withholds promotion.
Storage-model qualification is not hardware power-loss or product release.

All gates start NOT_EXECUTED. FAIL, SKIP, stale evidence or a missing required
gate prevents promotion. A directory, generated scaffold, compile or reviewer
label is not PASS. The independent controller verifies gate IDs, executable
commands, exit status, logs, source/contract/validator/binary/engine/platform/
fault-model hashes and applicable predecessor receipts. The implementer cannot
approve itself. Hash changes invalidate affected descendants. Source hashes
bind evidence, not reviewer trust: permissions and the trusted controller are
separate requirements. Broader V01–V12 coverage remains partial unless actually
qualified. Future-stage files may be drafted now; implementation stays locked.
