#!/usr/bin/env bash
# deploy/vercel/deploy.sh — One-command Vercel deploy for Orion Atlas (rhea-atlas/)
# Usage:
#   RHEA_API_URL=https://rhea-api-xxx.a.run.app bash deploy/vercel/deploy.sh
#   RHEA_API_URL=... TRIBUNAL_API_URL=... bash deploy/vercel/deploy.sh
#
# Required env:
#   RHEA_API_URL         — Cloud Run URL for the Rhea backend (no trailing slash)
# Optional env:
#   TRIBUNAL_API_URL     — Cloud Run tribunal endpoint (defaults to RHEA_API_URL/api)
#   GEMINI_API_KEY       — Override NEXT_PUBLIC_GEMINI_API_KEY for production
#   VERCEL_TOKEN         — Non-interactive auth token (CI use)
#   VERCEL_ORG_ID        — Vercel org/team ID (CI use)
#   VERCEL_PROJECT_ID    — Vercel project ID (CI use)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
APP_DIR="${REPO_ROOT}/rhea-atlas"

# ── Colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[deploy]${NC} $*"; }
ok()    { echo -e "${GREEN}[ok]${NC} $*"; }
warn()  { echo -e "${YELLOW}[warn]${NC} $*"; }
die()   { echo -e "${RED}[error]${NC} $*" >&2; exit 1; }

# ── Validate required input ───────────────────────────────────────────────────
if [[ -z "${RHEA_API_URL:-}" ]]; then
  die "RHEA_API_URL is not set. Example:\n  RHEA_API_URL=https://rhea-api-abc123.a.run.app bash deploy/vercel/deploy.sh"
fi

RHEA_API_URL="${RHEA_API_URL%/}"                        # strip trailing slash
TRIBUNAL_API_URL="${TRIBUNAL_API_URL:-${RHEA_API_URL}/api}"

info "Cloud Run API  : ${RHEA_API_URL}"
info "Tribunal API   : ${TRIBUNAL_API_URL}"
info "App dir        : ${APP_DIR}"

# ── Ensure app directory exists ───────────────────────────────────────────────
[[ -d "${APP_DIR}" ]] || die "rhea-atlas directory not found at: ${APP_DIR}"
[[ -f "${APP_DIR}/package.json" ]] || die "No package.json found in ${APP_DIR}"

# ── Check / install Vercel CLI ────────────────────────────────────────────────
if ! command -v vercel &>/dev/null; then
  warn "vercel CLI not found — installing globally..."
  npm install -g vercel
  ok "vercel CLI installed: $(vercel --version)"
else
  ok "vercel CLI: $(vercel --version)"
fi

# ── Build env-var flags for vercel deploy ────────────────────────────────────
ENV_FLAGS=(
  -e "NEXT_PUBLIC_RHEA_API=${RHEA_API_URL}"
  -e "NEXT_PUBLIC_TRIBUNAL_API=${TRIBUNAL_API_URL}"
)

if [[ -n "${GEMINI_API_KEY:-}" ]]; then
  ENV_FLAGS+=(-e "NEXT_PUBLIC_GEMINI_API_KEY=${GEMINI_API_KEY}")
  info "Gemini API key : provided via env"
else
  # Read from .env.local as fallback — never commit to the deployment log
  LOCAL_KEY="$(grep -E '^NEXT_PUBLIC_GEMINI_API_KEY=' "${APP_DIR}/.env.local" 2>/dev/null | cut -d= -f2- || true)"
  if [[ -n "${LOCAL_KEY}" ]]; then
    ENV_FLAGS+=(-e "NEXT_PUBLIC_GEMINI_API_KEY=${LOCAL_KEY}")
    warn "Gemini API key : read from .env.local (consider setting GEMINI_API_KEY env var in CI)"
  else
    warn "Gemini API key : not set — Gemini features will be unavailable"
  fi
fi

# ── CI / non-interactive token flags ─────────────────────────────────────────
TOKEN_FLAGS=()
[[ -n "${VERCEL_TOKEN:-}" ]]      && TOKEN_FLAGS+=(--token "${VERCEL_TOKEN}")
[[ -n "${VERCEL_ORG_ID:-}" ]]     && TOKEN_FLAGS+=(--scope "${VERCEL_ORG_ID}")

# ── Deploy ────────────────────────────────────────────────────────────────────
info "Running: vercel deploy --prod from ${APP_DIR}"
cd "${APP_DIR}"

DEPLOY_OUTPUT="$(vercel deploy --prod --yes \
  "${TOKEN_FLAGS[@]}" \
  "${ENV_FLAGS[@]}" \
  2>&1)"

echo "${DEPLOY_OUTPUT}"

# ── Extract and print the deployment URL ─────────────────────────────────────
DEPLOY_URL="$(echo "${DEPLOY_OUTPUT}" | grep -E '^https://' | tail -1 || true)"

echo ""
if [[ -n "${DEPLOY_URL}" ]]; then
  ok "Deployment URL: ${DEPLOY_URL}"
else
  warn "Could not parse deployment URL from output — check vercel dashboard"
fi
