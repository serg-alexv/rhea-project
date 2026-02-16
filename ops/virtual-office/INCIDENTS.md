# INCIDENTS — What Broke + Status
> Updated continuously by any agent that discovers a problem.

## 2026-02-16

### INC-2026-02-16-001: Background agents broken
- **Symptom:** All background agents die with 400 Bad Request
- **Root cause:** Unknown (Bonsai was removed, still broken)
- **Workaround:** Foreground-only, 3 concurrent max
- **Status:** WORKAROUND ACTIVE
- **Verify:** Spawn a background sonnet agent, confirm it stays alive for >5 minutes
- **Rollback:** Kill all background processes; re-enable foreground-only mode in orchestration
- **Next test:** Check Bonsai API logs; verify no stale auth tokens

### INC-2026-02-16-002: Bridge 2/6 providers down (was 4/6)
- **LIVE:** OpenAI ✅, OpenRouter ✅, Gemini ✅, DeepSeek ✅
- **DOWN:** Azure 401 (bad credentials), HuggingFace 404 (URL bug)
- **Fixed:** Gemini (keys working), DeepSeek (balance restored), probe stderr bug
- **Status:** IMPROVED — 4/6 live. See docs/procedures/auth-errors.md for remaining fixes.
- **Verify:** `bash ops/bridge-probe.sh`
- **Rollback:** Revert to tier-1 only (OpenAI); disable experimental providers
- **Next test:** Rotate Azure key (manual Microsoft login); fix HuggingFace URL construction

### INC-2026-02-16-003: Python hashlib broken
- **Symptom:** pyenv Python 3.11 throws "unsupported hash type blake2b"
- **Root cause:** Broken OpenSSL linkage in pyenv build
- **Workaround:** Use `/usr/bin/python3` (system) or fix pyenv
- **Status:** WORKAROUND NEEDED
- **Verify:** Run `python3 -c "import hashlib; print(hashlib.blake2b())"` and confirm no error
- **Rollback:** Switch all scripts to use `/usr/bin/python3` instead of pyenv version
- **Next test:** Rebuild pyenv with explicit OpenSSL flags; or update pyenv to latest

### INC-2026-02-16-004: B-2nd rh.1 directory inaccessible
- **Symptom:** B-2nd agent reports "rh.1/ directory now seems gone or inaccessible"
- **Root cause:** B-2nd deleted ~/B-2nd which broke its cwd; may be looking at wrong path
- **Status:** RESOLVED — B2 can read/write /Users/sa/rh.1 (confirmed 22:58 MSK)
- **Verify:** B2 ran probe, edited files, pushed successfully
- **Rollback:** N/A (resolved)
- **Next test:** N/A

### INC-2026-02-16-005: Chrome JS execution rejected
- **Symptom:** osascript Chrome JS command rejected by user permission
- **Root cause:** Security concern about JS execution in browser
- **Workaround:** Alternative extraction method needed (API, manual copy, export)
- **Status:** BLOCKED
- **Verify:** Attempt osascript command; confirm permission prompt or allow list works
- **Rollback:** Use manual export or API-based extraction; avoid osascript entirely
- **Next test:** Check Chrome automation policies; try CDPv11 protocol or browser extension instead
