# Preservation protocol changes

## 1.0.0 — initial preservation recipe

- Evidence: supplied WD maps, binary-provenance findings and `2026-09-06-cloud-001` capability check.
- Added SHA-256 object addressing, source locators, explicit availability/storage distinctions, append-only runs and a pending queue.
- Separated the archival `stash` branch from the report PR targeting `rhea-project-v2`.
- Recorded the incomplete Rhea checkout, sensitive VM/key media and absent Blueshoes B0 binaries as distinct collection cases.
- Added resume rules that reuse hashes and observations and keep expensive corpus reading out of repeated model context.
- Validation for the initial run covers supplied artifact bytes, manifest consistency and remote publication identities. This recipe has not yet been executed against the WD filesystem.
- Compatibility: schema `rhea-leftover-run/1`, genome `rhea-leftover-preservation/1.0.0`.
- Rollback: use a previous protocol commit; retained object/run history is not deleted.

## Required fields for a future change

Version; motivating evidence/run; previous behavior; change; expected benefit; verification performed and its limits; migration; rollback. Record authority/scope changes explicitly and obtain applicable authorization before using expanded access.
