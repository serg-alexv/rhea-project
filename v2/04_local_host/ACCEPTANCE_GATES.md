# ACCEPTANCE_GATES — 04_local_host
Prerequisite: all LIT gates; separately frozen local IPC/admission contract.
HOST-01: Endpoint credential, application/service policy and workspace denial
tests reject impersonation, same-user overreach, remote pipe clients and
spoofed servers. Actor is derived by the host, never deserialized authority.
HOST-02: Reject unknown versions/enums, oversized/truncated/reordered frames,
invalid IDs and unauthorized methods before unbounded allocation or storage.
HOST-03: Request storm, cancellation, timeout and disconnect preserve scoped
OperationId and CAS; lost ACK resolves through the original GetOperation.
HOST-04: Race publication with policy revocation. In-flight admission and
revocation follow the frozen epoch/linearization rule; new requests cannot
use revoked grants. The database still checks the expected head atomically.
HOST-05: The only database access is the qualified library. Dependency and
runtime denial tests find no legacy routes, shell, model or routing effects.
HOST-06: Bounded memory/queues, service restart and complete LIT regression
pass on each claimed desktop host profile; IPC status never fabricates commit.
All HOST gates permit stage 05; local transport does not qualify remote access.

All gates start NOT_EXECUTED. FAIL, SKIP, stale evidence or a missing required
gate prevents promotion. A directory, generated scaffold, compile or reviewer
label is not PASS. The independent controller verifies gate IDs, executable
commands, exit status, logs, source/contract/validator/binary/engine/platform/
fault-model hashes and applicable predecessor receipts. The implementer cannot
approve itself. Hash changes invalidate affected descendants. Source hashes
bind evidence, not reviewer trust: permissions and the trusted controller are
separate requirements. Broader V01–V12 coverage remains partial unless actually
qualified. Future-stage files may be drafted now; implementation stays locked.
