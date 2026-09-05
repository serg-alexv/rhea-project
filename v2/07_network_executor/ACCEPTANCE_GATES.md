# ACCEPTANCE_GATES — 07_network_executor
Prerequisite: AI-01..06; frozen operation-specific network effect contract.
NET-01: Verify separate helper identity/permissions, managed scope and fixed
operations. Deny arbitrary shells, ABI payloads, ioctl numbers and model grants.
NET-02: Competing requests from one expected node epoch/generation/config digest
cannot both receive distinct successful application receipts for that state.
Test exclusive-writer assumptions and fail-closed response to out-of-band drift.
NET-03: Persist scoped operation claim/intent before effects; inject crashes
before/during/after native application and receipt writes. Reconcile actual
state and preserve UNKNOWN when effect outcome cannot be established.
NET-04: Distinguish route/PF transactions; prove each supported OS operation's
atomicity/rollback limits. Never infer combined route+PF atomicity from headers.
NET-05: Test capability nonce reuse, changed ID meaning, expiry, restart epoch,
fencing, permission denial and stale proposals without affecting the Omnia head.
NET-06: Verify actual OpenBSD ABI conversion and restricted OS primitives on a
disposable VM/network. Hardware enablement requires separate hardware evidence.
All NET gates permit stage 08; a failed external effect cannot undo a file ACK.

All gates start NOT_EXECUTED. FAIL, SKIP, stale evidence or a missing required
gate prevents promotion. A directory, generated scaffold, compile or reviewer
label is not PASS. The independent controller verifies gate IDs, executable
commands, exit status, logs, source/contract/validator/binary/engine/platform/
fault-model hashes and applicable predecessor receipts. The implementer cannot
approve itself. Hash changes invalidate affected descendants. Source hashes
bind evidence, not reviewer trust: permissions and the trusted controller are
separate requirements. Broader V01–V12 coverage remains partial unless actually
qualified. Future-stage files may be drafted now; implementation stays locked.
