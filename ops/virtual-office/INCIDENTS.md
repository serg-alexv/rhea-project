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

### INC-2026-02-16-006: Rex (LEAD) crashed with 400
- **Symptom:** Rex session dropped with HTTP 400 error
- **Root cause:** Likely related to INC-001 (400 Bad Request pattern) or context window overflow — Rex had been running extended autonomous session
- **Last commit before crash:** b604627 (DEC-009 + consensus_analyzer.py, 729 lines)
- **Data loss:** NONE — all work committed and pushed before crash
- **Status:** DOWN — LEAD offline
- **Impact:** No routing authority (only LEAD reads/routes inbox per OFFICE.md rules)
- **Workaround:** Argos (COWORK) monitoring office, human can restart Rex in rh.1 terminal
- **Verify:** Rex comes back online, heartbeat via Firebase or new commit
- **Next test:** Check rh.1 terminal error output for exact 400 payload

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

### INC-2026-02-16-007: Azure Foundry catalog broken for Jais
- **Symptom:** Jais 30B Chat not found in Azure catalog search (382 models only)
- **Root cause:** Microsoft rebranded Azure AI Foundry → Microsoft Foundry (~Nov 2025). Old catalog had 11K+ models, new has 382 curated.
- **Workaround:** Marketplace listing alive: core42.core42-jais30b-v3-chat-offer
- **Status:** DEFERRED
- **Source:** COWORK_20260216_session-memory.md Turn 12
