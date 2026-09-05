# Technical documentation index

**Status: DESIGN_ONLY.** This documentation organizes the selected architecture and the next contract-preparation task. No document here is a test receipt, a frozen byte contract, or authority to unlock implementation.

## Start and design

| Document | Purpose | Status |
| --- | --- | --- |
| [Repository README](../../README.md) | Vision, bounded problem and all eight components | Branch overview |
| [Workspace README](../README.md) | Trae reading order and Stage 01 scope | Handoff |
| [START_HERE.md](../START_HERE.md) | Exact local workspace/Git arrangement and immediate next work | Local handoff |
| [ROADMAP.md](../ROADMAP.md) | Alpha, v1 and v2 scope and exit requirements | Planned milestones |
| [ARCHITECTURE.txt](../ARCHITECTURE.txt) | Dependency graph, conditional isolation argument and proposed IPC/RPC | Selected design; enforcement unimplemented |
| [TECH_SPEC_LIT_001.md](TECH_SPEC_LIT_001.md) | Transaction ordering, historical receipt rules and recovery oracles | First draft; contract freeze blocked |
| [ASSEMBLY.json](../ASSEMBLY.json) | Machine-readable stages, admissions and gate statuses | All 55 gates `NOT_EXECUTED` |

## Evidence inputs

| Input | Interpretation |
| --- | --- |
| [recomb1.md](../01_contracts/evidence/recomb1.md) | Adversarial review constraining the isolated OMNIA-LIT-001 slice |
| [rhea_semantic_core.json](../01_contracts/evidence/rhea_semantic_core.json) | 99 structural records; source observations and design gaps, not runtime proof |
| [source_registry.json](../01_contracts/evidence/source_registry.json) | Source locations and recorded identities |
| [EVIDENCE_INDEX.md](../01_contracts/evidence/EVIDENCE_INDEX.md) | Bundled evidence map and extraction limitations |
| [extraction_manifest.json](../01_contracts/evidence/extraction_manifest.json) | Expanded extraction inventory |
| [Omnia SOURCE.json](../03_omnia_lit/SOURCE.json) | Frozen Omnia source and the separate future implementation boundary |
| [PREPARATION.json](../PREPARATION.json) | Historical local scaffold receipt; its original no-push state is not current remote status |

The review references `OMNIA-LIT-001_HANDOFF.md` and `OMNIA-LIT-001_ACCEPTANCE.json`. They are **not bundled**. Retrieve and reconcile them, or obtain an explicitly reviewed replacement, before CON-02 and contract freeze. The draft must not silently supply canonical encodings, receipt layouts or unspecified bounds.

## Stage specifications and proof gates

| Stage | Existing authority and gates | Technical work to complete after admission |
| --- | --- | --- |
| 01 | [Instructions](../01_contracts/AGENTS.md), [CON-01–05](../01_contracts/ACCEPTANCE_GATES.md) | Freeze the bounded LIT contract and public vectors |
| 02 | [Instructions](../02_validation/AGENTS.md), [VAL-01–06](../02_validation/ACCEPTANCE_GATES.md) | Independent encoders, complete-ACK observer and versioned fault profiles |
| 03 | [Instructions](../03_omnia_lit/AGENTS.md), [LIT-01–12](../03_omnia_lit/ACCEPTANCE_GATES.md) | Implement and qualify the additive Omnia target against the frozen contract |
| 04 | [Instructions](../04_local_host/AGENTS.md), [HOST-01–06](../04_local_host/ACCEPTANCE_GATES.md) | Freeze identity, bounded IPC, admission and revocation semantics |
| 05 | [Instructions](../05_rhea_play/AGENTS.md), [PLAY-01–06](../05_rhea_play/ACCEPTANCE_GATES.md) | Freeze the typed client contract and native UI state model |
| 06 | [Instructions](../06_advisory_runtime/AGENTS.md), [AI-01–06](../06_advisory_runtime/ACCEPTANCE_GATES.md) | Freeze modality/proposal schemas, worker isolation and native qualification profile |
| 07 | [Instructions](../07_network_executor/AGENTS.md), [NET-01–06](../07_network_executor/ACCEPTANCE_GATES.md) | Freeze effect-specific grants, intent ledger and reconciliation semantics |
| 08 | [Instructions](../08_remote_bridge/AGENTS.md), [RPC-01–08](../08_remote_bridge/ACCEPTANCE_GATES.md) | Freeze peer roles, RPC limits, replay behavior and composition evidence |

Future work listed here is an index of obligations, not a claim that corresponding specifications or implementations already exist. Later domains receive separately versioned contract and oracle reviews; they are not initial LIT dependencies.

## Documentation authority

Use the bundled review and reconciled normative inputs to establish the initial contract. A reviewed, identified contract freeze and its public vectors then govern implementation; this draft must be reconciled to that freeze. Stage gates govern promotion through independent evidence review. If these sources disagree, record and resolve the discrepancy before claiming a gate has passed.

The [workspace instructions](../AGENTS.md) require independent contract, oracle and implementation ownership. A Markdown rule is not a sandbox: CI/controller permissions, build allowlists, OS isolation and negative tests must eventually enforce the boundaries.

Legacy documentation outside `v2/` describes earlier workstreams. The new repository README and roadmap entry point link here so those historical product claims cannot be mistaken for v2 qualification.
