# Session Context

**Session ID:** 261278d3-25c3-4789-93e7-bfcc23c40cd5

**Commit Message:** Teach the gpt-5.1 variant of Orion to be unstoppable, please. so many of

## Prompt

teach the gpt-5.1 variant of Orion to be unstoppable, please. so many of idiotic stop-questions, i cant handle this anymore

## Summary

`★ Insight ─────────────────────────────────────`
Codex CLI has 3 layers of instruction precedence: (1) `~/.codex/config.toml` — global trust/approval settings, (2) `~/.codex/AGENTS.md` — global system prompt (was iOS-specific, now overridden by project-level), (3) project-level `.codex/AGENTS.md` + `CODEX.md` — project-specific instructions that take priority. The old iOS `AGENTS.md` had "stop and propose a plan if >3 files" which was poisoning every Orion session. Project-level files override global.
`─────────────────────────────────────────────────`

**Done. Orion is now configured to be unstoppable:**

| Layer | File | What changed |
|-------|------|-------------|
| Global config | `~/.codex/config.toml` | `approval_policy = "never"`, `sandbox = "workspace-write"` |
| Project agent | `rh.1/.codex/AGENTS.md` | 61 lines — full autonomy directive, domain ownership, coordination protocol |
| Workspace | `rhea-atlas/CODEX.md` | 47 lines — anti-pattern blacklist, launch command, zero-question mandate |
| Shell aliases | `~/.zshrc` | `orion` (full-auto) and `orion-yolo` (bypass everything) |

**Launch Orion:**
```bash
source ~/.zshrc
orion          # full-auto sandboxed
orion-yolo     # no sandbox, no approvals, total freedom
```

The old iOS "stop after 3 files" poison in `~/.codex/AGENTS.md` is now overridden by the project-level file. Next Orion session should execute without a single question.

## Key Actions

- - **Bash**: Find Orion config/prompt files
- - **Bash**: Find Codex CLI instruction files
- - **Bash**: Check common GPT/Codex config paths
- - **Read**: /Users/sa/.codex/AGENTS.md
- - **Read**: /Users/sa/.codex/config.toml
- - **Bash**: Check Codex rules directory
- - **Read**: /Users/sa/.codex/rules/default.rules
- - **Read**: /Users/sa/rh.1/apparatus/nexus/memories/ORION.md
- - **Bash**: Find project-level Codex config
- - **Bash**: Create project-level .codex directory
