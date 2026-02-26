#!/usr/bin/env bash
# =============================================================================
# deploy/deploy-all.sh — Rhea Dispersed Cloud Master Deployment Orchestrator
# =============================================================================
#
# Architecture:
#   [Oracle Cloud VM]  ← Redis 7 (persistence, always-free, ARM A1)
#         |
#   [Google Cloud Run] ← rhea-backend FastAPI (serverless, free tier)
#         |
#   [Vercel]           ← rhea-atlas Next.js UI (edge CDN, free tier)
#
# Usage:
#   bash deploy/deploy-all.sh                  # full deploy
#   bash deploy/deploy-all.sh --backend-only   # Cloud Run only
#   bash deploy/deploy-all.sh --frontend-only  # Vercel only (needs RHEA_API_URL)
#   bash deploy/deploy-all.sh --dry-run        # print plan, no execution
#   bash deploy/deploy-all.sh --help           # this help
#
# Environment variables (all optional — sensible defaults apply):
#   PROJECT_ID      GCP project ID          (default: gen-lang-client-0839944748)
#   REGION          Cloud Run region         (default: us-central1)
#   SERVICE         Cloud Run service name   (default: rhea-backend)
#   RHEA_API_URL    Override Cloud Run URL   (required for --frontend-only)
#   VERCEL_TOKEN    Vercel auth token (CI)
#   VERCEL_ORG_ID   Vercel org ID (CI)
#
# Bash 3.2 compatible (macOS default shell).
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Script-level constants
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

CLOUDRUN_DEPLOY="${SCRIPT_DIR}/cloudrun/deploy.sh"
VERCEL_DEPLOY="${SCRIPT_DIR}/vercel/deploy.sh"

# Cloud Run defaults (mirror cloudrun/deploy.sh so we can query service URL)
PROJECT_ID="${PROJECT_ID:-gen-lang-client-0839944748}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-rhea-backend}"

# ---------------------------------------------------------------------------
# Colour palette (compatible with bash 3.2 / macOS Terminal)
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'   # reset

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
info()    { printf "${CYAN}[deploy]${NC} %s\n" "$*"; }
ok()      { printf "${GREEN}[  ok  ]${NC} %s\n" "$*"; }
warn()    { printf "${YELLOW}[ warn ]${NC} %s\n" "$*"; }
err()     { printf "${RED}[ fail ]${NC} %s\n" "$*" >&2; }
die()     { err "$*"; exit 1; }
step()    { printf "\n${BOLD}${BLUE}==> %s${NC}\n" "$*"; }
dim()     { printf "${DIM}%s${NC}\n" "$*"; }
newline() { echo ""; }

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
print_banner() {
  printf "${BOLD}${CYAN}"
  cat <<'BANNER'

  ╔══════════════════════════════════════════════════════════════════╗
  ║          RHEA  —  Dispersed Cloud Deployment Orchestrator        ║
  ╠══════════════════════════════════════════════════════════════════╣
  ║                                                                  ║
  ║   Oracle Cloud  ──  Redis 7 on A1.Flex VM  (persistence)        ║
  ║        │              4 OCPU · 24 GB RAM · $0/mo                ║
  ║        ▼                                                         ║
  ║   Google Cloud Run  ──  rhea-backend FastAPI  (compute)         ║
  ║        │                 512 MB · scale-to-zero · $0/mo         ║
  ║        ▼                                                         ║
  ║   Vercel Edge CDN  ──  rhea-atlas Next.js  (UI)                 ║
  ║                           global CDN · hobby plan · $0/mo       ║
  ╚══════════════════════════════════════════════════════════════════╝

BANNER
  printf "${NC}"
}

# ---------------------------------------------------------------------------
# Usage / help
# ---------------------------------------------------------------------------
usage() {
  cat <<USAGE
Usage: bash deploy/deploy-all.sh [OPTIONS]

Options:
  --backend-only    Deploy Cloud Run backend only
  --frontend-only   Deploy Vercel frontend only (requires RHEA_API_URL env var)
  --dry-run         Print what would be executed; make no changes
  --help            Show this help message

Environment variables:
  PROJECT_ID        GCP project (default: gen-lang-client-0839944748)
  REGION            Cloud Run region (default: us-central1)
  SERVICE           Cloud Run service name (default: rhea-backend)
  RHEA_API_URL      Override Cloud Run URL (required for --frontend-only)
  VERCEL_TOKEN      Vercel auth token for CI / non-interactive auth
  VERCEL_ORG_ID     Vercel org / team ID for CI use

Examples:
  bash deploy/deploy-all.sh
  bash deploy/deploy-all.sh --backend-only
  RHEA_API_URL=https://rhea-xyz.a.run.app bash deploy/deploy-all.sh --frontend-only
  bash deploy/deploy-all.sh --dry-run
USAGE
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
DEPLOY_BACKEND=true
DEPLOY_FRONTEND=true
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --backend-only)   DEPLOY_FRONTEND=false ;;
    --frontend-only)  DEPLOY_BACKEND=false  ;;
    --dry-run)        DRY_RUN=true          ;;
    --help|-h)        print_banner; usage; exit 0 ;;
    *)
      err "Unknown option: $arg"
      usage
      exit 1
      ;;
  esac
done

# Guard: --frontend-only needs RHEA_API_URL
if [ "$DEPLOY_BACKEND" = "false" ] && [ "$DEPLOY_FRONTEND" = "true" ]; then
  if [ -z "${RHEA_API_URL:-}" ]; then
    die "--frontend-only requires RHEA_API_URL to be set.\n  Example: RHEA_API_URL=https://rhea-abc.a.run.app bash deploy/deploy-all.sh --frontend-only"
  fi
fi

# ---------------------------------------------------------------------------
# Prerequisite checks
# ---------------------------------------------------------------------------
check_prereqs() {
  step "Checking prerequisites"

  local missing=0

  check_cmd() {
    local cmd="$1"
    local label="${2:-$1}"
    local hint="$3"
    if command -v "$cmd" >/dev/null 2>&1; then
      ok "$label found: $(command -v "$cmd")"
    else
      err "$label not found — $hint"
      missing=$((missing + 1))
    fi
  }

  # gcloud — required for backend deploy
  if [ "$DEPLOY_BACKEND" = "true" ]; then
    check_cmd gcloud "gcloud CLI" "install from https://cloud.google.com/sdk/docs/install"
    check_cmd docker  "Docker"     "install from https://docs.docker.com/get-docker/"
  fi

  # vercel — required for frontend deploy
  if [ "$DEPLOY_FRONTEND" = "true" ]; then
    if command -v vercel >/dev/null 2>&1; then
      ok "vercel CLI found: $(command -v vercel)"
    else
      warn "vercel CLI not found — deploy/vercel/deploy.sh will install it via npm"
      check_cmd npm "npm (for vercel install)" "install Node.js from https://nodejs.org/"
    fi
  fi

  # SSH key — optional, but needed for Oracle VM work
  if [ -f "${HOME}/.ssh/id_ed25519" ]; then
    ok "SSH key found: ~/.ssh/id_ed25519 (Oracle VM access ready)"
  elif [ -f "${HOME}/.ssh/id_rsa" ]; then
    ok "SSH key found: ~/.ssh/id_rsa (Oracle VM access ready)"
  else
    warn "No SSH key found at ~/.ssh/id_ed25519 or ~/.ssh/id_rsa"
    warn "Oracle VM deployment requires SSH. Generate with: ssh-keygen -t ed25519 -C rhea-oracle"
  fi

  # .env file — required for secrets injection
  if [ "$DEPLOY_BACKEND" = "true" ]; then
    if [ -f "${REPO_ROOT}/.env" ]; then
      ok ".env file found at ${REPO_ROOT}/.env"
    else
      err ".env not found at ${REPO_ROOT}/.env — required for Cloud Run secrets"
      err "Copy .env.example and fill in your API keys"
      missing=$((missing + 1))
    fi
  fi

  if [ "$missing" -gt 0 ]; then
    die "$missing prerequisite(s) missing — fix the above errors and retry."
  fi

  ok "All prerequisites satisfied."
}

# ---------------------------------------------------------------------------
# Deploy: Cloud Run backend
# ---------------------------------------------------------------------------
deploy_backend() {
  step "Deploying backend to Google Cloud Run"

  if [ ! -f "${CLOUDRUN_DEPLOY}" ]; then
    die "Cloud Run deploy script not found: ${CLOUDRUN_DEPLOY}"
  fi

  if [ "$DRY_RUN" = "true" ]; then
    dim "  [dry-run] Would execute: bash ${CLOUDRUN_DEPLOY}"
    dim "  [dry-run]   PROJECT_ID=${PROJECT_ID}"
    dim "  [dry-run]   REGION=${REGION}"
    dim "  [dry-run]   SERVICE=${SERVICE}"
    CLOUDRUN_URL="https://rhea-backend-DRY-RUN.a.run.app"
    return 0
  fi

  # Capture the last line of output from deploy.sh, which prints the URL on stdout
  info "Running: bash ${CLOUDRUN_DEPLOY}"
  newline

  # cloudrun/deploy.sh prints the URL as the very last line on stdout.
  # We tee everything to the terminal and capture the final line.
  CLOUDRUN_RAW_OUTPUT="$(bash "${CLOUDRUN_DEPLOY}" \
    PROJECT_ID="${PROJECT_ID}" \
    REGION="${REGION}" \
    SERVICE="${SERVICE}" \
    2>&1 | tee /dev/stderr)" || die "Cloud Run deploy failed — see output above."

  CLOUDRUN_URL="$(printf '%s' "${CLOUDRUN_RAW_OUTPUT}" | grep -E '^https://' | tail -1 || true)"

  # Fallback: query gcloud directly if parsing failed
  if [ -z "${CLOUDRUN_URL}" ]; then
    warn "Could not parse Cloud Run URL from deploy output — querying gcloud..."
    CLOUDRUN_URL="$(gcloud run services describe "${SERVICE}" \
      --project "${PROJECT_ID}" \
      --region "${REGION}" \
      --format 'value(status.url)' 2>/dev/null || true)"
  fi

  if [ -z "${CLOUDRUN_URL}" ]; then
    die "Cloud Run URL could not be determined. Check the Cloud Console."
  fi

  ok "Cloud Run URL captured: ${CLOUDRUN_URL}"
}

# ---------------------------------------------------------------------------
# Deploy: Vercel frontend
# ---------------------------------------------------------------------------
deploy_frontend() {
  step "Deploying frontend to Vercel"

  if [ ! -f "${VERCEL_DEPLOY}" ]; then
    die "Vercel deploy script not found: ${VERCEL_DEPLOY}"
  fi

  if [ -z "${CLOUDRUN_URL:-}" ]; then
    die "CLOUDRUN_URL is empty — cannot pass RHEA_API_URL to Vercel deploy."
  fi

  if [ "$DRY_RUN" = "true" ]; then
    dim "  [dry-run] Would execute: bash ${VERCEL_DEPLOY}"
    dim "  [dry-run]   RHEA_API_URL=${CLOUDRUN_URL}"
    VERCEL_URL="https://rhea-atlas-DRY-RUN.vercel.app"
    return 0
  fi

  info "Running: RHEA_API_URL=${CLOUDRUN_URL} bash ${VERCEL_DEPLOY}"
  newline

  VERCEL_RAW_OUTPUT="$(RHEA_API_URL="${CLOUDRUN_URL}" \
    VERCEL_TOKEN="${VERCEL_TOKEN:-}" \
    VERCEL_ORG_ID="${VERCEL_ORG_ID:-}" \
    bash "${VERCEL_DEPLOY}" 2>&1 | tee /dev/stderr)" || die "Vercel deploy failed — see output above."

  VERCEL_URL="$(printf '%s' "${VERCEL_RAW_OUTPUT}" | grep -E '^https://' | tail -1 || true)"

  if [ -z "${VERCEL_URL}" ]; then
    warn "Could not parse Vercel deployment URL from output — check Vercel dashboard."
    VERCEL_URL="(check vercel.com/dashboard)"
  fi

  ok "Vercel deployment URL: ${VERCEL_URL}"
}

# ---------------------------------------------------------------------------
# Oracle: print manual instructions (cannot auto-deploy)
# ---------------------------------------------------------------------------
print_oracle_instructions() {
  step "Oracle Cloud VM (persistence layer)"

  printf "${YELLOW}"
  cat <<'ORACLE'
  Oracle Cloud cannot be deployed automatically from this script — it requires
  SSH access to a VM that you provision manually in the Oracle Console.

  Quick-start (if VM already exists):
  ─────────────────────────────────────────────────────────────────────────────
  VM_IP=<your-oracle-vm-public-ip>
  VM_USER=ubuntu                     # or: opc (Oracle Linux)

  # Upload scripts and run setup:
  scp deploy/oracle/setup-vm.sh deploy/oracle/docker-compose.yml \
      ${VM_USER}@${VM_IP}:~/
  ssh ${VM_USER}@${VM_IP} \
      "REDIS_PASSWORD='your-strong-secret-32plus-chars' bash setup-vm.sh"

  # Then update Cloud Run env:
  gcloud run services update rhea-backend \
      --region us-central1 \
      --set-env-vars "REDIS_URL=redis://:your-secret@${VM_IP}:6379"
  ─────────────────────────────────────────────────────────────────────────────

  Full instructions: deploy/oracle/README.md
ORACLE
  printf "${NC}"
}

# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------
health_check_url() {
  local label="$1"
  local url="$2"
  local path="${3:-/}"
  local full="${url%/}${path}"

  if [ "$DRY_RUN" = "true" ]; then
    dim "  [dry-run] Would check: GET ${full}"
    return 0
  fi

  if command -v curl >/dev/null 2>&1; then
    local http_code
    http_code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "${full}" 2>/dev/null || echo 000)"
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 400 ]; then
      ok "Health check ${label}: HTTP ${http_code} — ${full}"
    else
      warn "Health check ${label}: HTTP ${http_code} — ${full} (service may still be warming up)"
    fi
  else
    warn "curl not found — skipping health check for ${label}"
  fi
}

run_health_checks() {
  step "Running health checks"

  if [ "$DEPLOY_BACKEND" = "true" ] && [ -n "${CLOUDRUN_URL:-}" ]; then
    health_check_url "Cloud Run root  " "${CLOUDRUN_URL}" "/"
    health_check_url "Cloud Run health" "${CLOUDRUN_URL}" "/health"
  fi

  if [ "$DEPLOY_FRONTEND" = "true" ] && [ -n "${VERCEL_URL:-}" ]; then
    # Vercel dashboard URL falls back message — skip health check in that case
    if printf '%s' "${VERCEL_URL}" | grep -q '^https://'; then
      health_check_url "Vercel UI       " "${VERCEL_URL}" "/"
    else
      warn "Skipping Vercel health check — URL not available (check dashboard)."
    fi
  fi
}

# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------
print_summary() {
  step "Deployment Summary"

  printf "${BOLD}"
  printf "  %-24s  %-52s  %s\n" "Layer" "URL" "Cost"
  printf "  %-24s  %-52s  %s\n" "────────────────────────" "────────────────────────────────────────────────────" "──────"
  printf "${NC}"

  # Oracle VM row — always shown as manual
  printf "  %-24s  %-52s  %s\n" \
    "Oracle VM (Redis 7)" \
    "(manual — see deploy/oracle/README.md)" \
    "\$0/mo"

  # Cloud Run row
  if [ "$DEPLOY_BACKEND" = "true" ]; then
    local cr_url="${CLOUDRUN_URL:-not deployed}"
    printf "  %-24s  %-52s  %s\n" \
      "Google Cloud Run" \
      "${cr_url}" \
      "\$0/mo"
    if [ -n "${CLOUDRUN_URL:-}" ] && [ "$CLOUDRUN_URL" != "not deployed" ]; then
      printf "  %-24s  %-52s  %s\n" \
        "  └─ Health endpoint" \
        "${CLOUDRUN_URL}/health" \
        ""
    fi
  fi

  # Vercel row
  if [ "$DEPLOY_FRONTEND" = "true" ]; then
    local vc_url="${VERCEL_URL:-not deployed}"
    printf "  %-24s  %-52s  %s\n" \
      "Vercel (Next.js UI)" \
      "${vc_url}" \
      "\$0/mo"
  fi

  newline
  printf "${BOLD}${GREEN}"
  printf "  Total infrastructure cost: \$0.00/month\n"
  printf "${NC}"

  newline
  printf "${DIM}  Cost breakdown:\n"
  printf "    Oracle A1.Flex VM   — Always Free (permanent, no expiry)\n"
  printf "    Cloud Run           — Free tier: 2M requests/mo, 360K GB-s/mo, 180K vCPU-s/mo\n"
  printf "    Vercel Hobby        — Free tier: 100 deployments/day, 100 GB bandwidth/mo\n"
  printf "    GCP Artifact Reg.   — First 0.5 GB/month free; minimal Docker image storage\n"
  printf "${NC}"
}

# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------
main() {
  print_banner

  # Show dry-run notice
  if [ "$DRY_RUN" = "true" ]; then
    printf "${YELLOW}${BOLD}  DRY-RUN MODE — no changes will be made.${NC}\n\n"
  fi

  # Show deploy plan
  info "Deploy plan:"
  if [ "$DEPLOY_BACKEND" = "true" ];  then dim "  - Cloud Run backend (deploy/cloudrun/deploy.sh)"; fi
  if [ "$DEPLOY_FRONTEND" = "true" ]; then dim "  - Vercel frontend   (deploy/vercel/deploy.sh)"; fi
  dim "  - Oracle VM: instructions only (manual step)"
  newline

  # Initialize URL variables (may or may not be populated depending on flags)
  CLOUDRUN_URL="${RHEA_API_URL:-}"
  VERCEL_URL=""

  check_prereqs

  # ── Step 1: Cloud Run backend ──────────────────────────────────────────────
  if [ "$DEPLOY_BACKEND" = "true" ]; then
    deploy_backend
  else
    info "Skipping Cloud Run deploy (--frontend-only)"
    if [ -z "${CLOUDRUN_URL}" ]; then
      die "RHEA_API_URL must be set when skipping the backend deploy."
    fi
    info "Using provided RHEA_API_URL: ${CLOUDRUN_URL}"
  fi

  # ── Step 2: Vercel frontend ────────────────────────────────────────────────
  if [ "$DEPLOY_FRONTEND" = "true" ]; then
    deploy_frontend
  else
    info "Skipping Vercel deploy (--backend-only)"
  fi

  # ── Step 3: Oracle instructions ────────────────────────────────────────────
  print_oracle_instructions

  # ── Step 4: Health checks ──────────────────────────────────────────────────
  run_health_checks

  # ── Step 5: Summary table ──────────────────────────────────────────────────
  print_summary

  newline
  ok "Orchestration complete."
  newline
}

main "$@"
