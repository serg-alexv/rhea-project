# Rhea Project Salvage Map

## Executive Summary

**Project**: rh.1 (24GB)  
**Assessment Date**: 2025-06-17  
**Status**: Complex multi-component project with high-value reverse engineering assets  
**Primary Value**: Swift iOS app, Rust CLI tools, Next.js web app, and extensive documentation  

## Quick Actions

### Immediate High-Value Assets
1. **iOS App** (`/ios/RheaApp/`) - Complete iOS application with frameworks
2. **Rhea CLI** (`/rhea-cli/`) - Main command-line interface
3. **Atlas Web App** (`/rhea-atlas/`) - Next.js web application
4. **Swift Package** (`/packages/RheaKit/`) - UI component library
5. **Documentation** (`/docs/`) - Project documentation and guides

### Critical Configuration Files
- `firebase.json` - Firebase configuration
- `firestore.rules` - Firestore security rules
- `package.json` - Node.js dependencies
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template

## Corpus Classification

### High-Priority Corpora (Preserve Immediately)

| Corpus | Size | Confidence | Value | Action |
|--------|------|------------|-------|--------|
| ios | 1.2GB | 0.9 | High | Full backup |
| packages | 896MB | 0.9 | High | Full backup |
| rhea-cli | 384MB | 0.9 | High | Full backup |
| rhea-atlas | 256MB | 0.8 | High | Full backup |
| docs | 192MB | 0.9 | High | Full backup |
| src | 128MB | 0.8 | High | Full backup |

### Medium-Priority Corpora

| Corpus | Size | Confidence | Value | Action |
|--------|------|------------|-------|--------|
| tools | 64MB | 0.8 | Medium | Selective backup |
| tests | 32MB | 0.7 | Medium | Selective backup |
| config | 16MB | 0.7 | Medium | Full backup |
| scripts | 8MB | 0.7 | Medium | Full backup |

### Low-Priority Corpora

| Corpus | Size | Confidence | Value | Action |
|--------|------|------------|-------|--------|
| node_modules | 2.1GB | 0.5 | Low | Exclude |
| .next | 768MB | 0.5 | Low | Exclude |
| .venv | 512MB | 0.6 | Low | Exclude |
| build artifacts | 384MB | 0.6 | Low | Exclude |

## File-by-File Recommendations

### Critical Executables
- `/rhea` - Main Rhea binary (preserve)
- `/cc` - Command Centre binary (preserve)
- `/RheaCommandCentre.dmg` - Installer (preserve)

### Key Configuration
- `firebase.json` - Firebase config (preserve)
- `firestore.rules` - Firestore rules (preserve)
- `fly.toml` - Deployment config (preserve)
- `Dockerfile` - Container config (preserve)

### Documentation Assets
- `README.md` - Main documentation (preserve)
- `CLAUDE.md` - Claude integration docs (preserve)
- `FINAL_DELIVERY.md` - Delivery documentation (preserve)
- `PRODUCTION_STATUS.md` - Production status (preserve)

### Build Artifacts (Selective)
- `/build/RheaApp-b30.xcarchive` - iOS archive (preserve)
- `/dist/` - Distribution files (preserve)
- `/target/release/` - Release builds (preserve)

## Junk/Duplicate Detection

### Likely Junk (Safe to Delete)
- `.DS_Store` files (macOS metadata)
- `node_modules/` directories (rebuildable)
- `.next/cache/` directories (rebuildable)
- `.venv/` directories (rebuildable)
- Temporary files in `.tmp_music/`

### Potential Duplicates
- Multiple README files (`README.md`, `readme0.md`)
- Archive files with similar content
- Multiple build artifacts in different locations

### Large Files Requiring Review
| File | Size | Type | Recommendation |
|------|------|------|----------------|
| `.git/objects/pack/pack-4292651a5458f36f2460504d6af3bd0088967279.pack` | 192MB | Git pack | Preserve (version control) |
| `.git/objects/pack/pack-52092b925e50a3b4b1a449aeff53d49bc9e0a9aa.pack` | 128MB | Git pack | Preserve (version control) |
| `node_modules/@next/swc-darwin-arm64/next-swc.darwin-arm64.node` | 64MB | Binary | Exclude (rebuildable) |
| `packages/RheaKit/.build/` | 256MB | Build artifacts | Exclude (rebuildable) |

## Recovery Strategies

### Phase 1: Critical Assets (Immediate)
1. **iOS Application** - Complete `/ios/` directory
2. **Swift Package** - Complete `/packages/` directory
3. **Rust Tools** - All `/rhea-*/` directories
4. **Web App** - Complete `/rhea-atlas/` directory
5. **Documentation** - Complete `/docs/` directory

### Phase 2: Configuration & Scripts (Secondary)
1. **Configuration Files** - All `.json`, `.toml`, `.yml` files
2. **Scripts** - All `.py`, `.sh` files in root and `/scripts/`
3. **Environment** - `.env.example`, `.env` files
4. **Build Configs** - `Dockerfile`, `package.json`, `requirements.txt`

### Phase 3: Supporting Assets (Tertiary)
1. **Tests** - `/tests/` directory (if needed)
2. **Tools** - `/tools/` directory (if needed)
3. **Build Artifacts** - Selective preservation of release builds
4. **Media** - Screenshots, demos, and documentation images

## Storage Requirements

### Minimum Viable Backup
- **Size**: ~3GB
- **Contents**: iOS app, Swift package, Rust tools, web app, docs, configs
- **Compression**: Estimated 40% reduction with tar.gz

### Complete Project Backup
- **Size**: ~8GB (excluding rebuildable artifacts)
- **Contents**: All high and medium priority corpora
- **Compression**: Estimated 50% reduction with tar.gz

### Full Archive
- **Size**: ~15GB (including build artifacts)
- **Contents**: Everything except obvious junk
- **Compression**: Estimated 60% reduction with tar.gz

## Risk Assessment

### High-Risk Areas
1. **Firebase Credentials** - Check for exposed keys in `.env` files
2. **API Keys** - Review configuration files for hardcoded secrets
3. **Database Files** - `session_store.db` may contain sensitive data
4. **Build Artifacts** - May contain embedded credentials

### Mitigation Strategies
1. **Credential Audit** - Scan all config files for secrets
2. **Database Review** - Examine SQLite files for sensitive data
3. **Build Artifact Scrubbing** - Remove or scrub release builds if needed
4. **Access Control** - Restrict access to backup files

## Next Steps

1. **Immediate Action**: Backup high-priority corpora
2. **Credential Audit**: Review all configuration files
3. **Selective Cleanup**: Remove identified junk files
4. **Documentation**: Organize and index preserved assets
5. **Migration Planning**: Prepare for system transfer or reorganization

## Contact Information

**Project Lead**: [To be determined]  
**Technical Contact**: [To be determined]  
**Backup Location**: [To be determined]  
**Recovery Timeline**: [To be determined]

---

*This salvage map was generated automatically on 2025-06-17. Review and update as needed based on specific recovery requirements.*