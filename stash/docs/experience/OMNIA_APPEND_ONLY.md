# Can omnia-playbook become an append-only Git container?

Assessment version 1.0.0. **Decision: useful procedure catalog; substantial storage mechanisms still required.** The inspected repository does not implement a durable append-only artifact register. Git can carry versioned metadata and reviewed small objects for an open-ended logical archive. Physical capacity, write coordination, retention and access controls remain finite engineering concerns.

This document is source analysis and a proposed architecture. It does not install a writer, change Omnia schemas or pipelines, run diagnostics, implement a v2 contract, or claim acceptance. “Register” refers here to omnia-playbook's existing directory/schema catalog; no dedicated registry service or `registry/` implementation was found in the inspected tree. “Git container” means a portable repository of records and references, not an OCI container or an unlimited storage service.

## 1. Exact inspection scope

| Input | Pinned identity | Scope |
| --- | --- | --- |
| omnia-playbook main | `c9220eee388bba1b4d256d0a6ebd241cf5060102` | Complete recursive tree: 91 entries, 58 blobs, no truncation; 22 selected files read |
| RHEA archival input | `6ac41f6183e6539e9a3f9796bc0536b87a12f9b2` | Existing stash protocols, memory projections and receipts |
| RHEA v2 boundary | `accc8619b179539c3a775844f5f077fbad80715e` | Existing compatibility assessment points to Stage 01 constraints |

The checked omnia-playbook main revision is a comparison subject, not a replacement for the source frozen by the separate v2 task. That task retains OMNIA-LIT-001 and frozen source `f5995536fede02d403f0525ff9093996457efecb`. No source admission follows from this document.

File/blob identities and links are in [sources.json](sources.json). The following matrix describes code/configuration present at the pinned revision, not live CI results or runtime measurements.

## 2. Capability comparison

| Requirement | Present in omnia-playbook | Gap for an append-only register |
| --- | --- | --- |
| Portable procedure taxonomy | Foundation, adapters, checks, playbooks and references directories | Good conceptual home for reusable techniques; does not itself store execution history |
| Typed records | Three JSON Schemas: invariant, check, environment | No artifact, event, replica, custody, checkpoint or archive-segment schema |
| Strict top-level shape | The three schemas reject extra top-level properties | New storage fields need an explicitly versioned new type/envelope, not informal extra fields |
| Stable references | String IDs, source strings, check IDs, remediation paths | No inspected global ID uniqueness, cross-reference resolution or byte-pinned source enforcement |
| Execution specification | Check schema includes command, timeout and expected output/exit | A schema field does not enforce execution policy, timeout, output limits or qualification |
| Diagnostic execution | A hard-coded host DNS diagnostic | No generic executor driven by the check catalog in the inspected script |
| Execution observations | Timestamp, invariant ID, platform, status, reason, resolvers, raw output, read-only flag | No binding to source commit, command digest, observer identity, actual command exit record or artifact digests |
| Durable report retention | JSON/Markdown generation under `reports/` | `.gitignore` excludes those generated reports; only `.gitkeep` is tracked there |
| Collision-free record creation | UTC second-resolution report filenames | No exclusive creation, run UUID or writer coordination; an existing path can be overwritten |
| Append-only policy | No relevant enforcement found in inspected files | Need rejection of edits/deletions to sealed paths, including otherwise valid fast-forward commits |
| Content addressing and deduplication | No artifact CAS in the inspected tree | Need exact-byte digests, sizes, aliases and object existence verification |
| Cloud replica management | Apple/Windows adapter notes and storage foundation are placeholders | Need provider/account identity, upload/readback receipts and cache-eviction eligibility |
| Validation | Syntax, fixture schemas, shell/links checks and workflows | Actual catalog instances, referential integrity and storage semantics are not covered by the inspected schema-fixture checks |
| Incremental resume and task economy | No matching mechanism found in the inspected files | Need checkpoints, scope fingerprints, pagination/error state and changed-input scheduling |
| Retention and capacity rollover | No archive epochs or retention mechanism found | Need bounded segments, reachable archival references, replica policy and migration indexes |
| Privacy and local access policy | Security/contribution rules; local-agent SSH policy | Useful constraints in documentation; not demonstrated enforcement by a storage gateway |

Sources: pinned [README](https://github.com/timelabs-npo/omnia-playbook/blob/c9220eee388bba1b4d256d0a6ebd241cf5060102/README.md), [schemas directory](https://github.com/timelabs-npo/omnia-playbook/tree/c9220eee388bba1b4d256d0a6ebd241cf5060102/schemas), [diagnostic writer](https://github.com/timelabs-npo/omnia-playbook/blob/c9220eee388bba1b4d256d0a6ebd241cf5060102/scripts/diagnose.sh), [report writer](https://github.com/timelabs-npo/omnia-playbook/blob/c9220eee388bba1b4d256d0a6ebd241cf5060102/scripts/report.sh), [ignore rules](https://github.com/timelabs-npo/omnia-playbook/blob/c9220eee388bba1b4d256d0a6ebd241cf5060102/.gitignore), [validation script](https://github.com/timelabs-npo/omnia-playbook/blob/c9220eee388bba1b4d256d0a6ebd241cf5060102/scripts/validate.sh) and [schema tests](https://github.com/timelabs-npo/omnia-playbook/blob/c9220eee388bba1b4d256d0a6ebd241cf5060102/tests/test_schemas.py).

### Specific source-level failure modes

`report.sh` derives paths from `%Y%m%dT%H%M%SZ`. `diagnose.sh` opens its JSON output with mode `w`; report Markdown uses `write_text`. Two runs selecting the same second and directory can therefore target the same paths. This is an overwrite risk established by source inspection; no collision experiment was run.

The diagnostic emits logical `pass`, `fail` or `unsupported`, but contains no explicit process-exit mapping from that logical result. A caller must not treat process exit zero as a universal successful check. The script also does not consume the YAML check definitions; their timeout and expected-output fields are not a general execution engine.

The validator and Python tests exercise valid/invalid fixtures for the three schemas. That is different from validating every real invariant/check instance, resolving its referenced IDs, or enforcing retention and append-only writes. Workflow files establish configured commands, not that those commands succeeded. This assessment does not repair or rerun legacy CI.

## 3. Reuse the catalog without mixing evidence and authority

Keep these planes distinct:

| Plane | Suggested role | What it must not silently become |
| --- | --- | --- |
| Omnia procedure catalog | Invariants, rationales, documented checks and remediation recipes | The authority to run commands merely because a record contains one |
| Git archival register | Reviewed manifests, immutable event segments, receipts, small public evidence | Unlimited binary storage or proof that referenced cloud bytes still exist |
| Durable object stores | Large/private exact-byte objects and verified replicas | A multiwriter live database shared through sync folders |
| Derived indexes and compact memory | Search, summaries, current pointers and incremental discovery | The only surviving copy of evidence or an independent qualification verdict |
| Admitted scheduler/writer | Execute already authorized work, checkpoint and publish bounded deltas | Permission expansion or a PASS generator |

The existing rhea-memory/Nexus/soul/log.0/Redis role mapping fits this separation at the administrative level. Their implementations are not qualified as this storage layer by the earlier review. In particular, legacy SQLite key replacement and an unverified Redis authority model do not provide an append-only durable register. See [COMPATIBILITY.md](../../memory/COMPATIBILITY.md).

For a future Omnia extension, describe a preservation invariant using the current invariant/check/playbook model, but keep artifact and custody instances in a new versioned record family. Existing `additionalProperties: false` rules mean those fields cannot simply be attached to the old records. Proposed family names below are design vocabulary, not accepted v2 schemas.

## 4. A precise append-only contract

There are three different promises:

1. **Immutable objects:** an address identifies exact payload bytes. The object is never replaced by different bytes; a mismatch is an error.
2. **Append-only sealed records:** after publication, an event/run/segment path can only remain unchanged. Corrections arrive as new events with an explicit `supersedes` reference and reason.
3. **Mutable derived views:** `current.json`, search indexes, compact summaries and current procedure versions may advance. They identify their input records and can be rebuilt. They are outside the sealed namespace.

The current stash layout follows some of these rules procedurally. It has not demonstrated server-enforced append-only behavior. Git content addressing alone does not prevent a later commit from editing or deleting a path. Fast-forward-only branch updates preserve ancestry, but also permit such edits in descendants. Consequently, a “no force push” rule is necessary for this design but insufficient to enforce immutable record paths.

A future admitted write gate must inspect the complete proposed change set, reject sealed-path modifications/deletions, validate new records and object references, and publish through a controlled branch update. Repository protection must require that gate for all ordinary writers. Administrative bypass and retention privileges must be modeled explicitly. If the requirement includes resistance to an administrator rewriting/deleting the repository, independent protected retention or write-once storage is needed; a Git branch policy is not that guarantee.

Keep archived Git objects reachable from retained refs and maintain verified independent copies. Git's garbage collection can prune unreachable objects; reflog presence is not a permanent retention contract. See the official [git-gc documentation](https://git-scm.com/docs/git-gc).

## 5. Proposed record families and identifiers

| Record family | Minimum information | Validation purpose |
| --- | --- | --- |
| Procedure | Stable ID/version, scope, source refs, trigger, steps, authority requirements, expected evidence and stopping rule | Make a technique reproducible without granting execution permission |
| Artifact | Exact-byte SHA-256, byte length, format observation, confidentiality, source aliases | Identify content independently of filenames or repository object format |
| Observation/event | Unique event ID, run ID, observed/recorded timestamps, evidence class, subject, claim and result | Separate what happened from what a document merely asserts |
| Run/checkpoint | Declared roots, policy/source versions, capabilities, completed cursor, exclusions/errors and pending queue | Express completeness only within known coverage |
| Replica/custody | Artifact ID, destination identity, copy state, verification method/time and receipt | Distinguish uploaded, readback-verified, inaccessible and eligible-for-eviction states |
| Sealed segment/epoch | Included record range/IDs, byte digest, predecessor/checkpoint reference and storage locations | Bound writes and support replay and archival rollover |
| Correction | Referenced record, reason, replacement claim and evidence | Preserve history while allowing knowledge to improve |

Timestamp is evidence, not a uniqueness primitive. Use collision-resistant event/run IDs and detect collisions explicitly. For payloads, hash exact captured bytes. Git blob identity is separate; these repositories use SHA-1 object IDs, while the cross-store artifact key is SHA-256. Do not label the Git SHA-1 as a SHA-256 receipt.

An event must keep claimed and observed values separate. For example, a missing Blueshoes artifact has a manifest's expected hash, `availability: NOT_FOUND_IN_SCOPE`, and no observed hash. Its schema must not require fabricating observed bytes to satisfy a field. Signed assertions must also carry trust scope instead of a generic `trusted: true`.

Define serialization and any canonicalization only in the separately admitted contract work. This proposal does not invent a canonical byte format for OMNIA-LIT-001. Until such a format is frozen, exact serialized file bytes can be hashed and retained without pretending differently formatted JSON is the same payload.

## 6. Proposed write and recovery protocol

The following describes a future implementation; it was not installed by this change.

1. Capture to a private local spool under a unique run ID. Enforce source stability, size/privacy limits and explicit scope. Preserve pending items when a limit is reached.
2. Compute exact payload identity and check whether that verified object already exists. Reuse identical content while preserving a new observation/custody event when warranted.
3. Publish any external objects first. Record `UPLOADED` separately from `REMOTE_VERIFIED`; obtain trustworthy readback evidence before relying on the destination.
4. Seal a bounded event segment and manifest. A segment ID already containing different bytes is a collision; never overwrite it. An identical retry is idempotent.
5. Read the current branch head. Construct an additive tree against that head, with a complete sealed-path change check and a narrow allowlist for derived-view updates.
6. Publish the commit with concurrency control. If the head changed, read the new head, reconcile event IDs and reconstruct the candidate. Never force a stale tree onto the branch.
7. Verify the remote commit/tree and changed blobs, then publish a closure receipt naming that preceding commit. Advance compact derived pointers only to valid committed input records.
8. Mark a local cache object eligible for eviction only after its authoritative retained destination and required independent replicas meet policy. Record eviction and measured bytes separately.

On a local Git server, `git update-ref <ref> <new> <old>` can reject a changed expected ref. That is a Git reference update facility, not a cross-store transaction. A hosted API must be used according to its actual concurrency semantics; do not assume it exposes an equivalent old-OID parameter. See [git-update-ref](https://git-scm.com/docs/git-update-ref). With the GitHub publication approach used here, a commit is constructed on the observed parent and advanced without force; divergence requires a fresh candidate, not a forced update.

Git and cloud storage do not share an atomic transaction in this design. Recovery must therefore be explicit:

| Interruption | Retained state | Resume action |
| --- | --- | --- |
| Before object upload | Local spool or pending locator | Reuse stable verified bytes; recapture unstable sources |
| After upload, before verification | Remote object may exist | Verify the exact intended object; do not declare a backup yet |
| After verification, before Git commit | Verified external object lacks committed manifest | Reuse its receipt and publish the manifest idempotently |
| After commit, before closure receipt | Capture commit exists | Verify it and add the receipt; do not duplicate the capture |
| Competing writer advances head | Candidate is stale | Rebase the additive proposal logically; resolve ID collisions; revalidate affected paths |
| External object later disappears | Git record remains, replica becomes unavailable | Add a loss/correction event, restore from another verified replica if possible |

Concurrent producers should create disjoint immutable records. A single admitted committer or equivalent serialized write service can sequence publication. A local lock or a Redis TTL by itself does not establish cross-machine mutual exclusion, fencing or durability. Offline work is allowed in a spool; its later publication must still pass the current authority and schema rules.

## 7. Capacity: open-ended sequence, bounded physical stores

Current GitHub guidance recommends a compressed `.git` size up to **10 GB**, directory width up to **3,000** and single objects up to **1 MB**. It enforces a **100 MB** single-object limit and **2 GB** push limit. These are different kinds of limit: 10 GB is guidance, not an unlimited-storage entitlement or a universal hard quota. Recheck provider documentation before sizing a deployment. Source: [GitHub repository limits](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits).

No repository-size, throughput, concurrency or provider-quota benchmark was run here. The 58-blob Omnia tree count measures the inspected scaffold, not its storage capacity. Source strings and directory stubs cannot establish an operational capacity percentage.

### A transparent sizing model

Let `r` be events/day, `m` serialized metadata bytes/event, `H` retained days, and `D` unique external payload bytes/day. Then the raw retained event payload is approximately `r × m × H`; external raw payload is `D × H`. Git additionally retains trees, commits, indexes and prior versions. Compression, packing, repetition, replicas and provider overhead change actual storage, so measure them rather than inserting a universal multiplier.

**Illustrative workload only:** 10,000 events/day at 1,024 bytes/event produce 10,240,000 bytes/day and 3,737,600,000 bytes per 365-day year, about 3.48 GiB of serialized events before Git overhead. Batching 100 events gives 100 data commits/day rather than 10,000 if using one data commit per batch; closure/pointer commits would be additional. These are arithmetic estimates, not measured Omnia performance or a guarantee that a repository will remain healthy.

### Bounded layout and rollover

- Seal segments at a configured byte/record budget and use unique IDs. Keep a small index of segment identities; do not rewrite one ever-growing global JSONL file.
- Partition directories by epoch and an additional bounded shard key. Monitor actual directory width; one directory per day still becomes too wide at high event counts. A single two-hex digest prefix is also not a universal scale solution.
- Keep large binaries, VM disks, raw histories and repeatedly repackaged ZIPs outside ordinary Git blobs. Git records their exact identities, custody and approved locations.
- Seal an epoch before its chosen operational budget is exceeded. Publish a checkpoint and successor pointer. Older epochs can live in independently retained repositories or verified archival snapshots with explicit retrieval instructions. This is proposed future provisioning, not a claim that such shards exist now.
- Keep a portable catalog linking the epochs and their integrity anchors. Moving an epoch must add a relocation/custody record; it must not erase the ability to resolve an old reference.

Deleting a current file does not remove its reachable historical revisions. An append-only workload must budget for accumulated history. Partial or shallow local access may reduce initial transfer, but it does not create infinite remote capacity or provide complete local replay evidence. Do not reclaim a retained epoch merely because a small current index still references it.

The usable promise is: **the logical sequence can continue while new bounded storage is provisioned and old records remain verifiably retrievable.** Every actual provider/account, storage budget and retention horizon is finite. LFS or cloud object storage changes the payload location; it does not remove capacity, cost or retention requirements.

## 8. Fast reads without weakening the archive

Use a small current pointer and indexes keyed by project, record type, source identity and epoch. A reader first loads the pointer and relevant segment manifests, then only requested records or objects. Cache classifications using source, scope and policy identities. Retain negative-search coverage and its invalidation conditions.

Compact MEMORY.md, procedure selection and search indexes are derived views. They may be replaced and rebuilt from sealed records. Changes to a summary are not retroactive changes to the historical evidence. Avoid adding a full archive snapshot for an unchanged scheduler heartbeat; an actionable delta or changed blocker merits a new record.

This separates storage growth from context growth: the archive may grow while the model reads a bounded relevant slice. Actual context and latency improvements should be measured on a declared workload. No “infinite context” or quantitative speedup is established by the design.

## 9. Future implementation gates

These are requirements to test only when a storage implementation is separately admitted. They are not tests executed or passed in this documentation task.

| Case | Required result |
| --- | --- |
| Modify or delete a sealed record in a fast-forward commit | Write gate rejects it |
| Retry identical event ID and payload | Idempotent result; no duplicate logical event |
| Reuse event ID with different payload | Explicit collision failure; old record survives |
| Two producers publish concurrently | No lost records; stale writer retries against current state |
| Crash at each Git/cloud boundary | Replay reaches a consistent state without fabricating missing receipts |
| Upload response succeeds but readback differs | Replica is not verified; cache eviction remains ineligible |
| Missing expected binary | No invented observed digest; availability stays explicit |
| Wrong release architecture or self-supplied trust key | No upstream-authenticity promotion |
| Source changes during capture | Unstable capture is rejected or explicitly deferred |
| Windows-invalid source path or cloud placeholder | Portable object key preserves original locator; unavailable bytes stay pending |
| Untrusted record contains shell instructions | Record remains data; execution requires the current admitted procedure/scope |
| Segment/directory/epoch budget is reached | Checkpoint and bounded rollover, with no silent omission |
| Restore an older epoch without current derived indexes | Records and digests remain resolvable; indexes can be rebuilt |
| Repository administrator bypasses ordinary write policy | Risk is explicit; independent retention provides the required remaining protection |

Correctness must be demonstrated against the intended failure model. A checksum test alone does not demonstrate multiwriter safety, and a schema-fixture pass does not demonstrate durable storage. The current v2 independent-qualification boundary remains intact.

## 10. Smallest useful evolution

**Completed by this documentation release:** source-pinned comparison, 36 indexed techniques, operating sequence, explicit append-only semantics, sizing model and implementation acceptance questions. These live in `rhea-project:stash` so they are recoverable without modifying the legacy playbook.

**Future, separate decision:** admit a procedure/observation/artifact schema family and its serialization contract; implement a bounded spool and a single-writer publication path; then verify retries, collisions and crash recovery against the gates above. Only after that evidence should Omnia be described as an operational register. Cloud adapters and retention expansion follow their own concrete capability and identity checks.

Do not start by committing all leftover bytes into omnia-playbook or by reusing its generated `reports/` directory as a permanent ledger. Start with explicit roles, exact identities and bounded immutable segments. This preserves the useful catalog structure while making the missing storage guarantees visible and testable.
