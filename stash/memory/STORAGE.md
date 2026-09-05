# Typed storage and verified space reclamation

This procedure extends preservation protocol 1.1.0 under the user's request to use Google Drive/iCloud and free local space. It does not start a Rhea storage runtime or change v2 admission.

## Placement

| Data | Primary retention | Secondary/projection | Local retention |
| --- | --- | --- | --- |
| Stable project facts, scope, decisions | Reviewed versioned administrative files on GitHub `stash/memory` | Drive compact snapshot/pointer | Small pinned MEMORY.md and current manifest |
| Personal/private identity and preferences | Explicitly private user-controlled storage | Minimal public working preferences only | Compact permitted context |
| Nexus action receipts | Immutable per-run records, tied to sources and commits | Sealed Drive archive; optional verified iCloud replica | Latest receipt and unresolved cursor |
| log.0 raw events, agent histories | Private append-only segments and retention manifest | Sealed archive; preserve producer/range/omissions | Active segment and necessary replay window |
| Source, patches, small public evidence | Component source history or content-addressed stash archive | Drive sealed snapshot when preservation is requested | Active checkout and unique unuploaded changes |
| Binaries, large archives, VM snapshots | Authorized durable object/archive storage | Verified independent replica as required | Active/unsynced objects only; no VM startup |
| SQLite databases | Local writer-owned DB with a consistent backup procedure | Sealed backup snapshot and manifest | Live DB/WAL/SHM stay together under the writer |
| Redis | Running service's explicitly scoped transient state | Durable ledger holds any state whose loss affects correctness | No raw credential or unbounded source corpus cache |

The same file mirrored through two services is not automatically an independent backup. Record provider, account boundary, object ID, version, digest, size and recovery result. Do not let Google Drive and iCloud both manage the same mutable directory or nest their synchronization roots.

## Sequence: inventory → preserve → verify → release local bytes

The user supplied concrete WD roots during this run: **iCloud `C:\Users\wheel\iCloudDrive`** and **Google Drive `G:\`**. These are user-reported paths. The current Linux runtime cannot resolve them, `/mnt/c/Users/wheel/iCloudDrive` or `/mnt/g`; their existence, hydration state, account association and free space must be observed on WD. Do not guess a `G:\My Drive` child name: list the accessible drive first, then identify the intended account/folder. Preserve this mapping as a lead, not a successful mount check.

1. Identify the actual WD volume and provider roots from the local machine, including whether Google Drive is streaming or mirroring and the iCloud hydration/pinning status. Record filesystem, real paths, source identity and free/allocated bytes. The current cloud runtime cannot supply these measurements.
2. Enumerate unique/uncommitted files and outstanding writers. Never choose a file for removal because it has a cache-like name, appears in an old map, or has an expected hash in somebody else's report.
3. Capture stable bytes with their SHA-256/size and source relation. For a running SQLite DB use an appropriate consistent backup or coordinated offline snapshot; do not copy only `memory.db` while its WAL may hold committed state. Do not hydrate entire cloud trees merely to count filenames.
4. Upload to the correct privacy tier. Verify the actual remote object by re-reading/hashing bytes or trustworthy exact digest metadata, plus its object/version identifier. A successful upload request, placeholder, LFS pointer or sync icon alone does not establish every required copy.
5. For files managed by iCloud for Windows, use the provider's **Free up space** operation after verification: it removes the local downloaded copy while retaining the cloud item. Unpinning alone does not prove bytes were released. [Apple's procedure](https://support.apple.com/en-gb/guide/icloud-windows/icw55f49dfab/icloud).
6. For Google Drive, prefer streaming for the cold archive and explicit offline pinning for the small current memory. Mirroring retains a full local copy. Switching modes requires completed sync; the documented Windows sequence includes quitting Drive before removing the former, no-longer-synced mirror. Do not remove an active synced source directory by analogy. [Google's procedure](https://support.google.com/drive/answer/13401938?hl=en).
7. Remove ordinary temporary duplicate copies only when the exact replacement is verified, no writer/replay task needs them, and their location/role is known. Original unique source/history and evidence remain retained. Cloud deletion propagates differently from local dehydration; do not empty provider trash as a disk-space shortcut.
8. Measure again on the same WD volume. Record attempted bytes, actual allocated bytes released and free-space delta separately; concurrent activity can alter the latter. Report unknown/unavailable measurements as null, never estimate saved GB from logical file lengths.

Current execution: Google Drive read access verified; memory refresh archive upload/readback is recorded in the run's cloud receipt. WD local sync roots and iCloud are unavailable to this runtime. No local eviction or source deletion was executed. WD bytes freed: 0; WD reclaimable bytes: unknown.

## Hot memory economy

Start each task with MEMORY.md, current.json and unresolved items. Cache derived context by source digest, scope and policy version. When those inputs are unchanged, reuse the compact result. A mutable source must be revalidated; filename or mtime alone is insufficient evidence for final byte identity.

Do not store every run's full narrative in the hot context or scheduler prompt. Record immutable receipts separately and keep pointers. Keep soul.md stable and short. Do not truncate raw logs to make the prompt smaller: compact the projection and retain the event segments.

For Redis, inspect type, TTL, memory usage, producer and consumer/replay obligations before any future cleanup. Do not use FLUSHDB/FLUSHALL or broad namespace deletion. Expiring an idempotency key or lock too early can affect correctness; pending jobs and authoritative clocks cannot simply be reclassified as disposable cache. See redis-policy.json.

## Repeat and upgrade

Record every provider mapping and receipt in the current run, update only the compact pointer, and extend the existing WD pending queue with actual newly discovered objects. Protocol version changes must identify the new authority, source evidence, compatibility and rollback. A read-only scheduled watch reports new problems and capability changes; actual eviction runs as a bounded, separately recorded operation under the user's standing cleanup authorization.
