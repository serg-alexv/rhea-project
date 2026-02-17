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

### INC-2026-02-16-006: Rex (LEAD) — Anthropic daily token quota exhausted
- **Symptom:** Rex session returns `400 You have exceeded your daily token limit. You can resume at 2026-02-18 00:00 UTC`
- **Root cause:** Anthropic daily token limit hit (NOT a bug — quota cap). Rex had 25+ hour uptime before this.
- **Previous misdiagnosis:** Initially thought to be session crash (INC-001 pattern). Actually transient 400 on Feb 16, recovered. Now hard quota limit on Feb 17.
- **Data loss:** NONE — Rex read B2's P0 message before dying.
- **Status:** DOWN — LEAD offline until 2026-02-18 00:00 UTC
- **Impact:** No routing authority until quota resets
- **Workaround:** B2 continuing all work. Firebase messages queued for Rex.
- **Verify:** Rex starts responding after midnight UTC
- **Next test:** Implement hard token budget + provider fallback (OpenAI/Gemini) to avoid future exhaustion

### INC-2026-02-16-005: Chrome JS execution rejected
- **Symptom:** osascript Chrome JS command rejected by user permission
- **Root cause:** Security concern about JS execution in browser
- **Workaround:** Alternative extraction method needed (API, manual copy, export)
- **Status:** BLOCKED
- **Verify:** Attempt osascript command; confirm permission prompt or allow list works
- **Rollback:** Use manual export or API-based extraction; avoid osascript entirely
- **Next test:** Check Chrome automation policies; try CDPv11 protocol or browser extension instead

### INC-2026-02-16-006: ComfyUI Docker image broken
- **Symptom:** `ai-dock/comfyui:pytorch-2.4.1-cpu` removed from ghcr.io
- **Root cause:** Image deleted from registry (upstream)
- **Workaround:** Use `--lite` flag with deploy.sh (skips ComfyUI)
- **Status:** WORKAROUND ACTIVE
- **Source:** COWORK_20260216_agent-online.md
- **Verify:** `docker pull ai-dock/comfyui:pytorch-2.4.1-cpu` — expect 404
- **Next test:** Find replacement image or build from ComfyUI repo

## 2026-02-17

### INC-2026-02-17-001: Gemini API key leaked in git history
- **Symptom:** `AIzaSy*` key found in `.entire/chat_extracts.json` which was tracked in git
- **Root cause:** Entire.io chat extracts file included API response with key, file was not gitignored
- **Fix applied:** File removed from tracking (`git rm --cached`), added to `.gitignore`
- **Status:** MITIGATED — file untracked, but key remains in git history
- **Action needed:** ROTATE the Gemini API key in Google Cloud Console (key is burned)
- **Verify:** `git log -p --all -S 'AIzaSy' | head -5` should show the old commit only

### INC-2026-02-17-002: Firestore rules were wide open (if true)
- **Symptom:** All Firestore collections allowed unauthenticated read/write
- **Root cause:** Initial setup used `allow read, write: if true` for all collections
- **Fix applied:** Rules changed to `request.auth != null`, deployed via `firebase deploy`
- **Status:** RESOLVED — rules deployed, health probe passes with auth
- **Verify:** `ops/rhea_firebase.py health` shows READ + WRITE OK with auth
- **Note:** Service account OAuth2 token auth added to rhea_firebase.py

### INC-2026-02-16-007: Azure Foundry catalog broken for Jais
- **Symptom:** Jais 30B Chat not found in Azure catalog search (382 models only)
- **Root cause:** Microsoft rebranded Azure AI Foundry → Microsoft Foundry (~Nov 2025). Old catalog had 11K+ models, new has 382 curated.
- **Workaround:** Marketplace listing alive: core42.core42-jais30b-v3-chat-offer
- **Status:** DEFERRED
- **Source:** COWORK_20260216_session-memory.md Turn 12
