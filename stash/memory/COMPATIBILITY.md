# Compatibility of RHEA memory with the current boundary

Observed during the 2026-09-06 Moscow preservation session. GitHub and Drive sources below were read directly; personal-context retrieval supplied the historical role map. Existing databases, Redis, iCloud and WD storage were not reachable. This is a source/configuration assessment; no runtime or acceptance tests were executed.

## Result by component

| Component | Existing evidence | Compatibility with current constraints | Refresh performed by this change |
| --- | --- | --- | --- |
| rhea-memory | Standalone repository and embedded package implement SQLite facts/timeline. `store.py` has the same Git blob in both checked versions. `remember()` overwrites a key; provenance and owner/scope admission are not enforced by this API. | Suitable as a legacy local store or a conceptual durable-memory role. It is not an admitted implementation of v2 canonical byte contracts, distributed ownership, or independent qualification. | Sourced administrative facts in `rhea-memory.json` and a compact MEMORY.md. Existing code/DB is not modified or run. |
| Nexus | `docs/nexus.md` is a TOML-like v4.2 operator profile: stop for permission after more than one action; compile/smoke for patches; `stop_after_success=false`; a file-ledger lock uses `fcntl.flock`. | Its repetitive permission/verification rules conflict with current authorization and task economy. A local file lock is not a demonstrated cross-machine/cloud replication protocol. Operational evidence remains a useful role. | A dated decision/action record under `nexus/`; current rules in the preservation protocol. Legacy profile remains evidence. |
| soul.md | Multiple Drive versions were found; the 3,215-byte version matches the text of the checked GitHub `docs/soul.md`. It mixes preferences, personal profile assertions, metaphor and universal agent inheritance. | Compact working preferences fit. Old personal assertions are not current measurements; inherited personality does not grant execution or verdict authority. | A compact task-scoped `soul.md`; no health profile imported into operational state and no automatic loading claimed. |
| Redis | Drive assessment treats it as cache; another schema names an authoritative session Lamport clock and permanent snapshot/queue keys. No live endpoint was verified. | Hot cache/coordination is compatible as a future operational role outside the active slice. The authority conflict and durable queue semantics require resolution before reuse. TTL alone does not make locks or idempotency safe. | `redis-policy.json` records the permitted role, prohibited cleanup and exact migration questions. No Redis key changed. |
| log.0 | No exact `log.0` was found among the bounded returned search results or checked GitHub main tree. `0.log`, `p0.log` and `gem0.log` search hits are distinct names. | Raw append-only evidence is compatible. Existence, producer, writer coordination, completeness and retention of the intended original stream remain unknown. | A new, explicitly scoped preservation event segment under `log.0/`; it neither replaces nor claims recovery of the missing original stream. |
| Scheduler | The active Repo Conflict Watch still named rheknel/omnia-playbook/Blueshoes and broad legacy issues. | Its previous scope did not reflect the active v2 isolation/independent-PASS boundary. | Existing automation updated in place; hourly cadence and Moscow timezone retained. No duplicate task created. |

No percentage of runtime compatibility can be derived from these source reads. The role map is usable; the implementations are not qualified for v2 by this audit.

## Concrete source identities

- Current constraint: [v2/AGENTS.md](https://github.com/timelabs-npo/rhea-project/blob/accc8619b179539c3a775844f5f077fbad80715e/v2/AGENTS.md) and [Stage 01 AGENTS](https://github.com/timelabs-npo/rhea-project/blob/accc8619b179539c3a775844f5f077fbad80715e/v2/01_contracts/AGENTS.md). Only contract preparation is admitted; source observations are not qualification.
- Standalone [rhea-memory](https://github.com/timelabs-npo/rhea-memory/tree/5b4a12151f6f2363f9dd32dc87bd4d662bdefb31), `src/rhea_memory/store.py` and embedded [store.py](https://github.com/timelabs-npo/rhea-project/blob/75cb31e59ccc4f436a428811cb70bbc495254821/packages/rhea-memory/src/rhea_memory/store.py): shared Git blob `7872ca97cb00849a744bd14a7ab125bee1d0a738`. Matching this source file does not establish equal runtime state or package behavior.
- Legacy [Nexus profile](https://github.com/timelabs-npo/rhea-project/blob/75cb31e59ccc4f436a428811cb70bbc495254821/docs/nexus.md), blob `50cf4c7c2051807939088c8deea39684a330d46e`.
- Legacy [soul.md](https://github.com/timelabs-npo/rhea-project/blob/75cb31e59ccc4f436a428811cb70bbc495254821/docs/soul.md), blob `53dc09259ea1167d19ea696660439ae55622f4e8`. Drive copies were read as text; no byte-exact identity for a newly downloaded raw copy is claimed.
- Drive `redis-memory-assessment.md`, file `1Tnu8kTIq5_WdoNK6Pc_4W-J1kf6pXVvk`, modified 2026-06-17: cache is useful, not canonical planning truth or approval evidence.
- Drive `REDIS_SCHEMA.md`, file `10SxHLVIRJlKTmgnFFeTN6bcnoFIQXdPa`, modified 2026-06-18: snapshot/session clocks/queue have no TTL and the session clock is called authoritative. These are document statements, not an inspected Redis keyspace.

## Storage implications

`MemoryStore` enables SQLite WAL. SQLite documents that WAL requires processes sharing the same host and that its WAL file can contain committed state absent from the main database file. Therefore this procedure transfers a consistent offline/backup snapshot, not a live `memory.db` as a shared cloud file. This is a storage-policy inference from the implementation and [SQLite WAL documentation](https://www.sqlite.org/wal.html), not a test of a sync provider.

GitHub preserves reviewed public documents and source identities. Google Drive holds sealed archives and read-only projections. iCloud can hold an additional archive replica once access and bytes are verified. Redis holds replaceable hot state only after a separate operational admission. Active working files remain in one local writer's workspace; cloud projections do not arbitrate concurrent writes.

The user authorized utilizing existing cloud links and freeing space. No verified WD local link is visible from the current runtime. Actual WD capacity/reclaimable bytes remain unknown, and **0 WD bytes were freed**. See STORAGE.md for the provider-specific completion conditions.
