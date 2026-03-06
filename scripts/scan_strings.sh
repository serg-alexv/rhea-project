#!/bin/bash
# scan_strings.sh - Mining high-signal strings from docs mirror

OUT_FILE="artifacts/hits.jsonl"
mkdir -p artifacts

echo "Scanning for Firebase/Firestore endpoints..."
rg -i "firestore\.googleapis\.com|/databases/\(default\)/documents|identitytoolkit|firebase|firebaseapp|googleapis|accounts:signUp" docs/restore -S --json > "$OUT_FILE"

echo "Scanning for Play model hints..."
rg -i "pageComponent|page_components|pageComponents|clientGeneratedAssets|pageThumbnails|project|share|export" docs/restore -S --json >> "$OUT_FILE"

echo "Scanning for JSON schema-like keys..."
rg -i '"id"|"componentId"|"pageId"|"node"|"layers"|"props"|"variant"|"constraints"' docs/restore -S --json >> "$OUT_FILE"

echo "Scan complete. Hits saved to $OUT_FILE"
