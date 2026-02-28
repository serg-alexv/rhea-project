#!/usr/bin/env bash
set -euo pipefail

# Carbonyl profile manager (safe mode)
# - persistent per-service profiles
# - no token/cookie extraction or cloning
# - explicit login per profile through official auth flow

CARBONYL_BIN="${CARBONYL_BIN:-$(command -v carbonyl || true)}"
BASE_DIR="${CARBONYL_PROFILE_BASE:-$HOME/.config/carbonyl/profiles}"

usage() {
  cat <<USAGE
Usage:
  bash scripts/carbonyl_profiles.sh init
  bash scripts/carbonyl_profiles.sh open <openai|anthropic|gemini>
  bash scripts/carbonyl_profiles.sh status
  bash scripts/carbonyl_profiles.sh reset <openai|anthropic|gemini>
  bash scripts/carbonyl_profiles.sh safe-backup <name>

Notes:
  - Profiles are persistent: each service keeps its own user-data-dir.
  - No session token extraction/cloning is performed.
  - safe-backup excludes sensitive auth DB files on purpose.
USAGE
}

need_bin() {
  if [[ -z "$CARBONYL_BIN" ]]; then
    echo "carbonyl not found in PATH"
    exit 1
  fi
}

profile_dir() {
  local svc="$1"
  echo "$BASE_DIR/$svc"
}

service_url() {
  local svc="$1"
  case "$svc" in
    openai) echo "https://platform.openai.com" ;;
    anthropic) echo "https://console.anthropic.com" ;;
    gemini) echo "https://aistudio.google.com" ;;
    *) echo "" ;;
  esac
}

init_profiles() {
  mkdir -p "$BASE_DIR"/openai "$BASE_DIR"/anthropic "$BASE_DIR"/gemini
  cat > "$BASE_DIR/README.txt" <<TXT
Carbonyl service profiles
- openai
- anthropic
- gemini

Each profile uses Chromium user-data-dir.
Log in separately in each profile via official UI.
Do not copy auth databases between profiles.
TXT
  echo "initialized: $BASE_DIR"
}

open_service() {
  local svc="${1:-}"
  local url
  url="$(service_url "$svc")"
  if [[ -z "$url" ]]; then
    echo "unknown service: $svc"
    exit 2
  fi
  local dir
  dir="$(profile_dir "$svc")"
  mkdir -p "$dir"
  echo "opening $svc -> $url"
  exec "$CARBONYL_BIN" --user-data-dir="$dir" "$url"
}

status_profiles() {
  echo "carbonyl: ${CARBONYL_BIN:-not found}"
  echo "base: $BASE_DIR"
  for svc in openai anthropic gemini; do
    local dir
    dir="$(profile_dir "$svc")"
    if [[ -d "$dir" ]]; then
      echo "[$svc] profile: $dir"
      find "$dir" -maxdepth 2 -type d | sed 's/^/  - /'
    else
      echo "[$svc] profile: (missing)"
    fi
  done
}

reset_profile() {
  local svc="${1:-}"
  [[ -n "$svc" ]] || { echo "service required"; exit 2; }
  local dir
  dir="$(profile_dir "$svc")"
  rm -rf "$dir"
  mkdir -p "$dir"
  echo "reset profile: $svc"
}

safe_backup() {
  local name="${1:-}"
  [[ -n "$name" ]] || { echo "backup name required"; exit 2; }
  local out="$HOME/.config/carbonyl/backups/${name}"
  mkdir -p "$out"

  for svc in openai anthropic gemini; do
    local src dst
    src="$(profile_dir "$svc")"
    dst="$out/$svc"
    mkdir -p "$dst"
    if [[ -d "$src" ]]; then
      rsync -a --delete \
        --exclude 'Cookies*' \
        --exclude 'Login Data*' \
        --exclude 'Network/*' \
        --exclude 'Session*' \
        --exclude 'Web Data*' \
        "$src/" "$dst/"
    fi
  done

  echo "safe backup created: $out"
  echo "(auth/session DBs intentionally excluded)"
}

cmd="${1:-help}"
shift || true

case "$cmd" in
  init)
    need_bin
    init_profiles
    ;;
  open)
    need_bin
    open_service "$@"
    ;;
  status)
    need_bin
    status_profiles
    ;;
  reset)
    need_bin
    reset_profile "$@"
    ;;
  safe-backup)
    safe_backup "$@"
    ;;
  help|--help|-h)
    usage
    ;;
  *)
    usage
    exit 2
    ;;
esac
