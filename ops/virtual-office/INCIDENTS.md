# INCIDENTS — What Broke + Status
> Updated continuously by any agent that discovers a problem.

## 2026-02-16

### INC-001: Background agents broken
- **Symptom:** All background agents die with 400 Bad Request
- **Root cause:** Unknown (Bonsai was removed, still broken)
- **Workaround:** Foreground-only, 3 concurrent max
- **Status:** WORKAROUND ACTIVE

### INC-002: Bridge 4/6 providers down
- **Gemini T0:** 429 quota exceeded → check billing
- **Gemini T1:** 400 geo-blocked → use OpenRouter bypass
- **DeepSeek:** 402 insufficient balance → top up
- **Azure:** 401 bad credentials → rotate key (needs manual Microsoft login)
- **HuggingFace:** 404 → URL construction bug in bridge code
- **Status:** KNOWN, DOCUMENTED, WORKAROUND (OpenAI + OpenRouter live)

### INC-003: Python hashlib broken
- **Symptom:** pyenv Python 3.11 throws "unsupported hash type blake2b"
- **Root cause:** Broken OpenSSL linkage in pyenv build
- **Workaround:** Use `/usr/bin/python3` (system) or fix pyenv
- **Status:** WORKAROUND NEEDED

### INC-004: B-2nd rh.1 directory inaccessible
- **Symptom:** B-2nd agent reports "rh.1/ directory now seems gone or inaccessible"
- **Root cause:** B-2nd deleted ~/B-2nd which broke its cwd; may be looking at wrong path
- **Status:** INVESTIGATING (B-2nd is alive, may resolve itself)

### INC-005: Chrome JS execution rejected
- **Symptom:** osascript Chrome JS command rejected by user permission
- **Root cause:** Security concern about JS execution in browser
- **Workaround:** Alternative extraction method needed (API, manual copy, export)
- **Status:** BLOCKED
