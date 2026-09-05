# ACCEPTANCE_GATES — 01_contracts
Scope: initial LIT contract freeze; no product execution claim.
CON-01: Verify input hashes and source identities. Record that 99 structural
records, not 5,348 independently qualified implementations, underpin the plan.
CON-02: Retrieve and reconcile OMNIA-LIT-001_HANDOFF.md and
OMNIA-LIT-001_ACCEPTANCE.json referenced by recomb1.md. Until then BLOCKED.
CON-03: Freeze exact canonical bytes, domain separators, integer bounds,
empty input/root behavior, ordered chunks, parent rules, initialization,
operation scope/digest, terminal receipt limits, BUSY and OUTCOME_UNKNOWN.
CON-04: Specify one-DB transaction and acknowledgement/recovery oracles;
exclude every external effect and projection/replication field from LIT.
CON-05: Independent review signs off the contract identity and public vectors;
stage 02 may begin oracle implementation only after CON-01..05 pass.
Later transport/network freezes live in new versioned contract subtrees.
Their approval is required before the corresponding later target starts;
they are not prerequisites for LIT. Changed LIT bytes require a new freeze.

All gates start NOT_EXECUTED. FAIL, SKIP, stale evidence or a missing required
gate prevents promotion. A directory, generated scaffold, compile or reviewer
label is not PASS. The independent controller verifies gate IDs, executable
commands, exit status, logs, source/contract/validator/binary/engine/platform/
fault-model hashes and applicable predecessor receipts. The implementer cannot
approve itself. Hash changes invalidate affected descendants. Source hashes
bind evidence, not reviewer trust: permissions and the trusted controller are
separate requirements. Broader V01–V12 coverage remains partial unless actually
qualified. Future-stage files may be drafted now; implementation stays locked.
