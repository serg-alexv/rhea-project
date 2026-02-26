#!/usr/bin/env bash
# deploy/cloudrun/deploy.sh — One-command Cloud Run deploy for Rhea backend
# Usage:
#   bash deploy/cloudrun/deploy.sh                   # uses default PROJECT_ID
#   PROJECT_ID=my-other-project bash deploy/cloudrun/deploy.sh
#   VERCEL_ORIGIN=https://myapp.vercel.app bash deploy/cloudrun/deploy.sh
set -euo pipefail

# ---------------------------------------------------------------------------
# Config — override via env vars or edit defaults here
# ---------------------------------------------------------------------------
PROJECT_ID="${PROJECT_ID:-gen-lang-client-0839944748}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-rhea-backend}"
REPO="${REPO:-rhea}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE}"
VERCEL_ORIGIN="${VERCEL_ORIGIN:-}"   # e.g. https://rhea-atlas.vercel.app

# Path to .env file (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENV_FILE="${ENV_FILE:-${PROJECT_ROOT}/.env}"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
info()  { echo "[deploy] $*"; }
die()   { echo "[deploy] ERROR: $*" >&2; exit 1; }

require_cmd() { command -v "$1" &>/dev/null || die "'$1' not found — install gcloud SDK first"; }
require_cmd gcloud
require_cmd docker

# ---------------------------------------------------------------------------
# Load .env → exported env vars (skip comments / blanks)
# ---------------------------------------------------------------------------
if [[ -f "${ENV_FILE}" ]]; then
  info "Loading env from ${ENV_FILE}"
  set -a
  # shellcheck disable=SC1090
  source <(grep -v '^\s*#' "${ENV_FILE}" | grep -v '^\s*$')
  set +a
else
  die ".env file not found at ${ENV_FILE}. Copy .env.example and fill it in."
fi

# Validate required keys are non-empty
for VAR in OPENAI_API_KEY ANTHROPIC_API_KEY GEMINI_API_KEY OPENROUTER_API_KEY REDIS_URL; do
  [[ -n "${!VAR:-}" ]] || die "${VAR} is not set in ${ENV_FILE}"
done

# ---------------------------------------------------------------------------
# 1. Set active project
# ---------------------------------------------------------------------------
info "Setting project to ${PROJECT_ID}"
gcloud config set project "${PROJECT_ID}" --quiet

# ---------------------------------------------------------------------------
# 2. Enable required APIs (idempotent)
# ---------------------------------------------------------------------------
info "Enabling required GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  --quiet

# ---------------------------------------------------------------------------
# 3. Create Artifact Registry repo if it doesn't exist
# ---------------------------------------------------------------------------
if ! gcloud artifacts repositories describe "${REPO}" \
     --location="${REGION}" --quiet &>/dev/null; then
  info "Creating Artifact Registry repository '${REPO}'..."
  gcloud artifacts repositories create "${REPO}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="Rhea backend Docker images" \
    --quiet
fi

# ---------------------------------------------------------------------------
# 4. Authenticate Docker to Artifact Registry
# ---------------------------------------------------------------------------
info "Configuring Docker auth for ${REGION}..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# ---------------------------------------------------------------------------
# 5. Build and push Docker image
# ---------------------------------------------------------------------------
COMMIT_SHA="$(git -C "${PROJECT_ROOT}" rev-parse --short HEAD 2>/dev/null || echo "local")"
FULL_IMAGE="${IMAGE}:${COMMIT_SHA}"
LATEST_IMAGE="${IMAGE}:latest"

info "Building Docker image: ${FULL_IMAGE}"
docker build \
  --tag "${FULL_IMAGE}" \
  --tag "${LATEST_IMAGE}" \
  --cache-from "${LATEST_IMAGE}" \
  --file "${PROJECT_ROOT}/Dockerfile" \
  "${PROJECT_ROOT}"

info "Pushing image to Artifact Registry..."
docker push "${FULL_IMAGE}"
docker push "${LATEST_IMAGE}"

# ---------------------------------------------------------------------------
# 6. Build env-var string for Cloud Run
# ---------------------------------------------------------------------------
ENV_VARS="OPENAI_API_KEY=${OPENAI_API_KEY}"
ENV_VARS+=",ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}"
ENV_VARS+=",GEMINI_API_KEY=${GEMINI_API_KEY}"
ENV_VARS+=",OPENROUTER_API_KEY=${OPENROUTER_API_KEY}"
ENV_VARS+=",REDIS_URL=${REDIS_URL}"
# Optional extras from .env
for OPTIONAL in DEEPSEEK_API_KEY AZURE_OPENAI_ENDPOINT AZURE_OPENAI_API_KEY TRIBUNAL_API_KEYS; do
  if [[ -n "${!OPTIONAL:-}" ]]; then
    ENV_VARS+=",${OPTIONAL}=${!OPTIONAL}"
  fi
done

# ---------------------------------------------------------------------------
# 7. Build CORS / allowed-origins list
# ---------------------------------------------------------------------------
# Always allow localhost for local dev; add Vercel origin if provided
CORS_ORIGINS="http://localhost:3000,http://localhost:5173"
if [[ -n "${VERCEL_ORIGIN}" ]]; then
  CORS_ORIGINS="${CORS_ORIGINS},${VERCEL_ORIGIN}"
fi
# The app currently sets allow_origins=["*"] in rhead.py, but we pass this as
# an env var so you can tighten it later without a code change.
ENV_VARS+=",ALLOWED_ORIGINS=${CORS_ORIGINS}"

# ---------------------------------------------------------------------------
# 8. Deploy to Cloud Run
# ---------------------------------------------------------------------------
info "Deploying '${SERVICE}' to Cloud Run in ${REGION}..."
gcloud run deploy "${SERVICE}" \
  --image "${FULL_IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 1 \
  --port 8000 \
  --timeout 300 \
  --concurrency 80 \
  --set-env-vars "${ENV_VARS}" \
  --quiet

# ---------------------------------------------------------------------------
# 9. Output the service URL
# ---------------------------------------------------------------------------
SERVICE_URL="$(gcloud run services describe "${SERVICE}" \
  --region "${REGION}" \
  --format 'value(status.url)')"

info "-----------------------------------------------------------"
info "Deployment complete."
info "Service URL : ${SERVICE_URL}"
info "Health check: ${SERVICE_URL}/health"
info "API root    : ${SERVICE_URL}/"
info "-----------------------------------------------------------"
echo ""
echo "${SERVICE_URL}"
