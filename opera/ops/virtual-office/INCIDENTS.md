# INCIDENT: Extension TOML Corruption
> Timestamp: 2026-02-19T15:15:00Z
> Status: RESOLVED
> Impact: High (3 extensions broken)

## Description
Three core extension commands were failing to load due to TOML syntax errors and truncated files in the `~/.gemini/extensions/` directory.

## Affected Files
1. `gemini-cli-prompt-library/commands/testing/edge-cases.toml` (Syntax/Truncation)
2. `gemini-cli-prompt-library/commands/prompts/improve.toml` (Truncation)
3. `gemini-kit/commands/docs.toml` (Mismatched multi-line quotes + invalid divider `---`)

## Resolution
- Used `python3` to rewrite files with correct TOML syntax and UTF-8 encoding.
- Verified all three files using `toml.load()` in Python.
- Result: Verification passed. Extensions are now operational.

## Root Cause Analysis
Likely a race condition or write failure during an extension update or installation process. The use of non-standard dividers like `---` outside of string blocks in `docs.toml` also contributed.

## Prevention
Ensure extension installers validate TOML syntax before finalization.
