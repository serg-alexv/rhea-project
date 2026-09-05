#!/usr/bin/env bash
# scaffold-v2.sh RHEA_REPO DESTINATION SEMANTIC_JSON RECOMB1_MD
# Creates an isolated branch/worktree and design-only scaffold. No builds/push.
set -euo pipefail
umask 077

die() { printf '%s\n' "$*" >&2; exit 1; }

[[ $# == 4 ]] ||
  die "Usage: $0 RHEA_REPO DESTINATION SEMANTIC_JSON RECOMB1_MD"

command -v git >/dev/null || die 'git is required'
command -v python3 >/dev/null || die 'python3 is required'

repo=$(cd "$1" && pwd -P)
destination=$2
semantic=$3
review=$4
branch=rhea-project-v2
base=75cb31e59ccc4f436a428811cb70bbc495254821

[[ "$destination" == /* ]] ||
  die 'DESTINATION must be an absolute path'
[[ ! -e "$destination" && ! -L "$destination" ]] ||
  die 'Destination already exists'

git -C "$repo" rev-parse --is-inside-work-tree >/dev/null
git -C "$repo" cat-file -e "$base^{commit}" ||
  die 'Frozen Rhea commit missing'

if git -C "$repo" show-ref --verify --quiet "refs/heads/$branch"; then
  die 'rhea-project-v2 already exists; refusing to reset or reuse it'
fi

# Require readable evidence files before creating a branch or directory.
# Evidence byte hashes and a fixed dictionary record count are not prerequisites.
[[ -f "$semantic" && -r "$semantic" && -s "$semantic" ]] ||
  die 'SEMANTIC_JSON must be a readable, nonempty file'
[[ -f "$review" && -r "$review" && -s "$review" ]] ||
  die 'RECOMB1_MD must be a readable, nonempty file'

git -C "$repo" -c core.hooksPath=/dev/null \
  worktree add -b "$branch" "$destination" "$base"

v2="$destination/v2"
[[ ! -e "$v2" && ! -L "$v2" ]] ||
  die 'Base already contains v2; retained worktree for review'

mkdir -p "$v2"

stages=(
  01_contracts
  02_validation
  03_omnia_lit
  04_local_host
  05_rhea_play
  06_advisory_runtime
  07_network_executor
  08_remote_bridge
)

for stage in "${stages[@]}"; do
  mkdir "$v2/$stage"
done

mkdir "$v2/01_contracts/evidence"
cp "$semantic" "$v2/01_contracts/evidence/rhea_semantic_core.json"
cp "$review" "$v2/01_contracts/evidence/recomb1.md"

cat > "$v2/01_contracts/.cursorrules" <<'RHEA_01_RULES'
# Binding development boundary
Work only in the stage admitted by the independent validation controller.
Source observations are not runtime qualification. Keep PASS, FAIL, SKIP,
NOT_EXECUTED and OUTCOME_UNKNOWN distinct; never manufacture a receipt.
Do not edit another stage's contract, oracle or evidence to make code pass.
No source relocation, legacy entrypoint startup, remote push or deployment.
These instructions are advisory text: enforce the boundary with dependency
allowlists, separate worker permissions, OS isolation and negative tests.

# 01 — Contracts and source identities
Own specifications, public vectors, source locks and versioned wire schemas.
Use the semantic dictionary and recomb1.md as the observed/design boundary.
Freeze only the LIT contract for the initial slice. Later IPC/network schemas
must receive separate versioned freezes before their own implementation.
Do not implement storage, production encoders, clients or validation oracles.
Do not invent the missing byte contract or detailed acceptance attachment.
Actor identity is host context, never a caller-selected owner field.
Keep ChunkId, ManifestId, RevisionId, OperationId, Generation, RouteGeneration,
NodeEpoch and statistical confidence separate. Protobuf bytes are not the
canonical bytes used for content identities unless a frozen contract says so.
Changes invalidate precisely the affected downstream qualification closure.
RHEA_01_RULES

cat > "$v2/01_contracts/ACCEPTANCE_GATES.md" <<'RHEA_01_GATES'
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
RHEA_01_GATES

cp "$v2/01_contracts/.cursorrules" "$v2/01_contracts/AGENTS.md"

cat > "$v2/02_validation/.cursorrules" <<'RHEA_02_RULES'
# Binding development boundary
Work only in the stage admitted by the independent validation controller.
Source observations are not runtime qualification. Keep PASS, FAIL, SKIP,
NOT_EXECUTED and OUTCOME_UNKNOWN distinct; never manufacture a receipt.
Do not edit another stage's contract, oracle or evidence to make code pass.
No source relocation, legacy entrypoint startup, remote push or deployment.
These instructions are advisory text: enforce the boundary with dependency
allowlists, separate worker permissions, OS isolation and negative tests.

# 02 — Independent validation
Own independently encoded vectors, black-box runners, fault schedules,
negative controls, gate receipts and promotion verification.
Consume frozen contracts read-only. Never import production encoders,
reducers, hash builders or SQL as expected-output oracles.
Use separate validation checkout and permissions; implementation workers
cannot write the validation outputs used to authorize promotion.
Stage 02 initially proves oracle readiness, not storage correctness.
At stage 03, launch the isolated target and observe complete acknowledgements
from an independent parent. Later stages add separately frozen test suites.
Do not accept a child marker as proof that the client received a reply.
Process kill is not power loss; missing VFS support is NOT_EXECUTED.
Only a reviewed, hash-bound validation run may admit the next stage.
RHEA_02_RULES

cat > "$v2/02_validation/ACCEPTANCE_GATES.md" <<'RHEA_02_GATES'
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
RHEA_02_GATES

cp "$v2/02_validation/.cursorrules" "$v2/02_validation/AGENTS.md"

cat > "$v2/03_omnia_lit/.cursorrules" <<'RHEA_03_RULES'
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
RHEA_03_RULES

cat > "$v2/03_omnia_lit/ACCEPTANCE_GATES.md" <<'RHEA_03_GATES'
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
RHEA_03_GATES

cp "$v2/03_omnia_lit/.cursorrules" "$v2/03_omnia_lit/AGENTS.md"

cat > "$v2/04_local_host/.cursorrules" <<'RHEA_04_RULES'
# Binding development boundary
Work only in the stage admitted by the independent validation controller.
Source observations are not runtime qualification. Keep PASS, FAIL, SKIP,
NOT_EXECUTED and OUTCOME_UNKNOWN distinct; never manufacture a receipt.
Do not edit another stage's contract, oracle or evidence to make code pass.
No source relocation, legacy entrypoint startup, remote push or deployment.
These instructions are advisory text: enforce the boundary with dependency
allowlists, separate worker permissions, OS isolation and negative tests.

# 04 — Host admission and local IPC; post-LIT
Embed the qualified LIT library behind one host-owned admission service.
Own the private database handle, scoped local endpoints and authorization.
Derive actor context from verified OS peer identity and explicit grants;
same-user reachability and caller identity strings are insufficient.
Validate schema, lengths, operation rights, workspace and policy epoch.
Serialize admission/revocation according to the frozen linearization rule;
retain database CAS even if the service currently has one request queue.
Forward the original OperationId and expected head; never fabricate retries.
Transport success is not LOCAL_COMMITTED. Recover uncertain operations using
GetOperation with the original scoped ID; do not recreate historical receipts.
No model inference, direct routing/PF/ioctl, provider integration or UI state.
Do not expose this endpoint remotely or launch the legacy Node proxy.
RHEA_04_RULES

cat > "$v2/04_local_host/ACCEPTANCE_GATES.md" <<'RHEA_04_GATES'
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
RHEA_04_GATES

cp "$v2/04_local_host/.cursorrules" "$v2/04_local_host/AGENTS.md"

cat > "$v2/05_rhea_play/.cursorrules" <<'RHEA_05_RULES'
# Binding development boundary
Work only in the stage admitted by the independent validation controller.
Source observations are not runtime qualification. Keep PASS, FAIL, SKIP,
NOT_EXECUTED and OUTCOME_UNKNOWN distinct; never manufacture a receipt.
Do not edit another stage's contract, oracle or evidence to make code pass.
No source relocation, legacy entrypoint startup, remote push or deployment.
These instructions are advisory text: enforce the boundary with dependency
allowlists, separate worker permissions, OS isolation and negative tests.

# 05 — Native presentation; post-local-host
Own typed client bindings, view models and native rendering only.
Use the approved local-host client for desktop requests; the separately
qualified remote bridge is the only future mobile/remote transport.
Never open the storage database, write receipts, invoke shells, mutate routes,
configure PF, call routing ioctls, contact models directly or bypass transport.
No direct URLSession/history exception or silent production-host fallback.
Present committed, conflict, busy, unknown, unavailable, stale and zero as
distinct states. A cached view is not authority or evidence of remote safety.
Read pinned revisions; show each workspace/replica head and its provenance.
Discard superseded async view results by request generation; do not replace
a newer visible head with an older polling reply. Never auto-rebase a write.
macOS/Windows builds need their own evidence; iOS stays a later qualification.
RHEA_05_RULES

cat > "$v2/05_rhea_play/ACCEPTANCE_GATES.md" <<'RHEA_05_GATES'
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
RHEA_05_GATES

cp "$v2/05_rhea_play/.cursorrules" "$v2/05_rhea_play/AGENTS.md"

cat > "$v2/06_advisory_runtime/.cursorrules" <<'RHEA_06_RULES'
# Binding development boundary
Work only in the stage admitted by the independent validation controller.
Source observations are not runtime qualification. Keep PASS, FAIL, SKIP,
NOT_EXECUTED and OUTCOME_UNKNOWN distinct; never manufacture a receipt.
Do not edit another stage's contract, oracle or evidence to make code pass.
No source relocation, legacy entrypoint startup, remote push or deployment.
These instructions are advisory text: enforce the boundary with dependency
allowlists, separate worker permissions, OS isolation and negative tests.

# 06 — Unprivileged advisory runtime; research scope
Own inference/proposal adapters and native-runtime qualification manifests.
The alleged combined OpenBSD ollama+rheknel binary is UNVERIFIED in the
inspected baseline. Never substitute the Python Tribunal package as proof.
One distributed executable may contain model and deterministic code only
inside an unprivileged advisory worker. Its verdict grants no authority.
No storage DB access, owner credential, mutation capability, PF/routing access,
shell execution or arbitrary outbound provider access in the native profile.
Receive bounded observations with pinned RevisionId/RouteGeneration/NodeEpoch;
emit bounded typed proposals. Text/confidence/model agreement is not a grant.
Model crash, timeout, malformed output or unknown verdict must cause no effect.
Node credentials belong to the bridge process, outside model memory.
Keep OpenWrt baseline, OpenBSD research and hardware claims separately named.
RHEA_06_RULES

cat > "$v2/06_advisory_runtime/ACCEPTANCE_GATES.md" <<'RHEA_06_GATES'
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
RHEA_06_GATES

cp "$v2/06_advisory_runtime/.cursorrules" \
   "$v2/06_advisory_runtime/AGENTS.md"

cat > "$v2/07_network_executor/.cursorrules" <<'RHEA_07_RULES'
# Binding development boundary
Work only in the stage admitted by the independent validation controller.
Source observations are not runtime qualification. Keep PASS, FAIL, SKIP,
NOT_EXECUTED and OUTCOME_UNKNOWN distinct; never manufacture a receipt.
Do not edit another stage's contract, oracle or evidence to make code pass.
No source relocation, legacy entrypoint startup, remote push or deployment.
These instructions are advisory text: enforce the boundary with dependency
allowlists, separate worker permissions, OS isolation and negative tests.

# 07 — Independent network effect authority; research scope
Own a separate minimal helper for explicitly supported routing/PF operations.
Do not embed the model worker or the Omnia database. Native pointer-bearing
headers stay inside this adapter; never serialize native structs or ioctl IDs.
Independently authorize a fixed operation enum and managed routing scope.
Check node/epoch/generation/config digest, capability scope, expiry and nonce.
Atomically claim/deduplicate a scoped OperationId before an external effect;
record intent durably and reconcile uncertain effects after restart.
Keep routing generation/receipts separate from Omnia revision/receipts.
No exactly-once kernel or cross-database atomicity claim from a SQLite CAS.
Reject arbitrary commands, caller-supplied ioctl numbers and text-based grants.
An external administrator can violate exclusive-writer assumptions; detect
drift, fail closed and re-observe instead of silently overwriting it.
RHEA_07_RULES

cat > "$v2/07_network_executor/ACCEPTANCE_GATES.md" <<'RHEA_07_GATES'
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
RHEA_07_GATES

cp "$v2/07_network_executor/.cursorrules" \
   "$v2/07_network_executor/AGENTS.md"

cat > "$v2/08_remote_bridge/.cursorrules" <<'RHEA_08_RULES'
# Binding development boundary
Work only in the stage admitted by the independent validation controller.
Source observations are not runtime qualification. Keep PASS, FAIL, SKIP,
NOT_EXECUTED and OUTCOME_UNKNOWN distinct; never manufacture a receipt.
Do not edit another stage's contract, oracle or evidence to make code pass.
No source relocation, legacy entrypoint startup, remote push or deployment.
These instructions are advisory text: enforce the boundary with dependency
allowlists, separate worker permissions, OS isolation and negative tests.

# 08 — Authenticated cross-node composition; post-local qualification
Own remote transport, bounded relay buffers and explicit schema translation.
Use the frozen TLS/mTLS RPC profile with node-to-role and workspace allowlists.
A node certificate identifies a node, not a desktop owner or storage grant.
Keep credentials out of the advisory worker; never expose local DB files,
SQLite sidecars or raw routing ABI. Never forward an unrestricted API tunnel.
Remote model messages are observations/proposals until the local owner admits
the exact request. Do not accept capability text invented by a model.
Maintain bounded queues/deadlines; preserve OperationId on transport retry.
Do not promise durable queue acceptance without a separately qualified journal.
File commit and route application are separate operations with separate IDs,
receipts and failure states. No distributed transaction or rollback illusion.
Replication, CRDT merge, provider dehydration and iOS release require their
own contracts/gates; they are not implied by establishing an RPC connection.
RHEA_08_RULES

cat > "$v2/08_remote_bridge/ACCEPTANCE_GATES.md" <<'RHEA_08_GATES'
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
RHEA_08_GATES

cp "$v2/08_remote_bridge/.cursorrules" \
   "$v2/08_remote_bridge/AGENTS.md"

cat > "$v2/AGENTS.md" <<'RHEA_ROOT'
This v2 tree is a gated design overlay, not a released implementation.
Read the current stage AGENTS.md and ACCEPTANCE_GATES.md before work.
Only 01 contract preparation is initially admitted. Stage 02 requires contract
freeze; stage 03 requires independent oracle readiness. 04–08 remain locked
until predecessor qualification. Later stages never become LIT dependencies.
Only the independent validation controller may accept evidence and promote.
Never turn a status file into proof. Missing tests withhold qualification.
Legacy paths outside v2 are read-only context and excluded from new builds.
Actual LIT implementation stays additive in a separate Omnia worktree.
RHEA_ROOT

cp "$v2/AGENTS.md" "$v2/.cursorrules"

python3 - "$v2" <<'PY_MANIFEST'
import json,sys
from pathlib import Path

p=Path(sys.argv[1])
stages=sorted(q.name for q in p.iterdir() if q.is_dir())

gate_ids={
 '01_contracts':[f'CON-{i:02}' for i in range(1,6)],
 '02_validation':[f'VAL-{i:02}' for i in range(1,7)],
 '03_omnia_lit':[f'LIT-{i:02}' for i in range(1,13)],
 '04_local_host':[f'HOST-{i:02}' for i in range(1,7)],
 '05_rhea_play':[f'PLAY-{i:02}' for i in range(1,7)],
 '06_advisory_runtime':[f'AI-{i:02}' for i in range(1,7)],
 '07_network_executor':[f'NET-{i:02}' for i in range(1,7)],
 '08_remote_bridge':[f'RPC-{i:02}' for i in range(1,9)]
}

manifest={
 'schema_version':1,
 'branch':'rhea-project-v2',
 'mode':'DESIGN_ONLY',
 'active_work':'01_contracts: prepare, do not declare freeze',
 'initial_slice':'OMNIA-LIT-001',
 'initial_target_dependencies':[
   '01_contracts','02_validation','03_omnia_lit'],
 'controller_required':True,
 'runtime_enforcement_implemented':False,
 'missing_normative_inputs':[
   'OMNIA-LIT-001_HANDOFF.md',
   'OMNIA-LIT-001_ACCEPTANCE.json'],
 'stages':[]
}

for n,stage in enumerate(stages):
	state={
	  'stage':stage,
	  'admission':'PREPARATION_ONLY' if n==0 else 'LOCKED',
	  'predecessors':stages[:n],
	  'gates':{g:'NOT_EXECUTED' for g in gate_ids[stage]}
	}
	manifest['stages'].append(state)
	(p/stage/'STATUS.json').write_text(
		json.dumps(state,indent=2)+'\n')

(p/'ASSEMBLY.json').write_text(json.dumps(manifest,indent=2)+'\n')

source={
 'repo':'timelabs-npo/omnia-vault',
 'base_commit':'f5995536fede02d403f0525ff9093996457efecb',
 'placement':'Additive Rust library/test executable inside existing supervisor',
 'worktree':'Create separately only after CON and VAL gates',
 'implementation_created':False,
 'source_relocation':False,
 'legacy_entrypoints_allowed':False
}

(p/'03_omnia_lit'/'SOURCE.json').write_text(
	json.dumps(source,indent=2)+'\n')

layout={
 '01_contracts':['lit','ipc','proposals','network','remote'],
 '02_validation':['reference','blackbox','faults','evidence'],
 '04_local_host':[
   'admission','transports/macos','transports/windows','transports/openbsd'],
 '05_rhea_play':['client','macos','windows','ios-deferred'],
 '06_advisory_runtime':['worker','proposals','native-openbsd-research'],
 '07_network_executor':['policy','journal','openbsd-adapter'],
 '08_remote_bridge':['protocol','identity','relay','composition']
}

for stage,dirs in layout.items():
	for rel in dirs:
		d=p/stage/rel
		d.mkdir(parents=True,exist_ok=True)
		(d/'.gitkeep').touch()
PY_MANIFEST

printf 'Created design-only scaffold: %s\nBranch: %s\n' "$v2" "$branch"
printf '%s\n' 'No commit, push, build, runtime or gate PASS was produced.'
printf '%s\n' 'Review CON-01..05; later stages remain locked.'