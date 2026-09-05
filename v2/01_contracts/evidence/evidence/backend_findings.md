# Backend evidence findings — frozen baseline, 2026-09-05

Read-only source analysis; no source executable, build, provider request, database mutation, deployment or hardware probe was run. The 39 flat records in `backend_records.json` bind each claim to repository SHA, original source lines and file hash; a snapshot hash is present only if the file is included in the patched pack. `Make` and `Dockerfile` are supplemental source evidence, not falsely represented as packed content.

## Baselines and scope

- `rheknel`: `6e605c5077b561c5330b505fef3e6654fbb852dd`; 19 tracked paths, one C source plus standalone build recipe. STEP1 0 selected files, patched selection 2.
- `omnia-vault`: `f5995536fede02d403f0525ff9093996457efecb`; patched selection 29 versus STEP1 2.
- `rhea-project`: `75cb31e59ccc4f436a428811cb70bbc495254821`; actual Tribunal is `src/tribunal_api.py`, with `rhea_bridge.py`, `consensus_analyzer.py` and `rhea_db.py`; patched selection 193 versus STEP1 38.
- Named local `/Users/sa/Documents/ChatGPT/Rheknel + mbsd + tribunal` has only `.git`, unborn HEAD, no remote, no source files. This establishes no local implementation. Hashed receipt copied to `outputs/rhea-architecture/evidence/local-network-inventory.json`.
- Complete tracked-path inventory and bounded negative-search locations are in `outputs/rhea-architecture/evidence/backend_scope_index.json`. The index includes paths/term hits only, never implementation bodies or credentials.

## Source-grounded conflicts

1. **BC-01 — Typed commit authority is missing from the current Rheknel baseline.** RHK.001–RHK.008 expose opaque C context pointers and callback registries. No typed `CommitValidator`, canonical revision object, expected generation or authority token is present in the inspected 19-path source tree. Do not import later local-only commit-validator claims into this remote SHA.
2. **BC-02 — Judgment does not govern dispatch at the public boundary.** RHK.004 allows an unknown judge tag; RHK.005 dispatches without judging. The example main sequences them, but another caller can invoke emit directly. RHK.003 can report successful registration after the callback array is already full. These are static control-flow findings, not executed failures.
3. **BC-03 — Three separate Omnia state views.** OMN.001–OMN.006 show JS event SQLite and independent Rust stub SQLite. OMN.012 adds an in-memory mock file array. None is a common canonical head. Do not describe this as two existing competing heads: the observed problem is disconnected state plus the absence of the proposed durable head.
4. **BC-04 — WAL is not the intended causal transaction.** OMN.004 performs three independent inserts, random/time IDs and null parent. OMN.005 returns timestamp-sorted rows. OMN.017 specifies a proposed generation-checked canonical revision protocol and explicitly distinguishes it from current code.
5. **BC-05 — Object identity differs by subsystem.** OMN.002/OMN.004 hash UTF-8 event contents; OMN.008 hashes the path string for filesystem storage. There is no common versioned `ObjectId` type or byte-hash contract joining these paths. Native move/copy/link/DB operations are separate, with DB errors ignored.
6. **BC-06 — Transport success is mistaken for operation success.** OMN.007/OMN.008 Rust returns JSON error status with an ordinary JSON response; OMN.013 checks only fetch `response.ok`, then marks the mock entry stubbed/hydrated and returns outer success. The API needs an explicit typed result/error contract before UI state can be trusted.
7. **BC-07 — Projection identity and authorization are inconsistent.** OMN.010 recognizes targets containing `.nebula_vault_store`, while stubbing writes `VaultData`. OMN.007–OMN.011 accept raw paths without an item/revision capability; OMN.016 performs prefix validation then shell interpolation. A path string is currently doing several unrelated jobs: source locator, object-name input and control authority.
8. **BC-08 — Tribunal consensus and Rheknel verdict are different contracts.** TRB.002–TRB.007 expose variable-k provider calls, heuristic text agreement and confidence. RHK.001 is a three-way enum; there is no observed import/call converting one into an authenticated deterministic commit decision. Treating them as interchangeable would invent an authority edge.
9. **BC-09 — Tribunal history is not a durable revision rollback protocol.** TRB.008–TRB.010 append volatile session state and separately persist a selected SQL representation; SQL exceptions are swallowed. TRB.013 rewind reads one in-memory entry without truncation or undoing effects. It is not an atomic ref swap or restart-safe causal restore.
10. **BC-10 — Native triple-model integration is unverified and unsupported by inspected source.** TRB.014 observes a Python3.11-slim image and Python entrypoint; TRB.005/TRB.006 show variable model selection and LiteLLM calls. RHK.007 builds one C demonstration. Bounded search found no Ollama/Rheknel/OpenBSD integration in the Tribunal backend/build scope. This does not prove no such work exists on another host or branch.
11. **BC-11 — Control receipts lack the storage consistency fields.** TRB.011 commands/receipts use in-memory queues, free-form status/action strings and short IDs. They lack expected revision, capability scope and idempotency identity; polling/receipt decorators differ from protected enqueue routes. This is a separate control-plane contract gap, not proof about live exposure.

## Observed dependency edges

| Producer / caller | Consumer / callee | Evidence |
|---|---|---|
| Node `addLog` | GCCmp `commitEvent` | OMN.014 → OMN.004 |
| Node cloud/offload APIs | Rust stub/restore handlers | OMN.011/OMN.013 → OMN.008/OMN.009 |
| Rust stub/restore | filesystem and `stubbed_files` | OMN.008/OMN.009 → OMN.006 |
| Node status/files | `mockLocalFiles` | OMN.012 |
| Tribunal HTTP API | `RheaBridge.tribunal` | TRB.008 → TRB.005 |
| Bridge tribunal | concurrent `ask`, then `ConsensusAnalyzer.analyze` | TRB.005 → TRB.006/TRB.007 |
| Bridge ask | LiteLLM + profile/visual context | TRB.006 |
| Tribunal HTTP API | volatile session list + `rhea_db.persist_history` | TRB.008 → TRB.010 |
| Rheknel demonstration main | judge followed by emit | RHK.007 → RHK.004/RHK.005 |

No shared Rheknel↔Omnia↔Tribunal authority edge was established. The Node storage router and Tribunal API are separate coordination hubs in their own subgraphs. A single system-wide key component cannot be claimed as currently implemented from these backend sources. A future shared revision/validation authority may be justified by BC-01/03/04/05/08, but must be labelled a proposal and then validated against Presentation and Network records.

## Extraction result

Patched native Repomix 1.18.0 configuration retains the original languages and adds Rust/C/C++/Objective-C/Objective-C++/TSX/JSX/JavaScript/Python/SQL plus structural/platform manifests. It includes selected architecture/contract Markdown and removes conflicting blanket Markdown/text ignores. Ten frozen repositories produced 429 files, with zero scanner exclusions and all source clones unchanged. Manifest and file hashes are in `outputs/rhea-architecture/extraction_manifest.json`.

Default ignores, explicit tests/build/vendor/assets exclusions and the 50 MiB input limit remain coverage boundaries. Uncompressed text may normalize outer whitespace; hashes identify pack bytes and original source separately. No one should treat a packed declaration, checked-in build recipe, test source, binary filename or documentation claim as execution proof.
