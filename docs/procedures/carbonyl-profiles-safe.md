# Carbonyl Profiles — Safe Session Persistence

Date: 2026-02-28
Owner: ORION
Status: ACTIVE

## Goal
Use Carbonyl with stable per-service profiles on one machine, without token/cookie extraction workflows.

## Script
- `scripts/carbonyl_profiles.sh`

## Quick Start
```bash
bash scripts/carbonyl_profiles.sh init
bash scripts/carbonyl_profiles.sh open openai
bash scripts/carbonyl_profiles.sh open anthropic
bash scripts/carbonyl_profiles.sh open gemini
```

## Commands
```bash
bash scripts/carbonyl_profiles.sh status
bash scripts/carbonyl_profiles.sh reset openai
bash scripts/carbonyl_profiles.sh safe-backup baseline-2026-02-28
```

## Security Posture
- Persistent session state is maintained inside each profile via normal browser behavior.
- Script does **not** extract, clone, or transport auth tokens.
- `safe-backup` excludes auth/session databases by design.
