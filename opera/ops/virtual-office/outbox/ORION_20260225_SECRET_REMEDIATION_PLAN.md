# ORION — Secret Scanning Remediation Plan
> Agent: ORION (Systems Architect) | Date: 2026-02-25
> Status: ANALYSIS COMPLETE — AWAITING HUMAN APPROVAL BEFORE EXECUTION

---

## 1. SITUATION SUMMARY

GitHub push protection is blocking `git push` on `hyperion/memory` because commit `11ae756` ("Planning: 6 todos") introduced 3 files containing **plaintext API keys** embedded inside dialogue transcripts.

- **Branch:** `hyperion/memory`
- **Blocked commits:** 10 unpushed (11ae756 through 33e82e2)
- **Remote HEAD:** `13205b0` (origin/hyperion/memory)
- **Introducing commit:** `11ae756` — a 200-file, 1.3M-line commit
- **The secrets exist ONLY on this branch, ONLY in this one commit's tree**

---

## 2. SECRETS INVENTORY

### 2a. Files Containing Full (Unredacted) Secrets

| # | File | Size | Lines with secrets |
|---|------|------|--------------------|
| 1 | `users/sa/archives/dialogues/20260220/merged/all_platform_dialogues_merged_20260220.md` | 4.5 MB | 31399, 31403-31406, 31407, 31411, 31414 |
| 2 | `teams/all_platform_dialogues_merged_20260220.md` | 4.5 MB | 31399, 31403-31406, 31407, 31411, 31414 (identical copy) |
| 3 | `users/sa/archives/snapshots/20260220/all_memory/raw/gemini_semantic_delta_snapshot_20260219.md.20260220T071432Z.bak` | 28 MB | Line 716 (OpenAI key only, in a long diff line) |

### 2b. Partially Redacted But Still Flaggable

| # | File | Line | Issue |
|---|------|------|-------|
| 1 | File 1 & 2 above | 7139 | `sk-proj-OpjXgRv-2KeSKHTN--bD4vaRqCaCfT5oDsxoAXMK3O-Ow35xr_[REDACTED]-mBXdXXGQTemJu7ZvkA` — partial redaction preserves prefix+suffix, likely still flagged |

### 2c. Full List of Exposed Secrets (8 total)

| Secret | Provider | Full Value Exposed? |
|--------|----------|---------------------|
| `OPENAI_API_KEY` (sk-proj-...) | OpenAI | YES — full key in 3 files |
| `GEMINI_API_KEY` (AIzaSyAP...) | Google | YES — in 2 files |
| `GEMINI_T1_API_KEY` (AIzaSyDa...) | Google | YES — in 2 files |
| `OPENROUTER_API_KEY` (sk-or-v1-...) | OpenRouter | YES — in 2 files |
| `DEEPSEEK_API_KEY` (sk-14fc...) | DeepSeek | YES — in 2 files |
| `COMPOSIO_API` (ak_GNZ...) | Composio | YES — in 2 files |
| `AZURE_API_KEY` (egIGJ...) | Azure | YES — in 2 files |
| `HF_TOKEN` (hf_atjx...) | HuggingFace | YES — in 2 files |

---

## 3. ARE THESE LIVE KEYS?

**YES — HIGHLY LIKELY.** Evidence:

1. The `.env` file exists at repo root (gitignored, not committed) — last modified Feb 20
2. The dialogue transcript is from Feb 15-16 (the session where the user filled in `.env`)
3. `src/rhea_bridge.py` was confirmed working with "all 6 providers available: true" per the transcript
4. The MEMORY.md notes from Feb 16 confirm: "Bridge: OpenAI OK, OpenRouter OK"
5. Gemini key was already flagged as needing rotation in the P0 list (separate quota issue)

**IMMEDIATE ACTION REQUIRED: Rotate ALL 8 keys at their respective provider dashboards.** Even if we clean git history, the keys were generated on Feb 15 and have been in plaintext in local git objects for 10 days. If any process, backup tool, or Entire.io sync touched these blobs, the keys are compromised.

---

## 4. REMEDIATION OPTIONS

### Option A: Interactive Rebase + In-Place Redaction (RECOMMENDED)

**Strategy:** Rewrite commit `11ae756` to contain redacted versions of the 3 files, then rebase the 9 subsequent commits on top.

**Steps:**
1. **Rotate all 8 API keys first** (human action at provider dashboards)
2. Create a backup branch: `git branch backup/pre-redaction-20260225`
3. Start interactive rebase: `git rebase -i 11ae756^` (mark `11ae756` as `edit`)
4. During the edit stop, replace secrets in the 3 files with `[REDACTED]`
5. `git add` the modified files, `git commit --amend`
6. `git rebase --continue` to replay the remaining 9 commits
7. Verify: `git log --all -p -S "sk-proj-OpjXgRv" | wc -l` should be 0
8. Force push: `git push --force-with-lease origin hyperion/memory`

**Pros:** Preserves commit history structure, only rewrites 10 commits
**Cons:** Requires interactive rebase (conflict risk low since later commits don't touch these files)
**Risk:** LOW — later commits don't modify any of the 3 secret-containing files

### Option B: BFG Repo Cleaner with Replacement File

**Strategy:** Use BFG to replace secret strings across all git history.

**Steps:**
1. **Rotate all 8 API keys first**
2. Install BFG: `brew install bfg`
3. Create `secrets.txt` with one secret per line (the 8 key values)
4. Run: `bfg --replace-text secrets.txt /Users/sa/rh.1`
5. `git reflog expire --expire=now --all && git gc --prune=now --aggressive`
6. Verify no secrets remain: grep the pack files
7. Force push all affected branches

**Pros:** Thorough, handles all branches/refs automatically, well-tested tool
**Cons:** Rewrites ALL history if secrets appear in older commits (they don't — only in 11ae756), needs install
**Note:** BFG is NOT currently installed. `brew install bfg` required.

### Option C: git filter-repo (Modern Alternative to filter-branch)

**Strategy:** Use `git-filter-repo` (Python-based, replaces deprecated `git filter-branch`).

**Steps:**
1. **Rotate all 8 API keys first**
2. Install: `pip install git-filter-repo`
3. Create expressions file mapping each secret to `[REDACTED]`
4. Run: `git filter-repo --replace-text expressions.txt --force`
5. Re-add remote: `git remote add origin <url>`
6. Force push

**Pros:** Faster than BFG, recommended by Git project, handles edge cases
**Cons:** Removes the remote (needs re-add), Python dependency

### Option D: Nuclear — Soft Reset and Recommit

**Strategy:** Squash all 10 unpushed commits into one clean commit after redacting working tree.

**Steps:**
1. **Rotate all 8 API keys first**
2. `git branch backup/pre-redaction-20260225`
3. Redact secrets in the 3 files in working tree
4. `git reset --soft origin/hyperion/memory` (preserves all changes, unstages)
5. `git add -A && git commit -m "Consolidated: 10 commits, secrets redacted"`
6. `git push origin hyperion/memory`

**Pros:** Simplest, no tools needed, guaranteed clean
**Cons:** Loses individual commit history (10 commits become 1), loses authorship granularity

---

## 5. RECOMMENDATION

**Option A (Interactive Rebase)** is the best balance of safety and history preservation.

However, there is a practical blocker: CLAUDE.md says we must NOT use `git rebase -i` since it requires interactive input. Therefore:

**REVISED RECOMMENDATION: Option B (BFG) or Option C (git-filter-repo).**

Between those two, **Option C (git-filter-repo)** is preferred because:
- It's a Python tool (already have Python in the project)
- It's the Git project's official recommendation over `filter-branch`
- It handles the replacement-text use case cleanly
- No Java dependency (BFG requires JVM)

**If speed is critical and we can accept losing granular commit history, Option D (Nuclear Reset) works in 5 minutes with zero tool installs.**

---

## 6. PRE-EXECUTION CHECKLIST (for human)

- [ ] **ROTATE ALL 8 API KEYS** at provider dashboards (OpenAI, Google x2, OpenRouter, DeepSeek, Composio, Azure, HuggingFace)
- [ ] Update `.env` with new keys after rotation
- [ ] Verify bridge still works: `python3 src/rhea_bridge.py status`
- [ ] Approve one of Options B/C/D above
- [ ] Confirm: is `feat/chronos-agents-and-bridge` (ahead 2, unpushed) also blocked or independent?

---

## 7. POST-REMEDIATION VERIFICATION

After executing whichever option:
```bash
# Verify no secrets in any ref
git log --all -p -S "sk-proj-OpjXgRv" | head -5          # should be empty
git log --all -p -S "egIGJK1LK1gZHRwf" | head -5         # should be empty
git log --all -p -S "hf_atjxpUcsqgtQ" | head -5           # should be empty
git log --all -p -S "sk-or-v1-ab2a672922" | head -5       # should be empty
git log --all -p -S "AIzaSyAPtNjNNadHxt" | head -5        # should be empty

# Verify push works
git push --dry-run origin hyperion/memory

# Run repo checks
bash scripts/rhea/check.sh
```

---

## 8. PREVENTION

To prevent recurrence:
1. Add a pre-commit hook that scans for API key patterns (sk-proj-, sk-or-v1-, AIzaSy, hf_, etc.)
2. Add secret-containing file patterns to `.gitignore` (dialogue archives with raw .env dumps)
3. Consider: should `users/sa/archives/dialogues/` and `teams/*.md` be in `.gitignore`?
4. The Gemini `.bak` snapshot (28MB, 443K lines) is also a liability — consider excluding `*.bak` from tracking
5. **`.gitignore` gap:** Neither `users/sa/archives/` nor `teams/*.md` are in `.gitignore`. The outbox IS ignored (`ops/virtual-office/outbox/*.md`), so this report won't be committed — it's local-only. But the dialogue archives that contain the secrets were never excluded.
6. Suggested `.gitignore` additions:
   ```
   # Dialogue archives (may contain embedded secrets from chat transcripts)
   users/sa/archives/
   teams/all_platform_dialogues_*.md
   *.bak
   ```

---

## 9. NOTE ON THIS REPORT

This file is at `ops/virtual-office/outbox/ORION_20260225_SECRET_REMEDIATION_PLAN.md` which IS gitignored (`ops/virtual-office/outbox/*.md` in `.gitignore`). It will NOT be committed or pushed. This is intentional — the report itself references secret patterns and file locations.

---

*ORION signing off. Keys are live. Rotate first, rewrite second. Do not push without rewriting.*
