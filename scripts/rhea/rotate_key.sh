#!/usr/bin/env bash
# rotate_key.sh — Safe credential rotation for Rhea bridge
# Keys NEVER appear in CLI args, history, or stdout.
#
# Usage:
#   bash scripts/rhea/rotate_key.sh paste <provider>    # clipboard → .env
#   bash scripts/rhea/rotate_key.sh create gemini        # auto-create via gcloud
#   bash scripts/rhea/rotate_key.sh audit                # check for exposure
#   bash scripts/rhea/rotate_key.sh test                 # test via bridge
#   bash scripts/rhea/rotate_key.sh wipe                 # clean traces

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

PROVIDERS="openai anthropic gemini openrouter deepseek redis_password azure hf firebase"

red()   { printf '\033[0;31m%s\033[0m\n' "$*"; }
green() { printf '\033[0;32m%s\033[0m\n' "$*"; }
yellow(){ printf '\033[0;33m%s\033[0m\n' "$*"; }

# Map provider → env var name
provider_to_var() {
  case "$1" in
    openai)         echo "OPENAI_API_KEY" ;;
    anthropic)      echo "ANTHROPIC_API_KEY" ;;
    gemini)         echo "GEMINI_API_KEY" ;;
    openrouter)     echo "OPENROUTER_API_KEY" ;;
    deepseek)       echo "DEEPSEEK_API_KEY" ;;
    redis_password) echo "REDIS_PASSWORD" ;;
    azure)          echo "AZURE_API_KEY" ;;
    hf)             echo "HF_TOKEN" ;;
    firebase)       echo "FIREBASE_API_KEY" ;;
    *) echo "" ;;
  esac
}

# Expected key prefix for validation
provider_prefix() {
  case "$1" in
    openai)    echo "sk-proj-" ;;
    anthropic) echo "sk-ant-" ;;
    gemini)    echo "AIzaSy" ;;
    openrouter) echo "sk-or-" ;;
    deepseek)  echo "sk-" ;;
    hf)        echo "hf_" ;;
    *) echo "" ;;
  esac
}

# ─── PASTE: clipboard → .env (zero shell exposure) ───
cmd_paste() {
  local provider="${1:-}"
  if [ -z "$provider" ]; then
    red "Usage: rotate_key.sh paste <provider>"
    echo "Providers: $PROVIDERS"
    exit 1
  fi

  local var
  var=$(provider_to_var "$provider")
  if [ -z "$var" ]; then
    red "Unknown provider: $provider"
    echo "Known: $PROVIDERS"
    exit 1
  fi

  # Read from clipboard into temp file (key never in shell variable visible to ps)
  local tmpfile
  tmpfile=$(mktemp /tmp/.rhea_key_XXXXXX)

  pbpaste > "$tmpfile" 2>/dev/null
  # Strip whitespace/newlines
  local key
  key=$(tr -d '[:space:]' < "$tmpfile")
  rm -f "$tmpfile"

  if [ -z "$key" ]; then
    red "Clipboard is empty. Copy your new key first, then run this."
    exit 1
  fi

  # Validate prefix if known
  local expected
  expected=$(provider_prefix "$provider")
  if [ -n "$expected" ]; then
    local prefix="${key:0:${#expected}}"
    if [ "$prefix" != "$expected" ]; then
      yellow "WARNING: Key doesn't start with expected prefix '$expected'"
      yellow "Got: ${key:0:8}..."
      printf "Continue anyway? [y/N] "
      read -r ans
      [ "$ans" = "y" ] || [ "$ans" = "Y" ] || exit 1
    fi
  fi

  # Update .env — use perl so key never appears in process args
  if grep -q "^${var}=" "$ENV_FILE" 2>/dev/null; then
    perl -i -pe "BEGIN{\$k=\$ENV{_RHEA_KEY}} s/^${var}=.*/${var}=\$k/" "$ENV_FILE" <<< ""
    # Fallback: direct sed-like replacement via temp file
    local tmpenv
    tmpenv=$(mktemp /tmp/.rhea_env_XXXXXX)
    while IFS= read -r line; do
      case "$line" in
        "${var}="*) echo "${var}=${key}" ;;
        *) echo "$line" ;;
      esac
    done < "$ENV_FILE" > "$tmpenv"
    mv "$tmpenv" "$ENV_FILE"
    green "Updated $var in .env"
  else
    echo "${var}=${key}" >> "$ENV_FILE"
    green "Added $var to .env"
  fi

  # If it's redis_password, also update REDIS_URL and REDIS_PWD
  if [ "$provider" = "redis_password" ]; then
    local host port user
    host=$(grep '^REDIS_HOST=' "$ENV_FILE" | cut -d= -f2)
    port=$(grep '^REDIS_PORT=' "$ENV_FILE" | cut -d= -f2)
    user=$(grep '^REDIS_USERNAME=' "$ENV_FILE" | cut -d= -f2)
    local new_url="redis://${user}:${key}@${host}:${port}"

    local tmpenv2
    tmpenv2=$(mktemp /tmp/.rhea_env_XXXXXX)
    while IFS= read -r line; do
      case "$line" in
        REDIS_URL=*)  echo "REDIS_URL=${new_url}" ;;
        REDIS_PWD=*)  echo "REDIS_PWD=${key}" ;;
        *) echo "$line" ;;
      esac
    done < "$ENV_FILE" > "$tmpenv2"
    mv "$tmpenv2" "$ENV_FILE"
    green "Also updated REDIS_URL and REDIS_PWD"
  fi

  # Clear clipboard
  echo -n "" | pbcopy
  green "Clipboard cleared."
  echo "Key length: ${#key} chars"
  echo "Provider:   $provider"
  green "Done. Run 'rotate_key.sh test' to verify."
}

# ─── CREATE: auto-generate key via API ───
cmd_create() {
  local provider="${1:-}"
  case "$provider" in
    gemini)
      echo "Available Gemini projects:"
      echo "  1) gen-lang-client-0839944748 (Rhea)"
      echo "  2) gen-lang-client-0074239115 (Default Gemini)"
      printf "Pick [1]: "
      read -r choice
      local project
      case "${choice:-1}" in
        1) project="gen-lang-client-0839944748" ;;
        2) project="gen-lang-client-0074239115" ;;
        *) red "Invalid"; exit 1 ;;
      esac

      yellow "Creating new Gemini key..."
      local result
      result=$(gcloud services api-keys create \
        --display-name="rhea-$(date +%Y%m%d)" \
        --project="$project" 2>&1)

      local new_key
      new_key=$(echo "$result" | grep 'keyString' | sed 's/.*"keyString":"\([^"]*\)".*/\1/')

      if [ -z "$new_key" ]; then
        red "Failed to extract key"
        exit 1
      fi

      # Write directly (key only in variable, never in args)
      local tmpenv
      tmpenv=$(mktemp /tmp/.rhea_env_XXXXXX)
      while IFS= read -r line; do
        case "$line" in
          GEMINI_API_KEY=*) echo "GEMINI_API_KEY=${new_key}" ;;
          *) echo "$line" ;;
        esac
      done < "$ENV_FILE" > "$tmpenv"
      mv "$tmpenv" "$ENV_FILE"
      green "New Gemini key → .env (${#new_key} chars, ${new_key:0:8}...)"
      ;;
    *)
      red "Auto-create supported for: gemini"
      echo "For others: create in web console → copy → rotate_key.sh paste <provider>"
      exit 1
      ;;
  esac
}

# ─── AUDIT: check for exposed keys ───
cmd_audit() {
  echo "=== Rhea Credential Exposure Audit ==="
  echo ""
  local issues=0

  while IFS='=' read -r var val; do
    # Skip comments and short values
    case "$var" in \#*|"") continue ;; esac
    [ ${#val} -lt 10 ] && continue
    # Only check secret-looking vars
    case "$var" in *KEY*|*TOKEN*|*PASSWORD*|*PWD*|*SECRET*|*API) ;; *) continue ;; esac

    local short="${val:0:8}...${val: -4}"

    # Check git tracked content (staged files)
    if git -C "$PROJECT_ROOT" grep -qF "$val" HEAD -- 2>/dev/null; then
      red "EXPOSED in git HEAD: $var ($short)"
      issues=$((issues + 1))
    fi

    # Check git log diffs (slower, sample last 50 commits)
    if git -C "$PROJECT_ROOT" log -50 --all -p 2>/dev/null | grep -qF "$val" 2>/dev/null; then
      red "EXPOSED in git history: $var ($short)"
      issues=$((issues + 1))
    fi

    # Check zsh history
    if [ -f "$HOME/.zsh_history" ] && grep -qF "$val" "$HOME/.zsh_history" 2>/dev/null; then
      red "EXPOSED in zsh history: $var ($short)"
      issues=$((issues + 1))
    fi

    # Check bash history
    local histfile="${HISTFILE:-$HOME/.bash_history}"
    if [ -f "$histfile" ] && grep -qF "$val" "$histfile" 2>/dev/null; then
      red "EXPOSED in bash history: $var ($short)"
      issues=$((issues + 1))
    fi

  done < <(grep -v '^#' "$ENV_FILE" | grep '=')

  # Check .env tracking
  if git -C "$PROJECT_ROOT" ls-files --error-unmatch .env >/dev/null 2>&1; then
    red "CRITICAL: .env is tracked by git!"
    issues=$((issues + 1))
  else
    green ".env is NOT tracked by git"
  fi

  if grep -qF '.env' "$PROJECT_ROOT/.gitignore" 2>/dev/null; then
    green ".env is in .gitignore"
  else
    red ".env NOT in .gitignore!"
    issues=$((issues + 1))
  fi

  echo ""
  if [ $issues -eq 0 ]; then
    green "No exposure detected."
  else
    yellow "$issues exposure(s) found."
    echo "  Fix: rotate_key.sh paste <provider>  (after creating new key)"
    echo "  Fix: rotate_key.sh wipe              (clean history traces)"
    echo "  Fix: git filter-repo or BFG           (purge git history)"
  fi
}

# ─── TEST: verify keys via bridge ───
cmd_test() {
  yellow "Testing provider keys via bridge..."
  cd "$PROJECT_ROOT"
  python3 src/rhea_bridge.py status 2>&1 || echo "(bridge status failed)"
}

# ─── WIPE: clean traces ───
cmd_wipe() {
  yellow "Wiping credential traces..."

  # Clear clipboard
  echo -n "" | pbcopy
  green "Clipboard cleared"

  # Clean zsh history
  if [ -f "$HOME/.zsh_history" ]; then
    local before after
    before=$(wc -l < "$HOME/.zsh_history")
    grep -vE '(sk-proj-|sk-ant-|AIzaSy|sk-or-v1-|sk-e[0-9a-f]{20}|hf_[A-Za-z])' "$HOME/.zsh_history" > "$HOME/.zsh_history.clean" 2>/dev/null || cp "$HOME/.zsh_history" "$HOME/.zsh_history.clean"
    mv "$HOME/.zsh_history.clean" "$HOME/.zsh_history"
    after=$(wc -l < "$HOME/.zsh_history")
    green "Zsh history: cleaned $((before - after)) lines"
  fi

  # Clean bash history
  local histfile="${HISTFILE:-$HOME/.bash_history}"
  if [ -f "$histfile" ]; then
    local before after
    before=$(wc -l < "$histfile")
    grep -vE '(sk-proj-|sk-ant-|AIzaSy|sk-or-v1-|sk-e[0-9a-f]{20}|hf_[A-Za-z])' "$histfile" > "${histfile}.clean" 2>/dev/null || cp "$histfile" "${histfile}.clean"
    mv "${histfile}.clean" "$histfile"
    after=$(wc -l < "$histfile")
    green "Bash history: cleaned $((before - after)) lines"
  fi

  # Clean temp key files
  rm -f /tmp/.rhea_key_* /tmp/openai_key_* /tmp/anthropic_key_* /tmp/gemini_key_* 2>/dev/null
  green "Temp key files cleaned"

  green "Trace wipe complete."
}

# ─── MAIN ───
case "${1:-help}" in
  paste)  shift; cmd_paste "$@" ;;
  create) shift; cmd_create "$@" ;;
  audit)  cmd_audit ;;
  test)   cmd_test ;;
  wipe)   cmd_wipe ;;
  *)
    cat <<'HELP'
rotate_key.sh — Safe credential rotation for Rhea

Commands:
  paste <provider>   Copy key to clipboard first, then run. Key → .env directly.
  create gemini      Auto-create Gemini key via gcloud.
  audit              Scan git + shell history for exposed keys.
  test               Test all provider keys via bridge.
  wipe               Clean clipboard, history, temp files.

Providers: openai anthropic gemini openrouter deepseek redis_password azure hf firebase

Workflow:
  1. Create new key in provider's web console
  2. Copy to clipboard (Cmd+C)
  3. bash scripts/rhea/rotate_key.sh paste openai
  4. bash scripts/rhea/rotate_key.sh test
  5. bash scripts/rhea/rotate_key.sh wipe
HELP
    ;;
esac
