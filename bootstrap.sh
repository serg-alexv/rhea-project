#!/usr/bin/env bash
set -euo pipefail

# Rhea Project — Bootstrap Script (safe + idempotent)
# Run inside repo root:  chmod +x bootstrap.sh && ./bootstrap.sh
#
# Flags:
#   --no-venv       Skip Python venv creation
#   --dry-run       Show actions without writing files
#   --install-claude  (optional) Install Claude Code (runs official installer)
#
# Notes:
# - No destructive moves: root docs are copied into docs/ if present.
# - You stay in control: this script writes only "missing" files by default.

DRY_RUN=0
NO_VENV=0
INSTALL_CLAUDE=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --no-venv) NO_VENV=1 ;;
    --install-claude) INSTALL_CLAUDE=1 ;;
    *) echo "Unknown flag: $arg" >&2; exit 1 ;;
  esac
done

run() {
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "DRY-RUN: $*"
  else
    eval "$@"
  fi
}

say() { printf "\n== %s ==\n" "$1"; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

in_repo_root() {
  [ -d ".git" ] || return 1
  return 0
}

write_if_missing() {
  local path="$1"
  shift
  if [ -f "$path" ]; then
    echo "exists: $path"
  else
    echo "write:  $path"
    if [ "$DRY_RUN" -eq 0 ]; then
      mkdir -p "$(dirname "$path")"
      cat > "$path" <<EOF
$*
EOF
    fi
  fi
}

copy_if_exists() {
  local src="$1"
  local dst="$2"
  if [ -f "$src" ] && [ ! -f "$dst" ]; then
    echo "copy:   $src -> $dst"
    run "mkdir -p \"$(dirname "$dst")\""
    run "cp \"$src\" \"$dst\""
  fi
}

say "Preflight"
need_cmd git
need_cmd python3
need_cmd curl

if ! in_repo_root; then
  echo "This does not look like a git repo root (missing .git)." >&2
  echo "Run this from inside your rhea-project directory." >&2
  exit 1
fi

OS="$(uname -s || true)"
echo "OS: $OS"
echo "Repo: $(basename "$(pwd)")"
echo "Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"

say "Create/normalize structure"
run "mkdir -p docs src prompts scripts .claude .entire"

# If your repo currently has architecture.md/state.md/decisions.md at root,
# copy them into docs/ (do NOT delete originals).
copy_if_exists "architecture.md" "docs/architecture.md"
copy_if_exists "state.md"        "docs/state.md"
copy_if_exists "decisions.md"    "docs/decisions.md"

say "Scaffold documentation (only if missing)"
write_if_missing "AGENT_RULES.md" \
"# Agent Rules (Rhea)\n\n\
## Working style\n\
- Keep diffs small and reviewable.\n\
- Do not change unrelated files.\n\
- Prefer additive edits (new files) over refactors.\n\
- Never delete data/logs without explicit instruction.\n\n\
## Claude Code usage\n\
- Always show a plan before editing.\n\
- Always list files you will touch.\n\
- After changes: show summary + run checks.\n\n\
## Repo invariants\n\
- docs/state.md stays <= 2KB.\n\
- docs/* are the canonical specs.\n\
- src/* contains executable code.\n"

write_if_missing "docs/MVP_LOOP.md" \
"# MVP_LOOP — Closed-Loop Scheduler Spec (Draft)\n\n\
## Goal\n\
Rhea is a controller that proposes the next best action under uncertainty, not a perfect day plan.\n\n\
## State x_t (minimal)\n\
- sleep_proxy: (from device / manual quick tag)\n\
- energy: 1–5 (or inferred)\n\
- time_budget: minutes available in current window\n\
- friction: current resistance (inferred: context switches, doomscroll, etc.)\n\n\
## Action set A (MVP)\n\
- micro-interventions (2–5 min)\n\
- tasks (10–60 min)\n\
- recovery actions (walk, breathing, light, hydration)\n\n\
## Reward / Utility\n\
- completion (binary)\n\
- strain penalty (context switches, overruns)\n\
- agency score (user felt in control)\n\n\
## Safety constraints\n\
- minimum viable day (anti-spiral)\n\
- hard bounds: no more than N context switches/hour\n\
- recovery floor: if sleep_proxy low → enforce recovery actions\n\n\
## Online updates\n\
- Bayesian duration update per action\n\
- completion probability update\n\
- bandit policy for micro-interventions\n\n\
## Logging schema\n\
- timestamp, state snapshot, action proposed, action taken, duration, outcome\n"

write_if_missing "docs/ROADMAP.md" \
"# Roadmap\n\n\
## Stage 0 — Specs + controller skeleton\n\
- Finalize MVP_LOOP\n\
- Define log schema\n\
- Minimal Python simulation harness\n\n\
## Stage 1 — iOS MVP (next-best-action)\n\
- SwiftUI shell\n\
- 10-second check-in\n\
- Local-only persistence\n\n\
## Stage 2 — Passive signals\n\
- HealthKit / Watch\n\
- Feature extraction\n\n\
## Stage 3 — Optimization (MPC)\n\
- Replanning under uncertainty\n\
- Hard constraints + safe defaults\n"

write_if_missing ".env.example" \
"# Copy to .env and fill values\n\
# Never commit .env\n\
\n\
OPENAI_API_KEY=\n\
ANTHROPIC_API_KEY=\n\
GEMINI_API_KEY=\n\
OPENROUTER_API_KEY=\n\
DEEPSEEK_API_KEY=\n\
AZURE_OPENAI_ENDPOINT=\n\
AZURE_OPENAI_API_KEY=\n"

write_if_missing "requirements.txt" \
"# Minimal deps for local bridge experiments\n\
python-dotenv\n\
requests\n"

say "Python environment"
if [ "$NO_VENV" -eq 1 ]; then
  echo "Skipping venv (--no-venv)."
else
  if [ -d ".venv" ]; then
    echo "exists: .venv"
  else
    echo "create: .venv"
    run "python3 -m venv .venv"
  fi
  # shellcheck disable=SC1091
  if [ "$DRY_RUN" -eq 0 ]; then
    source .venv/bin/activate
    python -m pip install --upgrade pip >/dev/null
    pip install -r requirements.txt >/dev/null
    deactivate || true
  else
    echo "DRY-RUN: would install requirements into .venv"
  fi
fi

say "Claude Code (optional)"
if [ "$INSTALL_CLAUDE" -eq 1 ]; then
  echo "Installing Claude Code via official installer..."
  # Official docs: curl -fsSL https://claude.ai/install.sh | bash
  # (You asked for a one-piece setup: this is the standard upstream path.)
  run "curl -fsSL https://claude.ai/install.sh | bash"
else
  echo "Skipped. To install later, run:"
  echo "  curl -fsSL https://claude.ai/install.sh | bash"
fi

say "Quick checks"
echo "Git status:"
git status --porcelain || true

say "Next steps"
cat <<'TXT'
1) Activate venv:
   source .venv/bin/activate

2) Create a working branch:
   git checkout -b feature/mvp-loop

3) Ask Claude Code to implement ONE change-set at a time.
   Prompt template:

   TASK:
   - Add/upgrade: docs/MVP_LOOP.md + docs/log_schema.md
   - Constraints: minimal diffs, do not touch unrelated files
   - Output: plan -> edits -> summary -> checks

4) Commit:
   git add -A
   git commit -m "docs: bootstrap MVP loop + agent rules"
TXT

say "Done"
