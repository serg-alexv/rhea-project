# Rhea-Biomolecula Template Encryption & Storage

All templates (scenes, materials, animations, story metadata) now live under `packages/RheaKit/Sources/RheaKit/Resources/templates` and are branded as **Rhea-Biomolecula** objects.

## Naming convention
- File names follow `rhea-biomolecula-<type>-<slug>.json` (e.g., `rhea-biomolecula-scene-aerobic-probiotic.json`).
- In Mongo the collection is named `biomolecula_templates`.
- Each document: `{ "scene": "aerobic-probiotic", "type": "scene", "version": 1, "hash": "...", "created_by": "orion", "encrypted_blob": <base64> }`.

## Encryption process
1. `BIORENDERER_TEMPLATE_KEY` (32-byte AES-256 key) lives in Google Secret Manager / Fly secret.
2. Run the helper (to be added under `scripts/biorendera_encrypt.py` or `rhea-cli biorendera encrypt`) with `--input resources/templates/rhea-biomolecula-<...>.json` and `--env BIORENDERER_TEMPLATE_KEY`.
3. The helper: reads JSON, serializes to UTF-8, encrypts with AES-GCM (nonce stored alongside), base64-encodes cipher, outputs `secure/<name>.enc` in `Resources/templates` and inserts/updates Mongo doc.
4. To export: `rhea-cli biorendera export <scene>` fetches Mongo doc, retrieves key from env, decrypts, loads JSON, renders via BioRenderer, writes PNG/JSON results, and optionally posts to share endpoint.
5. After export, log the event in `docs/orchestrate-log.md` plus Mongo task log (this ensures auditability). Keep the ciphertext only in storage; decrypted payload never touches disk outside the export step.

## Mongo schema (example)
```
{
  "scene": "aerobic-probiotic",
  "type": "scene",
  "version": 1,
  "created_at": "2026-03-03T06:15:00Z",
  "created_by": "orion",
  "hash": "sha256(...)",
  "encrypted_blob": "BASE64(AES-GCM(...))",
  "nonce": "BASE64(...)"
}
```

## Usage
- Add new templates by placing JSON into `Resources/templates`, run the encrypt helper, then commit both the original (for review) and encrypted output.
- On deployment, set `BIORENDERER_TEMPLATE_KEY` via `flyctl secrets set BIORENDERER_TEMPLATE_KEY=<base64 key>` and ensure `TASK_DB_URI` points to Mongo with TLS.
- During export, the CLI/agents read `BIORENDERER_TEMPLATE_KEY`, decrypt the template, render via BioRenderer, and publish or store artifacts.

Want me now to implement `scripts/biorendera_encrypt.py` and document the CLI wrapper under `packages/rhea-cli`?"EOF