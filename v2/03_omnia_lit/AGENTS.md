# Binding development boundary
Work only in the stage admitted by the independent validation controller.
Source observations are not runtime qualification. Keep PASS, FAIL, SKIP,
NOT_EXECUTED and OUTCOME_UNKNOWN distinct; never manufacture a receipt.
Do not edit another stage's contract, oracle or evidence to make code pass.
No source relocation, legacy entrypoint startup, remote push or deployment.
These instructions are advisory text: enforce the boundary with dependency
allowlists, separate worker permissions, OS isolation and negative tests.

# 03 — OMNIA-LIT-001 only
This folder owns the assembly manifest, not a relocated storage implementation.
Add Rust library and test executable inside the existing Omnia supervisor in
an isolated worktree rooted at f5995536fede02d403f0525ff9093996457efecb.
Expose only PublishItemBytesV1, GetHead, GetOperation and revision-pinned
ReadItem. Accept owned immutable bytes and host-established identity.
Keep chunks, manifests, revisions, local head and terminal operation receipts
in one SQLite database; publish them in one committing transaction.
Authorize receipt access; resolve scoped OperationId and request digest before
fresh expected-head CAS. Preserve original historical receipts on retries.
Verify reused objects and content closure; never overwrite corruption.
No HTTP/socket listener, network, UI, model, Rheknel dependency, shell, raw
user-path mutation, symlink, external CAS files, provider, eviction, Redis,
replication, garbage collection or history pruning. Do not start legacy main.
Stop the implementation slice after LIT qualification; later folders are
separate scopes, never dependencies of this target or its build command.
