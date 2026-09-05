# ACCEPTANCE_GATES — 06_advisory_runtime
Prerequisite: PLAY-01..06; frozen observations/proposals and runtime budgets.
AI-01: Pin target OS, build/toolchain, executable, model/weight identities and
runtime profile. Prove actual native OpenBSD execution; Python/container or
OpenWrt output cannot stand in for the claimed three-model OpenBSD binary.
AI-02: Malicious prompt/output, forged verdict and compromised worker cannot
read DB/credentials or invoke privileged network/storage effects.
AI-03: Bound memory/CPU/time/output/queue resources; kill/timeout/OOM cannot
change a file head or route. Model output remains non-authorizing data.
AI-04: Every proposal binds observed revisions, route generation, node epoch
and schema; stale/unknown observation is represented, not silently refreshed.
AI-05: Host-side deterministic admission independently rejects forged grants;
a policy function sharing model memory is not the authorization boundary.
AI-06: Reproducible native tests qualify the actual claimed model count and
hardware profile. An unavailable native target keeps stage 07 locked.
No prerequisite from this stage may be added retroactively to LIT qualification.

All gates start NOT_EXECUTED. FAIL, SKIP, stale evidence or a missing required
gate prevents promotion. A directory, generated scaffold, compile or reviewer
label is not PASS. The independent controller verifies gate IDs, executable
commands, exit status, logs, source/contract/validator/binary/engine/platform/
fault-model hashes and applicable predecessor receipts. The implementer cannot
approve itself. Hash changes invalidate affected descendants. Source hashes
bind evidence, not reviewer trust: permissions and the trusted controller are
separate requirements. Broader V01–V12 coverage remains partial unless actually
qualified. Future-stage files may be drafted now; implementation stays locked.
