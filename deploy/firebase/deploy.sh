#!/usr/bin/env bash
# =============================================================================
# deploy/firebase/deploy.sh — Deploy rhea-atlas Next.js UI to Firebase Hosting
# =============================================================================
#
# Builds a static export of the Next.js frontend and deploys it to Firebase
# Hosting (Google-managed CDN, always-free tier).
#
# Usage:
#   NEXT_PUBLIC_RHEA_API=https://rhea-xyz.a.run.app bash deploy/firebase/deploy.sh
#
# Required env:
#   NEXT_PUBLIC_RHEA_API   — Cloud Run URL for the Rhea backend (no trailing slash)
#
# Optional env:
#   NEXT_PUBLIC_TRIBUNAL_API   — Tribunal endpoint (defaults to NEXT_PUBLIC_RHEA_API/api)
#   FIREBASE_PROJECT           — Firebase project ID (default: reads from .firebaserc)
#
# Bash 3.2 compatible (macOS default shell).
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
APP_DIR="${REPO_ROOT}/rhea-atlas"

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info() { printf "${CYAN}[firebase]${NC} %s\n" "$*"; }
ok()   { printf "${GREEN}[  ok   ]${NC} %s\n" "$*"; }
warn() { printf "${YELLOW}[ warn  ]${NC} %s\n" "$*"; }
die()  { printf "${RED}[ error ]${NC} %s\n" "$*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Validate required input
# ---------------------------------------------------------------------------
if [ -z "${NEXT_PUBLIC_RHEA_API:-}" ]; then
  die "NEXT_PUBLIC_RHEA_API is not set.
  Example:
    NEXT_PUBLIC_RHEA_API=https://rhea-api-abc123.a.run.app bash deploy/firebase/deploy.sh"
fi

NEXT_PUBLIC_RHEA_API="${NEXT_PUBLIC_RHEA_API%/}"   # strip trailing slash
NEXT_PUBLIC_TRIBUNAL_API="${NEXT_PUBLIC_TRIBUNAL_API:-${NEXT_PUBLIC_RHEA_API}/api}"

info "Cloud Run API  : ${NEXT_PUBLIC_RHEA_API}"
info "Tribunal API   : ${NEXT_PUBLIC_TRIBUNAL_API}"
info "App dir        : ${APP_DIR}"

# ---------------------------------------------------------------------------
# Check firebase CLI
# ---------------------------------------------------------------------------
if ! command -v firebase >/dev/null 2>&1; then
  warn "firebase CLI not found."
  warn "Install it with:  npm i -g firebase-tools"
  warn "Then authenticate: firebase login"
  die "firebase CLI is required — install and retry."
else
  ok "firebase CLI: $(firebase --version)"
fi

# ---------------------------------------------------------------------------
# Ensure app directory and package.json exist
# ---------------------------------------------------------------------------
if [ ! -d "${APP_DIR}" ]; then
  die "rhea-atlas directory not found at: ${APP_DIR}"
fi
if [ ! -f "${APP_DIR}/package.json" ]; then
  die "No package.json found in ${APP_DIR}"
fi

# ---------------------------------------------------------------------------
# Copy firebase.json to repo root (firebase CLI expects it at project root)
# ---------------------------------------------------------------------------
FIREBASE_JSON_SRC="${SCRIPT_DIR}/firebase.json"
FIREBASE_JSON_DST="${REPO_ROOT}/firebase.json"

if [ ! -f "${FIREBASE_JSON_DST}" ]; then
  info "Copying firebase.json to repo root..."
  cp "${FIREBASE_JSON_SRC}" "${FIREBASE_JSON_DST}"
  ok "firebase.json placed at ${FIREBASE_JSON_DST}"
else
  info "firebase.json already exists at repo root — using existing file."
fi

# ---------------------------------------------------------------------------
# Build: static export
# ---------------------------------------------------------------------------
info "Building Next.js static export..."
printf "\n"

cd "${APP_DIR}"

# Export env vars so next build can embed them
export NEXT_PUBLIC_RHEA_API="${NEXT_PUBLIC_RHEA_API}"
export NEXT_PUBLIC_TRIBUNAL_API="${NEXT_PUBLIC_TRIBUNAL_API}"

npx next build
npx next export

ok "Static export complete — output at: ${APP_DIR}/out"

# ---------------------------------------------------------------------------
# Deploy to Firebase Hosting
# ---------------------------------------------------------------------------
info "Deploying to Firebase Hosting..."
printf "\n"

cd "${REPO_ROOT}"

FIREBASE_ARGS="--only hosting"
if [ -n "${FIREBASE_PROJECT:-}" ]; then
  FIREBASE_ARGS="${FIREBASE_ARGS} --project ${FIREBASE_PROJECT}"
fi

firebase deploy ${FIREBASE_ARGS}

# ---------------------------------------------------------------------------
# Extract and print the hosting URL
# ---------------------------------------------------------------------------
printf "\n"
HOSTING_URL=""

# Attempt to read project ID from .firebaserc if not provided
if [ -z "${FIREBASE_PROJECT:-}" ] && [ -f "${REPO_ROOT}/.firebaserc" ]; then
  # .firebaserc is JSON; parse the default project with basic shell (no jq required)
  FIREBASE_PROJECT="$(grep -o '"default"[[:space:]]*:[[:space:]]*"[^"]*"' "${REPO_ROOT}/.firebaserc" \
    | sed 's/.*"default"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' || true)"
fi

if [ -n "${FIREBASE_PROJECT:-}" ]; then
  HOSTING_URL="https://${FIREBASE_PROJECT}.web.app"
  ok "Firebase Hosting URL: ${HOSTING_URL}"
  printf "\n"
  printf "${BOLD}Deployment complete.${NC}\n"
  printf "  Hosting : %s\n" "${HOSTING_URL}"
  printf "  API     : %s\n" "${NEXT_PUBLIC_RHEA_API}"
  # Print the URL on its own line so deploy-all.sh can capture it via grep
  printf "\n"
  printf "%s\n" "${HOSTING_URL}"
else
  ok "Firebase Hosting deploy complete."
  warn "Could not determine hosting URL automatically."
  warn "Check your project at: https://console.firebase.google.com"
fi
