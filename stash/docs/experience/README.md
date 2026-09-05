# Preservation engineering experience register

Version **1.0.0**. Evidence cutoff: **2026-09-05 UTC / 2026-09-06 Europe/Moscow**. Scope: the supplied WD maps and binary audit, the RHEA preservation and memory sessions, and a source inspection of omnia-playbook. This is a documentation release on `rhea-project:stash`.

## Read only what the task needs

| Need | Entry point |
| --- | --- |
| Find, assess, preserve, publish or resume leftovers | [Field manual: 36 techniques](FIELD_MANUAL.md) |
| Decide whether Omnia can host an append-only register | [Omnia capacity assessment and proposed architecture](OMNIA_APPEND_ONLY.md) |
| Select techniques without loading the manual | [Machine-readable technique index](techniques.json) |
| Reproduce the source comparison | [Exact source revisions and inspected blobs](sources.json) |
| Execute the already established preservation process | [Protocol 1.1.0](../../protocol/LEFTOVER_PRESERVATION.md) and [task genome](../../protocol/task-genome.json) |
| Resume collection on the actual Windows machine | [WD handoff](../../protocol/RESUME_ON_WD.md) |

**Decision:** use omnia-playbook's taxonomy to describe procedures and invariants. Its inspected implementation is not an append-only artifact register. Keep reviewed records and manifests in Git, large/private objects in appropriate durable storage, and rebuildable indexes outside the immutable record layer. Open-ended growth requires bounded segments and storage expansion; a single Git repository cannot provide infinite capacity.

The `stash` branch contains both immutable-by-procedure run/object paths and mutable documentation/current-state projections. Whole-branch append-only enforcement has not been established. Existing reports, maps and receipts remain intact. This release adds documentation; it does not implement or qualify a storage runtime.

## Boundaries that a reader must retain

- WD, its reported `G:\` Drive mount and `C:\Users\wheel\iCloudDrive`, Redis and the original `log.0` were not accessible from the inspected Linux execution environment. Their complete recovery remains pending; **0 WD bytes were freed**.
- The earlier Google Drive archive was downloaded back and its SHA-256 verified. It contains the accessible preservation package, not the uncollected WD corpus. This documentation release is a later Git addition; it is not silently included in that earlier ZIP.
- Omnia assessment baseline: `timelabs-npo/omnia-playbook@c9220eee388bba1b4d256d0a6ebd241cf5060102`; RHEA archive input: `6ac41f6183e6539e9a3f9796bc0536b87a12f9b2`.
- The current v2 contract boundary remains separate. No legacy integration, component tests/builds, CI repair, gate edits or PASS assertions are part of this release.

“All experience” here means the available evidence in the declared corpus. It does not claim recovery of every past agent session, archive interior or remote machine. Technique status distinguishes observations from recommended generalizations and proposed mechanisms. No measured token-saving percentage or throughput result is available.

For selective local retrieval, filter the index before loading a manual section. For example, from this directory with `jq` available:

```sh
jq '.techniques[] | select(.phase == "publication") | {id,title,detail}' techniques.json
```

The index's shared guard applies to every entry: read the linked conditions before applying a recipe. Index membership never grants execution authority.

## Change record

`1.0.0`: extract 36 indexed techniques; separate evidence, custody and qualification; compare the actual Omnia schemas and writers; specify a proposed bounded append-only design, failure recovery and future acceptance criteria. The operational preservation genome remains at 1.1.0. Future changes to operational authority or storage semantics require their own versioned migration, not an edit to this historical assessment.
