# ACCEPTANCE_GATES — 05_rhea_play
Prerequisite: HOST-01..06; frozen typed presentation/client contracts.
PLAY-01: Build actual native macOS and Windows clients against one versioned
client contract; source declarations and the hme binary are not client proof.
PLAY-02: Dependency inspection plus runtime denied-operation tests demonstrate
no DB, raw network routing/PF, shell, direct model or transport-bypass path.
PLAY-03: Show LOCAL_COMMITTED only for a verified application receipt. Exercise
conflict, busy, unknown, unavailable, stale, empty and genuine zero separately.
PLAY-04: Delayed/out-of-order polling and workspace switching cannot overwrite
newer views; pinned reads keep the requested revision; retries keep the ID.
PLAY-05: Endpoint choice is explicit; no development credential or silent
local-to-production rewrite. Cache loss does not affect durable storage.
PLAY-06: Independent desktop end-to-end byte publication/read/restart succeeds
with all LIT/HOST regressions intact. iOS remains unqualified and deferred.
All PLAY gates permit stage 06 research; desktop release is a separate claim.

All gates start NOT_EXECUTED. FAIL, SKIP, stale evidence or a missing required
gate prevents promotion. A directory, generated scaffold, compile or reviewer
label is not PASS. The independent controller verifies gate IDs, executable
commands, exit status, logs, source/contract/validator/binary/engine/platform/
fault-model hashes and applicable predecessor receipts. The implementer cannot
approve itself. Hash changes invalidate affected descendants. Source hashes
bind evidence, not reviewer trust: permissions and the trusted controller are
separate requirements. Broader V01–V12 coverage remains partial unless actually
qualified. Future-stage files may be drafted now; implementation stays locked.
