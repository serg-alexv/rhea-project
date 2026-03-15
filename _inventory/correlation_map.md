# Correlation Map

## Corpus relationships (explicit)
1. **firebase_data ↔ ui_assets**
   - Evidence: `mirror/firebase_storage/clientGeneratedAssets/pageThumbnails/*` contains UI thumbnail images keyed by IDs.
   - Evidence: `ios/play-extraction/REPORT.md` describes `thumbs` structures and page component IDs.
   - Interpretation: Firebase-origin thumbnails are render derivatives tied to UI component/page entities.

2. **play_docs ↔ firebase_data**
   - Evidence: `ios/play-extraction/REPORT.md` + JSON files in `ios/play-extraction/teams|projects|components|urls`.
   - Interpretation: play extraction is metadata/document surface for Firebase-resident project state.

3. **docs/prompts/protocols ↔ configs**
   - Evidence: `CLAUDE.md`, `prompts/AUTONOMY_WITH_AUDIT_ROOT.md`, `prompts/STICKY_CONTEXT.md`, `.roomodes`, `.roo/mcp.json`, `REDIS_SCHEMA.md`.
   - Interpretation: policy docs + runtime config jointly define execution constraints and memory/state discipline.

4. **reverse ↔ app_bundles**
   - Evidence: reverse markers (`*.bndb`, reverse-related paths) plus compiled bundles (`.next/`, `rhea-atlas-out/`).
   - Interpretation: reverse corpus preserves binary/runtime context while bundle corpus captures deployable derivations.
   - Status: **tentative** where only path-level evidence exists.

5. **sessions ↔ docs/state + office relay**
   - Evidence: `.entire/`, `docs/state.md`, `docs/state_full.md`, `opera/ops/virtual-office/*`.
   - Interpretation: checkpoint/history and relay artifacts form continuity layer for resumable operations.

## Likely information flow
`configs/protocols` -> govern extraction/ops -> `firebase_data` + `play_docs` capture raw/derived app metadata -> `ui_assets` and `app_bundles` materialize user-facing surfaces -> `sessions/state` preserve operational continuity.

## Concept duplication / mirrors
- Page/component IDs appear in multiple forms: text IDs (`ios/play-extraction/components/page_component_ids.txt`), JSON metadata (`thumbs` maps), and thumbnail filenames in Firebase mirror paths.
- Policy constraints duplicated across `CLAUDE.md`, sticky prompt, and protocol docs (intended redundancy).

## Primary vs derived (working judgment)
- Primary candidates: protocol/config/state docs, source trees, extraction JSON metadata.
- Derived candidates: `.next` outputs, bundled chunks, mirrored thumbnail binaries.
- Mixed: `ios/play-extraction/` (contains both source-like metadata and generated summaries).

## Indexing recommendations
- Index together: `ios/play-extraction/**/*.json` + `mirror/firebase_storage/**/pageThumbnails/*` + `ios/play-extraction/REPORT.md` (entity-to-asset linkage).
- Index together: `CLAUDE.md` + `prompts/*.md` + `.roomodes` + `.roo/mcp.json` + `REDIS_SCHEMA.md` (protocol/runtime governance pack).
- Keep separated: build artifacts (`.next`, `rhea-atlas-out`) from source-of-truth docs/config to avoid retrieval pollution.
