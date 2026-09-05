# Presentation, Core/Apps and edge boundary findings

This contributor inspected frozen source privately and returned 35 compact interface/dataflow records. No source build, native app launch, device test, provider call, repository edit or source-code upload was performed. Current user authorization released STEP 2/3; the previous STEP 1 artifacts remain unchanged.

## Provenance and actual inventory

| Input | Frozen commit / observed local state | Finding |
|---|---|---|
| Actual `/Users/sa/Documents/ChatGPT/Core` | Git toplevel equals path; HEAD unborn; no tracked or working files | Core is an empty app-mapped Git project, not an implementation module (CORE.001) |
| Actual `/Users/sa/Documents/ChatGPT/Apps` | Git toplevel equals path; HEAD unborn; no tracked or working files | Apps is likewise an empty project container (APP.001) |
| `timelabs-npo/rhea-play` | `045c6d379003716a8344b5ac45dad8fdb7848a21` | macOS RheaPlay host, RheaKit client/state package |
| `timelabs-npo/rhea-ios` | `47a23441e2bcf8a5c86c81429a16ede6da9f9963` | iOS/macOS source entrypoints, duplicate RheaKit and keyboard |
| `timelabs-npo/rhea-keyboard` | `d387ecfe77f0db3d411f6f4505b84c2371caeb78` | iOS keyboard library and HTTP client |
| `timelabs-npo/rhea-atlas` | `05d5177bd3d5c4d83e8bcd34f8c5128c7e0bdfa2` | Browser projection, metric state, lazy route plugins |
| `serg-alexv/hme` | `bf78c9908821f4a2ae8f7091e0aea4479e10e053` | C/Rust world-engine and a distinct Windows network-pet artifact |
| `timelabs-npo/Blueshoes` | `9ad954c31d72e4f8a3f49171f799cae140e6b2f1` | Rust edge/runtime, concepts, lineage and network capability types |
| `timelabs-npo/omnia-playbook` | `c9220eee388bba1b4d256d0a6ebd241cf5060102` | Invariant/check schemas and documented directory separation |

All source records include exact line ranges, source-file SHA-256, frozen commit and the patched pack SHA-256. `snapshot_contains_path=false` explicitly identifies supplementary direct reads, particularly docs/manifests. `presentation_inventory.json` preserves complete tracked-file lists for these seven repos, duplicate comparison receipts and project-path checks. Local Core/Apps have separately hashed inventory receipts; no commit is fabricated for them.

## Source-derived dataflow

- RheaPlay/PlayShell → RheaStore → RheaAPI → remote `/health`, `/agents/status`, `/cc/*`, `/aletheia/*`, supervisor and model endpoints. RheaKit is the observed native client/state aggregation point, not established durable domain authority. Its local database initialization declares cache tables but does not itself demonstrate an offline synchronization path. (PLAY.001–004, PLAY.006–010)
- KeyboardViewController ↔ host textDocumentProxy → KeyboardView → TribunalClient → `/keyboard/quick` or `/dialog` → optional free-text/score reply. These response scores are advisory model/UI metadata, not a deterministic grant or verified native OpenBSD tribunal. (APP.005–008)
- Atlas HTTP/SSE endpoints → useAtlasSync conversion/fallback logic → Zustand AtlasState → route/rendering plugins. (APP.011–014)
- hme feature frame → C world_engine_step / analogous Rust Engine.step → integer pose frame → renderer. This supplies an actual constrained application engine; it does not establish a Rhea-wide storage/AI authority. (CORE.002–005)
- Blueshoes runtime imports semantic validation and exposes a typed network capability graph; its own Entity/ProvenanceReceipt types form a separate domain. (EDGE.001–004)

No cross-repository dependency linking hme world-engine, Blueshoes semantic registry and RheaKit into one implemented universal kernel was established by this bounded inspection. That is an evidence limit, not a global absence claim.

## Concrete conflicts for STEP 3

| Conflict | Exact observation | Evidence | Proposed resolution, not implemented |
|---|---|---|---|
| CF-P01 — folder labels vs modules | Actual Core and Apps projects contain only `.git` and have no HEAD | CORE.001, APP.001 | Keep these organizational containers; assign modules from contracts rather than invent code behind labels |
| CF-P02 — copied package ownership | 25/25 Swift files under RheaPlay's RheaKit match Rhea-iOS byte-for-byte; 3/3 keyboard source files match standalone keyboard | APP.004 | One canonical package/version plus client hosts; 28 of 56 paired copies are redundant physical copies at these commits |
| CF-P03 — source availability vs native packaging | rhea-ios's two project.yml files contain 10 checked relative package/source references that do not exist at their resolved paths; keyboard repo is a library | APP.002, APP.003, APP.005 | Fix a selected source root/project generator and independently qualify iOS/macOS builds/signing; do not infer shipping clients |
| CF-P04 — single HTTP authority assertion | RheaAPI comment claims every pane uses it, but History fetch directly calls URLSession and supplies its own auth header | PLAY.004, PLAY.012 | Route transport/auth through one injected client per host; verify by source/API boundary checks |
| CF-P05 — missing/false and unavailable/empty | AgentDTO optional lease_expired/hard_fail become false and lease token becomes 0; RheaStore errors yield empty arrays; connectionAlive tracks only agent fetch | PLAY.003, PLAY.010 | Model `unknown`, `unavailable`, `stale`, and `observed empty` explicitly; retain timestamps/error evidence |
| CF-P06 — incompatible health contracts | Native HealthSnapshot requires seven fields; browser accepts several endpoint shapes and treats any nonempty object as healthy | PLAY.004, APP.012 | Shared versioned health/readiness projection with typed availability and origin/time |
| CF-P07 — fabricated or retained metrics | Atlas initial score 94 and D=243.8; fallback D=audit_records*0.05+243.8; OR fallback and positive-only setters drop valid zero values | APP.011–013 | Separate measured, derived, fixture and unknown values; carry formula/provenance; accept valid zero without truthiness coercion |
| CF-P08 — local/remote endpoint ownership | Native simulator defaults localhost:8400; Atlas defaults localhost:8000; non-simulator migration rewrites selected local/private URLs to production | PLAY.011 | Explicit endpoint profile with user intent and no blanket conversion of deliberate local endpoints |
| CF-P09 — same word, distinct authority/type | `agreement_score:Double?`, `consensusScore:number`, world `frame_hash:u64`, receipt `transformation_hash:String`, and `generation:u64` do not have interchangeable meanings | APP.008, APP.011, CORE.004, EDGE.003 | Namespace epistemic score, render integrity, cryptographic identity, receipt sequence and storage revision/generation types |
| CF-P10 — Core semantic free strings | Blueshoes closes ConceptType variants but Entity properties/Relation predicates remain strings; Playbook expected_state/output are open objects | EDGE.002, CORE.006–007 | Introduce versioned per-domain payload schemas only where executable contracts need them; do not pretend a flat dictionary already solves value semantics |
| CF-P11 — Keyki identity unsupported | No case-insensitive Keyki match in the three inspected Rhea native/keyboard repos, while actual RheaKeyboard has the requested functional role | APP.010 | Mark Keyki → RheaKeyboard as a proposed legacy mapping pending identity confirmation |
| CF-P12 — mobile and research spill | Existing RheaPlay panes include NDI and other wide operations surfaces, while Omnia MVP v1 remains desktop filesystem management | PLAY.001, APP.002, APP.008 | Make Omnia capabilities/scope explicit in its client projection; copied legacy panes do not release v2 features |

These conflicts are precise source-derived reasons for later decisions. They are not a request to implement patches during extraction.

## Native-platform claim boundaries

- **macOS:** RheaPlay has a macOS 14 target, concrete SwiftUI app source and local RheaKit path. No compilation, signing, notarization or execution was performed here. (PLAY.001–002)
- **iOS:** RheaPreview and keyboard source exist. The observed project path issues prevent inferring a self-contained build from declarations; keychain service naming does not establish entitlements or device access. No TestFlight/device verification. (APP.002–007)
- **Windows:** hme's checked-in `World2NetworkDragon.exe` is 718,336 bytes and has measured SHA-256 `b2107825ff8d582fb0f23a9f099c943f2cf036bdf0f125fd0c589e57b8d194d7`, exactly matching the release manifest. That verifies artifact identity only; it is a network-pet app, not the Windows Omnia/RheaPlay client. It was not executed. (APP.016)
- **C/Rust and Lens:** Analogous source APIs exist; README reports historical parity tests and explicitly pending Lens/live-WLAN runtime gates. Treat historical claims separately from current source/receipt checks. (CORE.003–005)

## Legacy mapping candidates

| Legacy name | Source-backed role/candidate | Confidence |
|---|---|---|
| Core (systems) | Organizational container for independently versioned domain cores; hme engine and Blueshoes semantic/executor contracts are actual separate modules | Container observed; placement proposed |
| Apps (users) | Organizational container for RheaPlay, Rhea-iOS, Atlas, keyboard and separate hme Windows app | Container observed; grouping proposed |
| Rhea-play | macOS operations host plus shared RheaKit API/state package | Observed |
| Keyki | RheaKeyboard/iOS keyboard extension role | Candidate alias only |
| Blueshoes (marketing) | Blueshoes edge/runtime + typed network capabilities; marketing is only a workspace label | Runtime observed |
| Omnia (continuation) / omnia-playbook | Invariant/check/environment contract scaffold distinct from storage engine | Observed; no merger asserted |
| hme | World-engine and network-conditioned rendering application | Observed |

The most defensible presentation simplification is one source of shared client contracts, explicit client projections and typed provenance-aware view state. Selecting the actual cross-system Key Component still requires integration with the other contributors' data-plane and network/AI records.
