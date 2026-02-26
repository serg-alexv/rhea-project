#!/usr/bin/env bash
# =============================================================================
# deploy/teardown.sh — Rhea Dispersed Cloud Teardown
# =============================================================================
#
# Removes cloud resources in reverse-deploy order:
#   1. Firebase Hosting — disable hosting via firebase CLI
#   2. Google Cloud Run — delete service + optionally clean Artifact Registry
#   3. Oracle VM — NOT auto-deleted (backup layer; see note below)
#
# Usage:
#   bash deploy/teardown.sh               # interactive, confirms before deleting
#   bash deploy/teardown.sh --yes         # skip confirmation prompts
#   bash deploy/teardown.sh --dry-run     # print what would be done, no changes
#   bash deploy/teardown.sh --help
#
# Environment variables:
#   PROJECT_ID       GCP project (default: gen-lang-client-0839944748)
#   REGION           Cloud Run region (default: us-central1)
#   SERVICE          Cloud Run service name (default: rhea-backend)
#   REPO             Artifact Registry repo name (default: rhea)
#   FIREBASE_PROJECT Firebase project ID (default: reads from .firebaserc)
#
# WARNING: Cloud Run deletion is IMMEDIATE and IRREVERSIBLE.
#          Oracle VM data is NOT touched by this script.
#
# Bash 3.2 compatible (macOS default shell).
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PROJECT_ID="${PROJECT_ID:-gen-lang-client-0839944748}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-rhea-backend}"
REPO="${REPO:-rhea}"
FIREBASE_PROJECT="${FIREBASE_PROJECT:-}"

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
info()    { printf "${CYAN}[teardown]${NC} %s\n" "$*"; }
ok()      { printf "${GREEN}[  ok    ]${NC} %s\n" "$*"; }
warn()    { printf "${YELLOW}[ warn   ]${NC} %s\n" "$*"; }
err()     { printf "${RED}[ error  ]${NC} %s\n" "$*" >&2; }
die()     { err "$*"; exit 1; }
step()    { printf "\n${BOLD}${BLUE}==> %s${NC}\n" "$*"; }
dim()     { printf "${DIM}%s${NC}\n" "$*"; }
newline() { echo ""; }

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
print_banner() {
  printf "${BOLD}${RED}"
  cat <<'BANNER'

  ╔══════════════════════════════════════════════════════════════════╗
  ║           RHEA  —  Dispersed Cloud Teardown Script              ║
  ╠══════════════════════════════════════════════════════════════════╣
  ║                                                                  ║
  ║  This script removes deployed cloud resources.                   ║
  ║  Oracle VM is intentionally SKIPPED (backup + monitoring layer). ║
  ║                                                                  ║
  ║  Cloud Run deletion is IMMEDIATE and IRREVERSIBLE.               ║
  ╚══════════════════════════════════════════════════════════════════╝

BANNER
  printf "${NC}"
}

# ---------------------------------------------------------------------------
# Usage / help
# ---------------------------------------------------------------------------
usage() {
  cat <<USAGE
Usage: bash deploy/teardown.sh [OPTIONS]

Options:
  --yes       Skip all confirmation prompts (use in CI at your own risk)
  --dry-run   Print what would be deleted; make no actual changes
  --help      Show this help message

Environment variables:
  PROJECT_ID       GCP project (default: gen-lang-client-0839944748)
  REGION           Cloud Run region (default: us-central1)
  SERVICE          Cloud Run service name (default: rhea-backend)
  REPO             Artifact Registry repo (default: rhea)
  FIREBASE_PROJECT Firebase project ID (default: reads from .firebaserc)

Examples:
  bash deploy/teardown.sh                   # interactive teardown
  bash deploy/teardown.sh --yes             # non-interactive (CI)
  bash deploy/teardown.sh --dry-run         # preview only
USAGE
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
YES=false
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --yes)     YES=true    ;;
    --dry-run) DRY_RUN=true ;;
    --help|-h) print_banner; usage; exit 0 ;;
    *)
      err "Unknown option: $arg"
      usage
      exit 1
      ;;
  esac
done

# ---------------------------------------------------------------------------
# Confirmation helper
# ---------------------------------------------------------------------------
confirm() {
  local prompt="$1"
  if [ "$YES" = "true" ]; then
    info "Auto-confirming: ${prompt}"
    return 0
  fi
  printf "${YELLOW}${BOLD}%s [y/N] ${NC}" "$prompt"
  read -r reply
  case "$reply" in
    y|Y|yes|YES) return 0 ;;
    *) return 1 ;;
  esac
}

# ---------------------------------------------------------------------------
# Prerequisite check
# ---------------------------------------------------------------------------
check_prereqs() {
  step "Checking prerequisites"

  if command -v gcloud >/dev/null 2>&1; then
    ok "gcloud CLI found"
  else
    warn "gcloud CLI not found — Cloud Run teardown will be skipped."
    warn "Install from: https://cloud.google.com/sdk/docs/install"
    GCLOUD_MISSING=true
  fi
  GCLOUD_MISSING="${GCLOUD_MISSING:-false}"

  if command -v firebase >/dev/null 2>&1; then
    ok "firebase CLI found"
  else
    warn "firebase CLI not found — Firebase Hosting cleanup will show manual instructions."
    warn "Install with: npm i -g firebase-tools"
    FIREBASE_MISSING=true
  fi
  FIREBASE_MISSING="${FIREBASE_MISSING:-false}"
}

# ---------------------------------------------------------------------------
# Teardown: Firebase Hosting
# ---------------------------------------------------------------------------
teardown_firebase_hosting() {
  step "Firebase Hosting Cleanup"

  # Resolve Firebase project: use env var, then fall back to .firebaserc
  local fb_project="${FIREBASE_PROJECT:-}"
  if [ -z "${fb_project}" ]; then
    local firebaserc="${REPO_ROOT}/.firebaserc"
    if [ -f "${firebaserc}" ]; then
      fb_project="$(grep -o '"default"[[:space:]]*:[[:space:]]*"[^"]*"' "${firebaserc}" \
        | sed 's/.*"default"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' || true)"
    fi
  fi

  if [ "$FIREBASE_MISSING" = "true" ]; then
    warn "firebase CLI not available — manual cleanup required."
  else
    if [ -z "${fb_project}" ]; then
      warn "Firebase project ID not found — set FIREBASE_PROJECT or ensure .firebaserc exists."
    elif ! confirm "Disable Firebase Hosting for project '${fb_project}'?"; then
      info "Skipping Firebase Hosting cleanup."
    else
      if [ "$DRY_RUN" = "true" ]; then
        dim "  [dry-run] Would run: firebase hosting:disable --project ${fb_project} --force"
      else
        info "Disabling Firebase Hosting for project '${fb_project}'..."
        firebase hosting:disable --project "${fb_project}" --force \
          || warn "Could not disable hosting — may already be inactive or need 'firebase login'."
        ok "Firebase Hosting disabled for project '${fb_project}'."
      fi
    fi
  fi

  newline
  printf "${YELLOW}"
  cat <<'FIREBASE_NOTE'
  Firebase Hosting manual cleanup:
  ──────────────────────────────────────────────────────────────────────────
  To disable hosting via CLI:
    firebase hosting:disable --project <project-id>

  To delete the entire Firebase project (irreversible):
    Go to: https://console.firebase.google.com
    Project Settings → General → scroll to "Delete project"
  ──────────────────────────────────────────────────────────────────────────
FIREBASE_NOTE
  printf "${NC}"
}

# ---------------------------------------------------------------------------
# Teardown: Cloud Run
# ---------------------------------------------------------------------------
teardown_cloudrun() {
  step "Google Cloud Run — Delete Service"

  if [ "$GCLOUD_MISSING" = "true" ]; then
    warn "gcloud CLI not found — skipping Cloud Run teardown."
    return 0
  fi

  # Check if service exists
  local service_exists=false
  if gcloud run services describe "${SERVICE}" \
      --project "${PROJECT_ID}" \
      --region "${REGION}" \
      --quiet >/dev/null 2>&1; then
    service_exists=true
    local service_url
    service_url="$(gcloud run services describe "${SERVICE}" \
      --project "${PROJECT_ID}" \
      --region "${REGION}" \
      --format 'value(status.url)' 2>/dev/null || echo "(unknown)")"
    info "Found Cloud Run service:"
    dim "    Name   : ${SERVICE}"
    dim "    Region : ${REGION}"
    dim "    Project: ${PROJECT_ID}"
    dim "    URL    : ${service_url}"
  else
    warn "Cloud Run service '${SERVICE}' not found in project '${PROJECT_ID}' / region '${REGION}'."
    warn "Nothing to delete."
    service_exists=false
  fi

  if [ "$service_exists" = "true" ]; then
    newline
    if ! confirm "Delete Cloud Run service '${SERVICE}'? This is IRREVERSIBLE."; then
      info "Skipping Cloud Run service deletion."
    else
      if [ "$DRY_RUN" = "true" ]; then
        dim "  [dry-run] Would run: gcloud run services delete ${SERVICE} --region ${REGION} --project ${PROJECT_ID} --quiet"
      else
        info "Deleting Cloud Run service '${SERVICE}'..."
        gcloud run services delete "${SERVICE}" \
          --region "${REGION}" \
          --project "${PROJECT_ID}" \
          --quiet
        ok "Cloud Run service '${SERVICE}' deleted."
      fi
    fi
  fi

  # ── Artifact Registry cleanup (optional) ──────────────────────────────────
  step "Google Artifact Registry — Image Cleanup (optional)"

  local repo_exists=false
  if gcloud artifacts repositories describe "${REPO}" \
      --location="${REGION}" \
      --project="${PROJECT_ID}" \
      --quiet >/dev/null 2>&1; then
    repo_exists=true
    info "Found Artifact Registry repository '${REPO}' in ${REGION}."
  else
    info "Artifact Registry repository '${REPO}' not found — nothing to clean."
  fi

  if [ "$repo_exists" = "true" ]; then
    newline
    warn "The Artifact Registry repo '${REPO}' contains Docker images."
    warn "Deleting the repo frees storage (first 0.5 GB/month is free)."
    newline
    if ! confirm "Delete Artifact Registry repo '${REPO}' and ALL images in it?"; then
      info "Skipping Artifact Registry cleanup."
      dim "  To clean up images manually:"
      dim "    gcloud artifacts repositories delete ${REPO} --location=${REGION} --project=${PROJECT_ID}"
    else
      if [ "$DRY_RUN" = "true" ]; then
        dim "  [dry-run] Would run: gcloud artifacts repositories delete ${REPO} --location=${REGION} --project=${PROJECT_ID} --quiet"
      else
        info "Deleting Artifact Registry repository '${REPO}'..."
        gcloud artifacts repositories delete "${REPO}" \
          --location="${REGION}" \
          --project="${PROJECT_ID}" \
          --quiet
        ok "Artifact Registry repo '${REPO}' deleted."
      fi
    fi
  fi
}

# ---------------------------------------------------------------------------
# Oracle VM reminder (never auto-delete)
# ---------------------------------------------------------------------------
print_oracle_reminder() {
  step "Oracle Cloud VM — NOT deleted (backup + monitoring layer)"

  printf "${YELLOW}"
  cat <<'ORACLE'
  The Oracle Cloud VM is intentionally skipped by this teardown script.
  It runs backup and monitoring tasks. Auto-deleting it would require
  manual re-provisioning from scratch.

  If you truly want to decommission the Oracle VM:
  ──────────────────────────────────────────────────────────────────────────
  1. Stop any running services:
       ssh ubuntu@<VM_IP> "docker compose --env-file ~/.env.rhea down"

  2. Delete the instance in Oracle Cloud Console:
       Compute → Instances → rhea-oracle-vm → Terminate
  ──────────────────────────────────────────────────────────────────────────
ORACLE
  printf "${NC}"
}

# ---------------------------------------------------------------------------
# Teardown summary
# ---------------------------------------------------------------------------
print_summary() {
  step "Teardown Summary"

  if [ "$DRY_RUN" = "true" ]; then
    printf "${YELLOW}${BOLD}  DRY-RUN — no resources were modified.${NC}\n"
    return 0
  fi

  printf "${BOLD}"
  printf "  %-28s  %s\n" "Resource" "Status"
  printf "  %-28s  %s\n" "────────────────────────────" "──────────────────────"
  printf "${NC}"
  printf "  %-28s  %s\n" "Firebase Hosting"            "Disabled (if confirmed)"
  printf "  %-28s  %s\n" "Google Cloud Run service"   "Deleted (if confirmed)"
  printf "  %-28s  %s\n" "Artifact Registry repo"     "Deleted (if confirmed)"
  printf "  %-28s  %s\n" "Redis Cloud"                "NOT touched (managed)"
  printf "  %-28s  %s\n" "Oracle VM"                  "NOT touched (safe)"
  newline
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  print_banner

  if [ "$DRY_RUN" = "true" ]; then
    printf "${YELLOW}${BOLD}  DRY-RUN MODE — no changes will be made.${NC}\n\n"
  fi

  check_prereqs
  teardown_firebase_hosting
  teardown_cloudrun
  print_oracle_reminder
  print_summary

  ok "Teardown script complete."
  newline
}

main "$@"
