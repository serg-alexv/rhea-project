# ACCEPTANCE_GATES — 08_remote_bridge
Prerequisite: NET-01..06 and all earlier receipts; frozen remote RPC contract.
RPC-01: Mutual authentication, server identity, node-role/workspace mapping,
expiry/revocation and protocol-version rejection pass. Node identity cannot
become desktop actor identity or confer a mutation grant.
RPC-02: Deny generic tunneling, DB/sidecar transfer, native structs, filesystem
paths and shell operations. Model credentials are absent from worker memory.
RPC-03: Partition, reconnect, replay, duplication, reorder, truncated payload,
deadline and backpressure tests preserve IDs and separate domain generations.
RPC-04: A lost response after file commit yields reconciliation, not route
success or automatic storage retry under a fresh ID. Verify pinned reads.
RPC-05: File success/route failure and the inverse remain separate receipts;
unresolved external effect remains UNKNOWN. No cross-domain atomicity claim.
RPC-06: Prove observations/proposals can flow OpenBSD node → bridge → local
host → UI without unauthorized effects or silent success-shaped defaults.
RPC-07: Independent regression matrix covers claimed desktop/node profiles
with actual build/credential/fault identities. Native iOS qualification is
required before an iOS support claim, and remains outside Omnia desktop v1.
RPC-08: Close the target composition with an evidence manifest and explicit
remaining exclusions. Replication, CRDT merge, provider capture/eviction and
hardware product release need new gates; RPC PASS grants none of those claims.

All gates start NOT_EXECUTED. FAIL, SKIP, stale evidence or a missing required
gate prevents promotion. A directory, generated scaffold, compile or reviewer
label is not PASS. The independent controller verifies gate IDs, executable
commands, exit status, logs, source/contract/validator/binary/engine/platform/
fault-model hashes and applicable predecessor receipts. The implementer cannot
approve itself. Hash changes invalidate affected descendants. Source hashes
bind evidence, not reviewer trust: permissions and the trusted controller are
separate requirements. Broader V01–V12 coverage remains partial unless actually
qualified. Future-stage files may be drafted now; implementation stays locked.
