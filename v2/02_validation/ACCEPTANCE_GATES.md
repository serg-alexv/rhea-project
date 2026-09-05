# ACCEPTANCE_GATES — 02_validation
Prerequisite: CON-01..05. Exit means ORACLE_READY, never LIT_PASSED.
VAL-01: Independent checkout/worker cannot consume production logic as oracle;
implementation permissions cannot modify reviewed vectors or accepted results.
VAL-02: Independent encoders reproduce public vectors and derive boundary,
empty, malformed and overflow cases from the frozen contract.
VAL-03: Black-box harness schedules competing processes and observes complete
acknowledgements itself; framing rejects incomplete/truncated child output.
VAL-04: Fault fixtures distinguish process kill, I/O failure, power-loss model
and deliberate corruption; record unsupported mechanisms before target work.
VAL-05: Contract-derived negative controls are caught: CAS omitted, receipt
lookup after CAS, acknowledgement before commit, corrupted reused chunk,
missing receipt, BUSY mislabeled CONFLICT and fabricated success.
VAL-06: Harness/version/fault profiles frozen; LIT-01..12 remain NOT_EXECUTED.
All VAL gates permit stage 03 implementation. At stage 03 rerun the oracle
against the actual target and deliberate target mutants. Later target suites
are prepared here before each later stage, without weakening earlier tests.

All gates start NOT_EXECUTED. FAIL, SKIP, stale evidence or a missing required
gate prevents promotion. A directory, generated scaffold, compile or reviewer
label is not PASS. The independent controller verifies gate IDs, executable
commands, exit status, logs, source/contract/validator/binary/engine/platform/
fault-model hashes and applicable predecessor receipts. The implementer cannot
approve itself. Hash changes invalidate affected descendants. Source hashes
bind evidence, not reviewer trust: permissions and the trusted controller are
separate requirements. Broader V01–V12 coverage remains partial unless actually
qualified. Future-stage files may be drafted now; implementation stays locked.
