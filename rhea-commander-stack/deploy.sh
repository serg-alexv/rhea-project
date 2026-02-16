#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Rhea Commander Stack — Deployment Script
# ============================================================
# Usage: ./deploy.sh [command] [flags]
#
# Commands:
#   up [--lite]   Start stack (--lite skips ComfyUI)
#   down          Stop stack gracefully
#   nuke          Remove everything (containers, volumes, images)
#   status        Show running containers
#   logs [svc]    Tail logs (optional: litellm|lobechat|comfyui)
#   test          Run 5-point verification suite
#   env           Interactive .env setup wizard
#   help          Show this help
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Auto-detect docker compose command
if docker compose version &>/dev/null; then
  DC="docker compose"
elif command -v docker-compose &>/dev/null; then
  DC="docker-compose"
else
  echo "[!] Neither 'docker compose' nor 'docker-compose' found."
  echo "    Install Docker: https://docs.docker.com/get-docker/"
  exit 1
fi

header() { echo -e "\n\033[1;36m[rhea]\033[0m $1"; }
ok()     { echo -e "  \033[32m✓\033[0m $1"; }
fail()   { echo -e "  \033[31m✗\033[0m $1"; }
warn()   { echo -e "  \033[33m!\033[0m $1"; }

# ── ENV WIZARD ──────────────────────────────────────────────
cmd_env() {
  header "Interactive .env setup"

  if [[ -f .env ]]; then
    warn ".env already exists. Overwrite? (y/N)"
    read -r ans
    [[ "$ans" != "y" && "$ans" != "Y" ]] && { echo "Keeping existing .env"; return 0; }
  fi

  cp .env.example .env
  local count=0

  echo ""
  echo "Paste each API key (or press Enter to skip):"
  echo "─────────────────────────────────────────────"

  for var in ANTHROPIC_API_KEY OPENAI_API_KEY GEMINI_API_KEY DEEPSEEK_API_KEY OPENROUTER_API_KEY HF_TOKEN AZURE_API_KEY; do
    printf "  %-22s: " "$var"
    read -r val
    if [[ -n "$val" ]]; then
      # Use | as sed delimiter to avoid conflicts with API keys
      sed -i.bak "s|^${var}=.*|${var}=${val}|" .env
      count=$((count + 1))
    fi
  done

  rm -f .env.bak
  echo ""
  ok "$count provider(s) configured in .env"

  printf "  LiteLLM master key [sk-rhea-dev-key]: "
  read -r mk
  [[ -n "$mk" ]] && sed -i.bak "s|^LITELLM_MASTER_KEY=.*|LITELLM_MASTER_KEY=${mk}|" .env && rm -f .env.bak

  printf "  LobeChat access code (optional): "
  read -r ac
  [[ -n "$ac" ]] && sed -i.bak "s|^LOBECHAT_ACCESS_CODE=.*|LOBECHAT_ACCESS_CODE=${ac}|" .env && rm -f .env.bak

  echo ""
  ok ".env ready. Run: ./deploy.sh up"
}

# ── UP ──────────────────────────────────────────────────────
cmd_up() {
  [[ ! -f .env ]] && { warn "No .env found. Run: ./deploy.sh env"; exit 1; }

  if [[ "${1:-}" == "--lite" ]]; then
    header "Starting Rhea Commander (lite: LiteLLM + LobeChat)..."
    $DC up -d litellm lobechat
  else
    header "Starting Rhea Commander (full stack)..."
    $DC --profile full up -d
  fi

  echo ""
  cmd_verify_urls
}

# ── DOWN ────────────────────────────────────────────────────
cmd_down() {
  header "Stopping Rhea Commander..."
  $DC --profile full down
  ok "Stack stopped."
}

# ── NUKE ────────────────────────────────────────────────────
cmd_nuke() {
  header "⚠ This will remove ALL containers, volumes, and local images."
  printf "  Type 'yes' to confirm: "
  read -r confirm
  [[ "$confirm" != "yes" ]] && { echo "Aborted."; return 0; }

  $DC --profile full down -v --rmi local
  ok "Nuked. Clean slate."
}

# ── STATUS ──────────────────────────────────────────────────
cmd_status() {
  header "Container status:"
  $DC --profile full ps -a
}

# ── LOGS ────────────────────────────────────────────────────
cmd_logs() {
  local svc="${1:-}"
  if [[ -n "$svc" ]]; then
    $DC logs -f "$svc"
  else
    $DC --profile full logs -f --tail=50
  fi
}

# ── TEST ────────────────────────────────────────────────────
cmd_test() {
  header "Running 5-point verification..."
  local pass=0 total=5

  # 1. LiteLLM health
  if curl -sf "http://localhost:${LITELLM_PORT:-4000}/health" &>/dev/null; then
    ok "LiteLLM health check"
    pass=$((pass + 1))
  else
    fail "LiteLLM not responding on port ${LITELLM_PORT:-4000}"
  fi

  # 2. Model list
  local models
  models=$(curl -sf "http://localhost:${LITELLM_PORT:-4000}/v1/models" \
    -H "Authorization: Bearer ${LITELLM_MASTER_KEY:-sk-rhea-dev-key}" 2>/dev/null || true)
  if echo "$models" | grep -q '"id"'; then
    local model_count
    model_count=$(echo "$models" | grep -c '"id"' || true)
    ok "Model list returned ($model_count models)"
    pass=$((pass + 1))
  else
    fail "Cannot fetch model list"
  fi

  # 3. LobeChat UI
  if curl -sf "http://localhost:${LOBECHAT_PORT:-3210}" &>/dev/null; then
    ok "LobeChat UI reachable"
    pass=$((pass + 1))
  else
    fail "LobeChat not responding on port ${LOBECHAT_PORT:-3210}"
  fi

  # 4. ComfyUI (optional)
  if curl -sf "http://localhost:${COMFYUI_PORT:-8188}" &>/dev/null; then
    ok "ComfyUI reachable"
    pass=$((pass + 1))
  else
    warn "ComfyUI not running (optional, use --lite)"
    pass=$((pass + 1))
  fi

  # 5. Inference test (try gemini-flash first, then any available)
  local response
  response=$(curl -sf "http://localhost:${LITELLM_PORT:-4000}/v1/chat/completions" \
    -H "Authorization: Bearer ${LITELLM_MASTER_KEY:-sk-rhea-dev-key}" \
    -H "Content-Type: application/json" \
    -d '{"model":"gemini-flash","messages":[{"role":"user","content":"Reply with only: RHEA ONLINE"}],"max_tokens":20}' 2>/dev/null || true)
  if echo "$response" | grep -qi "rhea"; then
    ok "Inference test passed (gemini-flash)"
    pass=$((pass + 1))
  else
    fail "Inference test failed — check API keys in .env"
  fi

  echo ""
  header "Result: $pass/$total checks passed"

  if [[ $pass -ge 4 ]]; then
    echo ""
    echo "  ┌──────────────────────────────────────────────────┐"
    echo "  │  Rhea Commander is ONLINE                        │"
    echo "  │                                                  │"
    echo "  │  LiteLLM API:  http://localhost:${LITELLM_PORT:-4000}             │"
    echo "  │  LiteLLM UI:   http://localhost:${LITELLM_PORT:-4000}/ui           │"
    echo "  │  LobeChat:     http://localhost:${LOBECHAT_PORT:-3210}             │"
    echo "  │  ComfyUI:      http://localhost:${COMFYUI_PORT:-8188}             │"
    echo "  │                                                  │"
    echo "  │  API Key:      \$LITELLM_MASTER_KEY               │"
    echo "  └──────────────────────────────────────────────────┘"
    echo ""
  fi
}

# ── VERIFY URLS ─────────────────────────────────────────────
cmd_verify_urls() {
  echo "  Waiting for services to start..."
  sleep 5

  echo ""
  echo "  ┌──────────────────────────────────────────────────┐"
  echo "  │  Rhea Commander — Access Points                  │"
  echo "  │                                                  │"
  echo "  │  LiteLLM API:  http://localhost:${LITELLM_PORT:-4000}             │"
  echo "  │  LiteLLM UI:   http://localhost:${LITELLM_PORT:-4000}/ui           │"
  echo "  │  LobeChat:     http://localhost:${LOBECHAT_PORT:-3210}             │"
  echo "  │  ComfyUI:      http://localhost:${COMFYUI_PORT:-8188}             │"
  echo "  │                                                  │"
  echo "  │  Quick test:   ./deploy.sh test                  │"
  echo "  └──────────────────────────────────────────────────┘"
  echo ""
}

# ── HELP ────────────────────────────────────────────────────
cmd_help() {
  echo ""
  echo "  Rhea Commander Stack — deploy.sh"
  echo "  ════════════════════════════════"
  echo ""
  echo "  ./deploy.sh env           Set up API keys (interactive wizard)"
  echo "  ./deploy.sh up            Start full stack (LiteLLM + LobeChat + ComfyUI)"
  echo "  ./deploy.sh up --lite     Start lite stack (LiteLLM + LobeChat only)"
  echo "  ./deploy.sh down          Stop all services"
  echo "  ./deploy.sh status        Show container status"
  echo "  ./deploy.sh logs [svc]    Tail logs (optional: litellm, lobechat, comfyui)"
  echo "  ./deploy.sh test          Run 5-point verification + show URLs"
  echo "  ./deploy.sh nuke          Remove everything (requires confirmation)"
  echo "  ./deploy.sh help          Show this help"
  echo ""
}

# ── MAIN ────────────────────────────────────────────────────
case "${1:-help}" in
  env)    cmd_env ;;
  up)     cmd_up "${2:-}" ;;
  down)   cmd_down ;;
  nuke)   cmd_nuke ;;
  status) cmd_status ;;
  logs)   cmd_logs "${2:-}" ;;
  test)   cmd_test ;;
  help)   cmd_help ;;
  *)      echo "Unknown command: $1"; cmd_help; exit 1 ;;
esac
