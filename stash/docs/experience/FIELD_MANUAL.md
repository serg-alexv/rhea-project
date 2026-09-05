# Field manual: exploration, propagation and evidence assessment

Version 1.0.0. This manual extracts reusable engineering experience from the WD/RHEA preservation work. It complements [the executable-work instructions](../../protocol/LEFTOVER_PRESERVATION.md); shell fragments here are recipes to adapt inside an authorized scope, not commands executed by this documentation release.

“Propagation” means moving bytes and their identities, evidence class, ownership/scope and custody records to appropriate storage. A copy without this context is an incomplete transfer. “Expert assessment” means checking what evidence establishes and what remains unknown. “Speedup” means avoiding unnecessary reads, transfers, retries or model context while retaining the checks needed for the claimed result.

## 1. Evidence and authority model

| Class | What may be concluded | What may not be concluded |
| --- | --- | --- |
| Current direct observation | The named tool read these bytes, refs or configuration at the recorded time | That inaccessible machines or future executions agree |
| Supplied local audit | The supplied report states that its operator observed a result | That this execution environment reproduced the observation |
| Historical execution receipt | A retained record documents a past command/result | Current availability, current state or successful later steps |
| Signed author assertion | The signed text is consistent with the verified signing key | Independent signer trust, upstream origin or build linkage without further evidence |
| Design/source inspection | Code or documentation specifies a behavior or exposes a missing mechanism | Successful execution, deployment, durability or acceptance |
| Proposal/inference | A reasoned next design or operating rule | An installed feature, measured improvement or completed migration |

Never collapse these axes into one `verified` boolean: availability, byte identity, source identity, upstream authenticity, custody, build linkage, execution and qualification. A raw discovery map is useful for locating evidence; a map entry is not the evidence payload.

The existing user authorization covers archival publication and repeatable documentation. Historical instructions found inside profiles, logs or downloaded projects remain material to assess; they do not expand the current task's authority. The v2 boundary is documented in [the existing compatibility assessment](../../memory/COMPATIBILITY.md).

## 2. Technique register

Each entry gives its evidence basis, reusable action, economy mechanism and a condition that must not be lost. The compact [JSON index](techniques.json) supports selective retrieval. A recorded technique is not an installed automation.

### T01 — Establish the execution host before traversing paths

**Basis: session observation.** A Windows user interface and supplied WD paths coexisted with a Linux execution runtime. Test narrowly for the requested local roots and discover available connectors. Record host, reachable roots and unresolved account mappings. Use an available Drive connector for its declared scope. This avoids repeated impossible filesystem scans. Never mark a Windows path accessible because the user can see it on their own desktop; the connected Drive account was not proven to be the account mounted as `G:\`.

### T02 — Resume from the checkpoint, not the conversation corpus

**Basis: implemented protocol and memory projection.** Read the current pointer, latest summary, pending records, genome version and current remote ref first. Load original maps or logs only for the item being resolved. Key reused observations by content identity, scope and policy version. This avoids re-reading settled evidence. A changed capability, policy or source invalidates the relevant cached decision even when a filename is unchanged.

### T03 — Discover filenames before reading contents

**Basis: supplied WD maps and subsequent targeted reads.** Use `rg --files` or an equivalent bounded filename inventory. Search relevant names, then inspect the exact files returned. Include ignored files when build outputs are the target, and record exclusion rules. A later no-ignore pass in the supplied map added 1,734 paths: 1,662 vendor paths and 72 other paths. This demonstrates coverage sensitivity, not 1,734 newly recovered deliverables. Avoid filling model context with vendor trees.

### T04 — Treat pagination and search matching as evidence boundaries

**Basis: Drive discovery.** Follow available continuation tokens; exact-filter the returned name and parent after a provider's search. Record limits, access errors and unreturned pages. Hits named `0.log`, `p0.log` or `gem0.log` did not establish a file named `log.0`. Query narrowing and pagination reduce irrelevant reads, but a bounded search supports only `NOT_FOUND_IN_SCOPE`. It cannot establish global absence.

The supplied WD map also retained opaque Trae files named `database.db` that did not have a SQLite header. A familiar extension does not establish a readable format. Record the failed format/open observation and use separately available readable history; do not reinterpret arbitrary bytes or pursue credentials/decryption as a discovery shortcut.

### T05 — Separate path, claim, captured bytes and backup

**Basis: supplied maps and archival manifests.** Give every locator an availability state and a separate storage state. Keep inaccessible VM, guest-log and Mac paths as pending locators. Hashing a manifest does not preserve the six binaries named inside it. This allows useful partial publication without waiting for every machine. Do not silently mark unresolved items excluded merely to close a run.

The same rule applies to service discovery: the supplied historical Atlas/Themis/Tribunal notes described distinct deployed surfaces and routes that returned HTML. A responding page or fallback route does not prove that a named API/backend exists there. Keep repository, deployed URL, response type and observation time separate.

### T06 — Compare live repository identity before deciding “not on Git”

**Basis: earlier repository comparison retained in the report.** Read the remote ref and commit relationship, then compare source trees or specific objects. The mapped `C:\mbsd` revision was an ancestor of a checked remote revision; it was not simply “ahead.” The independent `mbsd-pipeline` work had no established upstream mapping. This avoids duplicate commits and false novelty. A stale `origin/*` ref or missing remote does not prove that bytes were never published elsewhere.

### T07 — Read Git objects when a checkout cannot represent the tree

**Basis: supplied WD map and Git API publication.** The report attributed 574 missing tracked paths to an incomplete Windows checkout, including path-name and lazy-fetch problems. Inspect commit/tree/blob identities before treating working-tree absence as deletion. For an archive, construct a new tree from an exact base and an explicit path allowlist. This avoids repairing an unrelated working tree just to publish documents. Never turn checkout damage into a deletion commit.

### T08 — Batch independent reads and serialize dependent mutations

**Basis: connector operations in this session.** Fetch independent source files or refs concurrently, inspect every success/error, then decide the next dependent operation. Publish objects, tree, commit and ref in order. Keep tool discovery narrow and print only relevant metadata. This reduces round trips and context noise. Unawaited work, ignored partial errors or concurrent writes to the same branch do not count as an acceleration.

### T09 — Use the supplied maps to select the smallest decisive probe

**Basis: binary-provenance report and subsequent comparison.** Start from the exact manifest, signer metadata, source revision or missing filename that can resolve the question. Expand roots only when a recorded uncertainty requires it. For the MBSD origin gap, recovering the correct signed arm64 checksum record is more decisive than another broad source-tree inventory. Keep the scope expansion log; a map is a discovery aid and must not become unquestioned truth.

### T10 — Preserve bytes before interpreting or normalizing them

**Basis: exact-byte publication of four source objects.** Compute SHA-256 and byte length on the original stream; retain it as an immutable object. Use a byte-preserving upload path, including base64 blob creation when text conversion would alter line endings. Create readable derivatives separately. A supplied map used mixed line endings. This avoids invisible corruption and repeated “same text” disputes. Semantic equivalence is not byte identity.

### T11 — Deduplicate content while retaining every source locator

**Basis: SHA-256 object layout in the archive.** Store an identical reviewed object once, keyed by digest and size, and add aliases/custody records for the different locations. Distinguish a duplicate payload from a duplicate event: two observations of identical bytes may both matter. This saves storage and repeated analysis. Do not replace source history with one arbitrarily selected “original,” or assume equal names mean equal content.

### T12 — Inspect archives within explicit limits

**Basis: supplied binary audit.** List bounded members and stream candidate bytes without extraction or execution. Check member count, declared and actual streamed size, decompression ratio, duplicate paths, traversal, links and special types. Record a limit stop as `DEFERRED_LIMIT`. The audit inspected a small Blueshoes transfer archive without finding candidate binaries. This avoids unpacking irrelevant or dangerous trees. Declared metadata alone does not cap actual decompression; enforce streaming limits too.

### T13 — Snapshot changing sources consistently

**Basis: existing storage policy; generalized procedure.** For ordinary files, detect change during capture and defer unstable results. For a database or VM disk, require a supported consistent snapshot or an agreed quiescent state; a filename copied successfully is insufficient. Do not start a VM merely to search its disk. This prevents repeating corrupt captures. SQLite WAL handling belongs to a consistent backup procedure; the existing [storage analysis](../../memory/COMPATIBILITY.md) explains the source basis.

### T14 — Keep secret-bearing bytes out of a public propagation path

**Basis: archive privacy policy and supplied audit scope.** Screen candidate paths and review publishable text. Keep private keys, credential media and authentication stores outside the collection; hold sensitive project material in an explicitly appropriate private destination. Preserve only non-secret locators/status in public records. This avoids a costly later history purge. Broad permission to preserve leftovers is not permission to disclose unrelated personal or credential material.

### T15 — Distinguish integrity, signer trust and upstream authenticity

**Basis: supplied MBSD audit.** Both handoff copies matched seven checksum entries and verified relative to a supplied Ed25519 key. The same bundle supplied the key, allowed signer and expected fingerprint. Record these facts separately: consistency was established; independent signer trust was not. This prevents repeated checksum work being mistaken for origin proof. For upstream verification, recover the correct release/architecture signed record and independently authenticate its key.

Repeated assistant agreement is also not independent evidence when all participants rely on the same report or signed assertion. Preserve source dependency, not just the number of agreeing summaries.

### T16 — Require an explicit source-to-build-to-output link

**Basis: supplied MBSD audit.** The signed manifest explicitly said the recorded dirty source and MT7981 stubs were not used for the included stock kernel. A build script, ELF format or banner did not repair that missing linkage. Request a receipt binding exact source/patch inputs, command/environment and output digest. This narrows the remaining evidence request. Do not compile something new and retroactively attribute its provenance to the old binary.

### T17 — Keep identity and device readiness separate

**Basis: supplied MBSD audit.** `flashable: false` and `ram_boot_ready: false` remained unchanged after checksum/signature checks. Record format, architecture and identity as independent observations. Successful archive custody does not admit firmware execution or prove board support. This prevents inappropriate deployment work and false completion. The original BSDRP comparison cannot elevate MBSD readiness beyond these findings.

### T18 — A missing expected artifact is not a digest mismatch

**Basis: supplied Blueshoes audit.** Six B0 manifest entries were `NOT_FOUND_IN_SCOPE`; observed sizes and digests were unavailable. The 5,080-byte transfer archive contained five source files and five AppleDouble sidecars. Ask for the original CI/release output or producer directory tied to the manifest commit. This avoids hashing unrelated files repeatedly. A future matching binary would establish manifest identity; build authenticity and deployed execution would still need their own receipts.

### T19 — Use exact allowlists when publishing Git evidence

**Basis: completed archival publication.** Build on the current base tree, add only reviewed paths and verify every changed blob plus unchanged out-of-scope root entries. Use expected-parent concurrency control and no force update. This publishes evidence without staging unrelated repository damage. A new tree without its intended base can omit existing project paths. `git add -A` is inappropriate for an unreviewed mixed or broken checkout.

### T20 — Verify the destination, not merely the upload response

**Basis: completed Git/Drive readback.** Check remote Git blob identity and size against local bytes; preserve SHA-256 as the cross-store payload identity. Download an archival cloud object back and hash it when trustworthy hash metadata is unavailable. The earlier 101,366-byte ZIP passed this readback. This closes transfer uncertainty once, allowing later reuse of a scoped receipt. Metadata success or a download URL alone does not establish durable bytes.

### T21 — Close receipts without circular self-hashes

**Basis: two-step publication receipts.** Publish a capture commit; verify it; add a subsequent receipt naming that commit/tree and the observed results. Corrections are new records that identify the superseded assertion. This makes provenance reproducible. A file cannot normally contain the final commit ID of the commit containing that same file. Avoid repeatedly rebuilding packages to chase such a circular identity.

### T22 — Separate archive publication from project integration

**Basis: stash archive and distinct v2 documentation PR.** Archive cross-project leftovers under `stash`; promote only individually reviewed reports or source changes to their owning project. Keep evidence paths and qualification gates distinct. This preserves scattered work now without pretending that all components compose. Never merge the whole archival branch into v2 as a cleanup shortcut; inherited legacy files are not newly assessed inputs.

### T23 — Give each memory type a bounded role

**Basis: memory refresh and compatibility review.** Stable sourced facts go to rhea-memory projections; operational decisions to Nexus; task preferences to soul.md; raw events to a scoped `log.0` segment; replaceable hot state to a separately admitted Redis role. The scheduler decides when to recheck. This prevents every component from becoming a second canonical database. Updating administrative projections does not mean the original live DB, ledger or stream was changed.

### T24 — Keep the context entry point compact and source-backed

**Basis: measured local files and earlier publication receipt.** The current MEMORY.md is 2,587 bytes and task-scoped soul.md is 1,560 bytes. Link evidence and pending work instead of embedding transcripts. Retrieve detail by item ID. These are measured input sizes, not measured token savings or a universal optimal budget. Preserve provenance and uncertainty during summarization; a compact assertion without its source is a lossy cache.

### T25 — Treat cloud replicas and mutable working state differently

**Basis: Drive archival work and storage policy.** Use sealed packages and read-only projections in cloud storage. Keep a mutable working directory under one active writer; do not nest Drive and iCloud sync roots or share a live SQLite/WAL database between them. Independently identify the intended account/root before changing local cache state. This avoids sync conflicts. Two copies under one account may share a failure domain and are not automatically independent backups.

### T26 — Reclaim cache bytes only after preservation is verified

**Basis: authorized procedure, not a performed WD cleanup.** For a confirmed local cloud cache, verify the retained remote object, then use the provider's supported eviction/dehydration mechanism. Measure allocated local bytes and free-space change, separately from logical file size and cloud quota. Do not delete the cloud original to free a local cache. No WD mount was available in the inspected runtime, so reclaimed WD bytes remained zero; this is not a cleanup success claim.

### T27 — Do not choose a canonical memory copy by filename or mtime alone

**Basis: multiple Drive copies of legacy material.** Compare content identity, version, source ownership and provenance. Select an explicit projection destination and record its source. Keep conflicting assertions as unresolved until the authoritative scope is known. This avoids refreshing every stale copy and amplifying contradictions. “Newest modified” may describe a copy or sync event rather than a newer factual state.

### T28 — Update an existing scheduler and make unchanged runs cheap

**Basis: completed scheduler configuration update.** The existing hourly watch was narrowed to the current v2 boundary and memory changes, retaining its cadence/timezone. First compare small refs/checkpoints; retrieve details only for changes. Report actionable deltas and preserve pending reasons without committing identical heartbeats. This avoids duplicate tasks and repeated broad legacy scans. A verified configuration update is not proof that a future scheduled run executed.

### T29 — Retry when inputs change, not because a timer fired

**Basis: current protocol and scheduler policy.** Cache blockers with capability/scope identity and a recheck trigger. WD mount availability, a new artifact receipt or newly granted access justifies another probe; an unchanged missing endpoint does not justify a full rescan. Use a bounded lightweight capability check where needed. Do not cache “absent” forever or suppress genuinely new evidence.

### T30 — Checkpoint partial progress explicitly

**Basis: published partial collection.** Store completed object receipts, next cursor, remaining roots, limits and errors. Declare `COMPLETE_IN_DECLARED_SCOPE` only when its coverage conditions hold; otherwise preserve a partial status. The original 41-item/group queue is not a count of captured files and was not closed by the memory refresh. This makes work resumable without claiming universal completion.

### T31 — Validate the claim with the smallest sufficient check

**Basis: documentation and preservation work.** For an archival document change, check syntax where applicable, links, source references, byte identities and the remote changed-path set. Do not launch unrelated builds or component tests to decorate the result. For a future storage engine, concurrency and crash tests would be necessary because durability is the claim. This saves irrelevant work while preserving meaningful verification.

The earlier report's historical `14/14 tests` and audit GO concerned an acquisition/backup script; they did not qualify RAM boot, flashing or Wi-Fi. A retained shell parse error likewise does not prove that the intended reset command executed. Bind each result to the exact component, command and claim it supports.

### T32 — Turn recurring failures into versioned genome changes

**Basis: protocol 1.1.0 and changelog.** Record the triggering evidence, new rule, scope, version, compatibility impact, migration and rollback. Add a new historical record rather than rewriting an old run. A docs-only experience release need not bump executable protocol semantics. This converts one investigation into repeatable practice. The genome cannot expand permissions, grant itself deployment authority or change v2 acceptance rules.

### T33 — Normalize tool envelopes once and retain compact results

**Basis: connector work in this session.** Understand the specific tool's nested result/content shape, unwrap it once, and store reusable parsed metadata. Print selected IDs, lengths, status and errors instead of entire trees or bodies. Never treat an HTTP/tool success envelope as the success of the requested mutation. This reduces context pressure and repeated discovery. Persist decisive evidence before transient scratch state disappears.

### T34 — Keep text editing and shell execution separate

**Basis: session editing experience.** Use structured arguments or literal patch/file writes for Markdown and JSON. Supply patch hunks in source order and against current context. A prior out-of-order patch could not locate an earlier hunk; rereading the narrow context resolved it. Avoid interpolating untrusted text into shell commands: JSON quoting does not neutralize backticks or command substitution. This prevents avoidable retries and accidental execution.

### T35 — Batch immutable records rather than making every event a commit

**Basis: proposed generalization, not a benchmarked implementation.** Collect bounded event segments, seal them once, publish the segment and manifest, and commit a batch. Give retries stable event identities and new captures collision-resistant run IDs. This can reduce commit/API overhead while keeping individual evidence records. Do not append forever to one shared JSONL file or use second-resolution filenames as a uniqueness guarantee. See the [Omnia design](OMNIA_APPEND_ONLY.md).

### T36 — Stop when the authorized claim is sufficiently verified

**Basis: task-economy correction.** Deliver the concrete artifact, verified publication and remaining blockers. Do not reopen settled questions merely to produce another summary, repeat a permission request already answered, or run another broad test suite. Further work needs a new uncertainty, changed input or required gate. This preserves user attention as well as tokens; it does not permit abandoning necessary work that is still reachable and authorized.

## 3. Repeatable operating sequence

1. **Admit scope.** Read current constraints, authorization, genome and pending checkpoint. Record host capabilities and exact repository revisions.
2. **Discover the delta.** Enumerate scoped names/metadata; include ignored output locations when relevant; retain pagination, excluded roots and access failures.
3. **Classify.** Assign project owner, evidence class, confidentiality, availability and intended memory/storage role. Keep uncertain ownership in a reviewed pending queue.
4. **Capture.** Stream stable exact bytes; compute size/SHA-256; preserve aliases. Defer unstable, oversized or inaccessible sources explicitly.
5. **Assess the narrow claim.** Compare manifests, architecture, source/build linkage and trust evidence. Record `UNKNOWN` where an independent link is absent.
6. **Propagate.** Write immutable objects to the appropriate destination; read back and verify; publish manifests and a later closure receipt. Keep large/private material out of public Git.
7. **Refresh projections.** Update the compact facts, operational checkpoint and task-specific preferences only when their source changes. Keep raw evidence separately retrievable.
8. **Reclaim local cache if eligible.** Confirm identity, accessibility and preservation receipts; use provider-supported eviction; measure actual reclaimed bytes.
9. **Close or checkpoint.** Report completed scope, pending reasons and the exact next decisive action. Upgrade the genome only for a reusable rule supported by evidence.

For current WD-specific paths and implementation details, reuse [RESUME_ON_WD.md](../../protocol/RESUME_ON_WD.md) instead of copying another divergent command script into this manual.

## 4. Cost accounting without invented speedups

Measure before/after for comparable scopes: API calls, bytes read/transferred, distinct objects, wall time, context bytes loaded, retries, committed paths, and actual local bytes reclaimed. Record tool/model version if token counts are measured. A smaller document or batched request is a mechanism for improvement, not proof of a percentage gain.

Earlier receipts establish four preserved source/report objects totaling 115,053 bytes; a later 27-member package was 101,366 compressed bytes for 257,698 uncompressed bytes. These are different packaging scopes, so subtracting them would be an invalid deduplication claim. The latter package's SHA-256 is `2bdcabfea24d69255ea43a2775b4929c4c053e3c44ac7c45e3ce6a7bfa69b564`. Its verified remote copy does not establish completeness of the WD collection.

A cache key should include at least source identity, claim type, scope/policy version and tool semantics relevant to that claim. Metadata-only comparison can decide where to look; a fresh byte-identity claim still needs trustworthy content identity. Negative results expire or are invalidated when coverage/capability changes.

## 5. Failure-to-rule ledger

| Failure or tempting shortcut | Reusable correction | Evidence boundary |
| --- | --- | --- |
| Commit all visible changes | Exact paths plus base-tree preservation; distinguish checkout damage | Git source inspection and publication |
| Read every old conversation again | Compact source-backed checkpoint and selective retrieval | Implemented memory projection |
| Trust a bundle because its included key verifies it | Separate key-relative consistency and independent trust | Supplied binary audit |
| Treat stock kernel plus local stubs as a custom port | Require explicit source/build/output linkage | Signed manifest statement in supplied audit |
| Treat missing files as hash failures | Preserve unavailable observations and search coverage | Supplied binary audit |
| Assume Drive connector proves a local `G:\` mapping | Verify account/root identity independently | Current capability observation |
| Treat a cloud upload as local space recovered | Readback, supported eviction, allocated-byte measurements | Procedure only; WD cleanup not performed |
| Repeatedly overwrite one log or current report | Immutable segments and derived mutable indexes | Proposed storage design |
| Apply an old profile's mandatory pauses/tests blindly | Apply current authorized scope and meaningful checks | Compatibility assessment |
| Claim the scheduler has run because it was updated | Distinguish configuration receipt from execution receipt | Completed configuration mutation |

## 6. How to extend this documentation

Add a stable technique ID with source refs, observed/proposed status, trigger, action, economy mechanism, failure condition and validation claim. Link the original evidence instead of copying it again. Add a changelog entry; keep old run records immutable. Reassess affected techniques when a schema, tool, policy or provider behavior changes. A useful future register can automate these relationships; the present [Omnia comparison](OMNIA_APPEND_ONLY.md) explains what is still missing.
