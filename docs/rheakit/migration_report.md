# Rhea Cloud Asset Migration Report (logs/migration_report.md)

**Generated:** 2026-03-11 10:25 UTC  
**Status:** Selective Migration in Progress  

---

## ✅ Migrated Assets

| Directory | Remote Target | Status | Notes |
|:----------|:--------------|:-------|:------|
| `docs/` | `gdrive_secure:docs` | In Progress | Transferred via --transfers 32 |
| `packages/` | `gdrive_secure:packages` | In Progress | Transferred via --transfers 32 |

## 📁 Local SSD Strategy (Source of Truth)

| Directory | Strategy | Status | Notes |
|:----------|:---------|:-------|:------|
| `src/` | Local SSD | ✅ Local | Primary development core. |
| `.git/` | Local SSD | ✅ Local | Authoritative history (8.5GB). |
| `rhea-session-server/` | Local SSD | ✅ Local | In-memory performance required. |
| `rhea-dash/` | Local SSD | ✅ Local | Frontend core. |

## 🏗️ Migration Architecture

- **Rclone Remote:** `gdrive_secure` (filename_encryption=obfuscate)
- **Encryption:** Obfuscated filenames for enhanced security.
- **Flags:** `--transfers 32 --checkers 32 --drive-chunk-size 64M`
- **Logs:** `logs/migration_docs.log`, `logs/migration_packages.log`

---

**Rules:**
1. All heavy assets MUST be synced to the `gdrive_secure` remote.
2. Symlinks will be used to maintain project structure if needed.
3. The `.git` directory MUST remain local on the SSD for high-performance operations.
