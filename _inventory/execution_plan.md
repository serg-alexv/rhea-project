# Execution Plan

## Selected immediate next phase
**Structured metadata extraction** (JSON key-frequency + ingest readiness for Firebase/Play corpora).

## Why this phase was selected
- Strongest evidence concentration is in `firebase_data` + `ios/play-extraction` metadata artifacts.
- Correlation map shows repeatable entity keys across docs/json/assets, making schema-first extraction high leverage.
- This phase is read-only against originals and produces reusable ingest artifacts.

## Started now
- Generated `_inventory/firebase_metadata_keyfreq.csv` from Firebase/Play JSON corpus.
- Prepared candidate sets (`firebase_candidates.csv`, `ui_candidates.csv`) for subsequent ingest pairing.

## Rollback / safety
- No original files modified.
- All generated artifacts are confined to `_inventory/` and can be removed independently.
