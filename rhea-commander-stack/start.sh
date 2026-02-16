#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# Rhea Commander Stack — Quick Start / Quick Reverse
# Usage:
#   ./start.sh up      → Start all services
#   ./start.sh down    → Stop all (reversible, data preserved)
#   ./start.sh nuke    → Full remove (containers + volumes)
#   ./start.sh lite    → LiteLLM only (no Docker needed)
#   ./start.sh status  → Show running services
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

case "${1:-status}" in
  up)
    echo -e "${CYAN}Starting Rhea Commander Stack...${NC}"
    if [ ! -f .env ]; then
      echo -e "${RED}Missing .env file. Copy .env.example to .env and add your keys.${NC}"
      exit 1
    fi
    if command -v docker &>/dev/null && docker compose version &>/dev/null; then
      docker compose up -d
      echo ""
      echo -e "${GREEN}Stack running:${NC}"
      echo "  LiteLLM:  http://localhost:4000  (AI Gateway)"
      echo "  LobeChat: http://localhost:3210  (Operator UI)"
      echo "  ComfyUI:  http://localhost:8188  (Visual Gen)"
    else
      echo -e "${RED}Docker not found. Use './start.sh lite' for LiteLLM-only mode.${NC}"
    fi
    ;;

  down)
    echo -e "${CYAN}Stopping stack (data preserved)...${NC}"
    docker compose down
    echo -e "${GREEN}Stopped. Run './start.sh up' to restart.${NC}"
    ;;

  nuke)
    echo -e "${RED}Removing stack + volumes...${NC}"
    docker compose down -v --remove-orphans
    echo -e "${GREEN}Fully removed. Clean slate.${NC}"
    ;;

  lite)
    echo -e "${CYAN}Starting LiteLLM-only (no Docker)...${NC}"
    if [ ! -f .env ]; then
      echo -e "${RED}Missing .env file.${NC}"
      exit 1
    fi
    set -a && source .env && set +a
    litellm --config litellm_config.yaml --port 4000 &
    LITELLM_PID=$!
    echo "$LITELLM_PID" > .litellm.pid
    echo -e "${GREEN}LiteLLM running at http://localhost:4000 (PID: $LITELLM_PID)${NC}"
    echo "Stop with: kill \$(cat .litellm.pid)"
    ;;

  status)
    echo -e "${CYAN}Rhea Commander Stack Status:${NC}"
    if command -v docker &>/dev/null; then
      docker compose ps 2>/dev/null || echo "  Docker stack: not running"
    fi
    if [ -f .litellm.pid ]; then
      PID=$(cat .litellm.pid)
      if kill -0 "$PID" 2>/dev/null; then
        echo "  LiteLLM (standalone): running (PID $PID)"
      else
        echo "  LiteLLM (standalone): stopped"
      fi
    fi
    ;;

  *)
    echo "Usage: ./start.sh {up|down|nuke|lite|status}"
    ;;
esac
