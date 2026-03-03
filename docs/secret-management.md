# Secret Management Policy for Rhea

## Goals
- Keep API keys/passwords out of code, git history, and chat logs.
- Store secrets in managed vaults (Keychain, Google Secret Manager, Fly secrets, Atlas secrets) and rotate regularly.
- Share access with agents via documented channels only (Keychain, secure vault) and log rotation events (not values) in infra notes.

## Storage tiers
1. **Local dev**: use macOS Keychain + `~/.rhea_secrets.json` (gitignored). Keychain entries named `Rhea/<service>`.
2. **Cloud**:
   - Fly.io secrets (`flyctl secrets set TASK_DB_URI=...`). These are mounted only at deploy time.
   - MongoDB Atlas secrets stored in Atlas UI (Database Access user) and mirrored to Fly env variables.
   - Google Secret Manager for multi-agent credentials (project `timelabs-npo`). Agents fetch via `gcloud secrets versions access latest --secret <name>`.
3. **Rotation**: rotate every 30 days or after suspected compromise. Log rotation events in `docs/rotation-log.md` (time, responsible agent, surface) without writing the secrets themselves.

## Sharing with agents
- Use Keychain sharing for local work (add `sa`, `rex`, `orion` to shared item). Document location in `docs/secret-management.md`.
- Cloud secrets shared via vault ACLs (Fly team, Atlas project). Notify Rex/hyperion through private relay, never chat.

## How to add a new secret
1. Generate credential securely (password manager or `openssl rand -base64 32`).
2. Store in Keychain + local file (gitignored) for dev.
3. Push to Fly/Atlas/Google Secret Manager.
4. Update `.env.example` to describe variable (without value).
5. Document rotation date in `docs/rotation-log.md`.

## How to rotate
- Rotate by creating new secret value, updating vault, redeploying service (Fly/Atlas), then revoking old entry.
- Log rotation entry in `docs/rotation-log.md` with timestamp/responsible agent + `surface`.

This document can be synced to Google Docs (shared with Rex) via `docs/google-sync.txt` instructions (no secret data). Need me to create the sync note? 
