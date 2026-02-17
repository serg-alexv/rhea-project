#!/usr/bin/env bash
# deploy_tribunal.sh — One-command Tribunal API deployment
# Usage:
#   ./scripts/deploy_tribunal.sh local    # Build + run locally (port 8400)
#   ./scripts/deploy_tribunal.sh fly      # Deploy to Fly.io
#   ./scripts/deploy_tribunal.sh railway  # Deploy to Railway
#   ./scripts/deploy_tribunal.sh stop     # Stop local container
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="rhea-tribunal"
CONTAINER="rhea-tribunal-local"
PORT="${TRIBUNAL_PORT:-8400}"

cmd="${1:-help}"

case "$cmd" in
  local)
    echo "Building $IMAGE..."
    docker build -f "$ROOT/Dockerfile.tribunal" -t "$IMAGE:latest" "$ROOT"

    # Stop existing if running
    docker rm -f "$CONTAINER" 2>/dev/null || true

    echo "Starting on port $PORT..."
    docker run -d \
      --name "$CONTAINER" \
      -p "$PORT:8400" \
      --env-file "$ROOT/.env" \
      "$IMAGE:latest"

    echo "Waiting for health..."
    for i in $(seq 1 10); do
      if curl -sf "http://localhost:$PORT/health" >/dev/null 2>&1; then
        echo "Tribunal API live at http://localhost:$PORT"
        echo "Swagger: http://localhost:$PORT/docs"
        curl -s "http://localhost:$PORT/health" | python3 -m json.tool
        exit 0
      fi
      sleep 1
    done
    echo "Health check failed. Logs:"
    docker logs "$CONTAINER"
    exit 1
    ;;

  fly)
    if ! command -v flyctl &>/dev/null; then
      echo "Install Fly.io CLI: curl -L https://fly.io/install.sh | sh"
      exit 1
    fi
    cd "$ROOT"
    echo "Deploying to Fly.io (region: fra)..."
    flyctl deploy --config fly.toml
    echo "Done. Check: flyctl status"
    ;;

  railway)
    if ! command -v railway &>/dev/null; then
      echo "Install Railway CLI: npm i -g @railway/cli"
      exit 1
    fi
    cd "$ROOT"
    echo "Deploying to Railway..."
    railway up
    echo "Done. Check: railway status"
    ;;

  stop)
    docker rm -f "$CONTAINER" 2>/dev/null && echo "Stopped." || echo "Not running."
    ;;

  help|*)
    echo "Usage: $0 {local|fly|railway|stop}"
    echo ""
    echo "  local    — Docker build + run on port $PORT"
    echo "  fly      — Deploy to Fly.io (needs flyctl + fly.toml)"
    echo "  railway  — Deploy to Railway (needs railway CLI)"
    echo "  stop     — Stop local Docker container"
    echo ""
    echo "Env vars (set in .env or export):"
    echo "  TRIBUNAL_API_KEYS   — comma-separated API keys"
    echo "  TRIBUNAL_PORT       — port (default 8400)"
    echo "  OPENAI_API_KEY      — for GPT models"
    echo "  ANTHROPIC_API_KEY   — for Claude models"
    echo "  GOOGLE_API_KEY      — for Gemini models"
    echo "  MISTRAL_API_KEY     — for Mistral models"
    echo "  DEEPSEEK_API_KEY    — for DeepSeek models"
    echo "  GROQ_API_KEY        — for Groq models"
    ;;
esac
