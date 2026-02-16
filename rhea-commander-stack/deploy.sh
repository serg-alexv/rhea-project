#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# Rhea Commander Stack — One-Command Deploy
# ═══════════════════════════════════════════════════════════════
#
# USAGE:
#   ./deploy.sh up        → Pull images + start everything
#   ./deploy.sh up --lite → LiteLLM + LobeChat only (skip ComfyUI)
#   ./deploy.sh down      → Stop all (data preserved, restartable)
#   ./deploy.sh nuke      → Remove everything including volumes
#   ./deploy.sh status    → Show what's running + health
#   ./deploy.sh logs      → Tail all logs (Ctrl+C to exit)
#   ./deploy.sh test      → Verify the stack is working
#   ./deploy.sh env       → Interactive .env setup wizard
#
# FIRST TIME:
#   ./deploy.sh env       → creates .env with your API keys
#   ./deploy.sh up        → pulls images and starts
#   open http://localhost:3210  → LobeChat UI
#
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
R='\033[0;31m' G='\033[0;32m' Y='\033[0;33m' C='\033[0;36m' B='\033[1m' N='\033[0m'

log()  { echo -e "${C}[rhea]${N} $*"; }
ok()   { echo -e "${G}[  ok]${N} $*"; }
warn() { echo -e "${Y}[warn]${N} $*"; }
err()  { echo -e "${R}[ err]${N} $*"; }

# ─── Preflight checks ───
check_docker() {
  if ! command -v docker &>/dev/null; then
    err "Docker not found. Install: https://docs.docker.com/get-docker/"
    exit 1
  fi
  if ! docker compose version &>/dev/null 2>&1; then
    # Try legacy docker-compose
    if command -v docker-compose &>/dev/null; then
      COMPOSE="docker-compose"
    else
      err "Docker Compose not found. Install Docker Desktop or docker-compose-plugin."
      exit 1
    fi
  else
    COMPOSE="docker compose"
  fi
}

check_env() {
  if [ ! -f .env ]; then
    warn "No .env file found."
    echo ""
    echo "  Run ${B}./deploy.sh env${N} to create one interactively,"
    echo "  or copy .env.example to .env and fill in your keys."
    echo ""
    exit 1
  fi
}

# ─── .env Setup Wizard ───
cmd_env() {
  log "Rhea Commander — Environment Setup"
  echo ""

  if [ -f .env ]; then
    warn ".env already exists. Creating .env.new instead."
    TARGET=".env.new"
  else
    TARGET=".env"
  fi

  # Master keys (with sane defaults)
  read -rp "LiteLLM master key [sk-rhea-commander-2026]: " MASTER_KEY
  MASTER_KEY="${MASTER_KEY:-sk-rhea-commander-2026}"

  read -rp "LobeChat access code [rhea2026]: " ACCESS_CODE
  ACCESS_CODE="${ACCESS_CODE:-rhea2026}"

  echo ""
  log "API Keys (press Enter to skip any provider)"

  read -rp "  Anthropic API key: " ANTHROPIC
  read -rp "  OpenAI API key: " OPENAI
  read -rp "  Gemini API key: " GEMINI
  read -rp "  DeepSeek API key: " DEEPSEEK
  read -rp "  OpenRouter API key: " OPENROUTER
  read -rp "  HuggingFace API key: " HF
  read -rp "  Azure API key (optional): " AZURE_KEY
  read -rp "  Azure API base URL (optional): " AZURE_BASE

  cat > "$TARGET" <<ENVFILE
# Rhea Commander Stack — Generated $(date -u +%Y-%m-%dT%H:%M:%SZ)

# Access control
LITELLM_MASTER_KEY=${MASTER_KEY}
LOBECHAT_ACCESS_CODE=${ACCESS_CODE}

# Port overrides (optional)
# LITELLM_PORT=4000
# LOBECHAT_PORT=3210
# COMFYUI_PORT=8188

# Provider API Keys
ANTHROPIC_API_KEY=${ANTHROPIC:-}
OPENAI_API_KEY=${OPENAI:-}
GEMINI_API_KEY=${GEMINI:-}
DEEPSEEK_API_KEY=${DEEPSEEK:-}
OPENROUTER_API_KEY=${OPENROUTER:-}
HF_API_KEY=${HF:-}

# Azure (optional)
AZURE_API_KEY=${AZURE_KEY:-}
AZURE_API_BASE=${AZURE_BASE:-}
ENVFILE

  echo ""
  ok "Created ${TARGET}"

  # Count configured providers
  COUNT=0
  [ -n "${ANTHROPIC:-}" ] && COUNT=$((COUNT+1))
  [ -n "${OPENAI:-}" ] && COUNT=$((COUNT+1))
  [ -n "${GEMINI:-}" ] && COUNT=$((COUNT+1))
  [ -n "${DEEPSEEK:-}" ] && COUNT=$((COUNT+1))
  [ -n "${OPENROUTER:-}" ] && COUNT=$((COUNT+1))
  [ -n "${HF:-}" ] && COUNT=$((COUNT+1))

  ok "${COUNT} provider(s) configured"
  [ "$COUNT" -eq 0 ] && warn "No API keys set — LiteLLM will start but can't route requests"
  echo ""
  echo "  Next: ${B}./deploy.sh up${N}"
}

# ─── Up ───
cmd_up() {
  check_docker
  check_env

  LITE=false
  [[ "${2:-}" == "--lite" || "${2:-}" == "-l" ]] && LITE=true

  if $LITE; then
    log "Starting Rhea Commander (lite: LiteLLM + LobeChat)..."
    $COMPOSE up -d litellm lobechat
  else
    log "Starting Rhea Commander (full stack)..."
    $COMPOSE up -d
  fi

  echo ""
  ok "Stack is starting. Waiting for health checks..."
  sleep 5

  # Show status
  cmd_status_quiet

  echo ""
  echo -e "  ${B}Open LobeChat:${N}  http://localhost:${LOBECHAT_PORT:-3210}"
  echo -e "  ${B}LiteLLM API:${N}   http://localhost:${LITELLM_PORT:-4000}"
  if ! $LITE; then
    echo -e "  ${B}ComfyUI:${N}       http://localhost:${COMFYUI_PORT:-8188}"
  fi
  echo ""
  echo "  Access code: $(grep LOBECHAT_ACCESS_CODE .env 2>/dev/null | cut -d= -f2 || echo 'rhea2026')"
  echo ""
  echo "  Logs:    ${B}./deploy.sh logs${N}"
  echo "  Test:    ${B}./deploy.sh test${N}"
  echo "  Stop:    ${B}./deploy.sh down${N}"
}

# ─── Down ───
cmd_down() {
  check_docker
  log "Stopping stack (data preserved)..."
  $COMPOSE down
  ok "Stopped. Restart with: ./deploy.sh up"
}

# ─── Nuke ───
cmd_nuke() {
  check_docker
  warn "This will remove ALL containers, images, and volumes."
  read -rp "Type 'yes' to confirm: " CONFIRM
  if [ "$CONFIRM" = "yes" ]; then
    $COMPOSE down -v --remove-orphans --rmi local 2>/dev/null || true
    ok "Fully removed. Clean slate."
  else
    log "Cancelled."
  fi
}

# ─── Status ───
cmd_status_quiet() {
  $COMPOSE ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || true
}

cmd_status() {
  check_docker
  log "Rhea Commander Stack Status:"
  echo ""
  cmd_status_quiet

  # Health check endpoints
  echo ""
  if curl -sf http://localhost:${LITELLM_PORT:-4000}/health >/dev/null 2>&1; then
    ok "LiteLLM: healthy"
  else
    warn "LiteLLM: not responding"
  fi

  if curl -sf http://localhost:${LOBECHAT_PORT:-3210} >/dev/null 2>&1; then
    ok "LobeChat: healthy"
  else
    warn "LobeChat: not responding"
  fi

  if curl -sf http://localhost:${COMFYUI_PORT:-8188} >/dev/null 2>&1; then
    ok "ComfyUI: healthy"
  else
    warn "ComfyUI: not responding (may be starting or not deployed)"
  fi
}

# ─── Logs ───
cmd_logs() {
  check_docker
  log "Tailing logs (Ctrl+C to exit)..."
  $COMPOSE logs -f --tail=50
}

# ─── Test ───
cmd_test() {
  log "Testing Rhea Commander Stack..."
  echo ""
  PASS=0
  FAIL=0

  # Test 1: LiteLLM health
  if curl -sf http://localhost:${LITELLM_PORT:-4000}/health >/dev/null 2>&1; then
    ok "LiteLLM health endpoint"
    PASS=$((PASS+1))
  else
    err "LiteLLM health endpoint"
    FAIL=$((FAIL+1))
  fi

  # Test 2: LiteLLM model list
  MODELS=$(curl -sf http://localhost:${LITELLM_PORT:-4000}/v1/models \
    -H "Authorization: Bearer $(grep LITELLM_MASTER_KEY .env 2>/dev/null | cut -d= -f2 || echo 'sk-rhea-commander-2026')" \
    2>/dev/null || echo "")
  if echo "$MODELS" | grep -q '"id"' 2>/dev/null; then
    MODEL_COUNT=$(echo "$MODELS" | grep -o '"id"' | wc -l)
    ok "LiteLLM models registered: ${MODEL_COUNT} models"
    PASS=$((PASS+1))
  else
    err "LiteLLM model list (no models or auth failed)"
    FAIL=$((FAIL+1))
  fi

  # Test 3: LobeChat reachable
  if curl -sf -o /dev/null http://localhost:${LOBECHAT_PORT:-3210} 2>&1; then
    ok "LobeChat UI reachable"
    PASS=$((PASS+1))
  else
    err "LobeChat UI not reachable"
    FAIL=$((FAIL+1))
  fi

  # Test 4: ComfyUI reachable
  if curl -sf -o /dev/null http://localhost:${COMFYUI_PORT:-8188} 2>&1; then
    ok "ComfyUI reachable"
    PASS=$((PASS+1))
  else
    warn "ComfyUI not reachable (may be skipped with --lite)"
    # Don't count as fail if lite mode
  fi

  # Test 5: Quick inference test (only if at least one provider key exists)
  if grep -qE '^(ANTHROPIC|OPENAI|GEMINI|DEEPSEEK)_API_KEY=.+' .env 2>/dev/null; then
    RESPONSE=$(curl -sf http://localhost:${LITELLM_PORT:-4000}/v1/chat/completions \
      -H "Authorization: Bearer $(grep LITELLM_MASTER_KEY .env | cut -d= -f2)" \
      -H "Content-Type: application/json" \
      -d '{"model":"gemini-flash","messages":[{"role":"user","content":"Say hello in 3 words"}],"max_tokens":20}' \
      2>/dev/null || echo "")
    if echo "$RESPONSE" | grep -q '"content"' 2>/dev/null; then
      ok "Inference test passed (gemini-flash responded)"
      PASS=$((PASS+1))
    else
      warn "Inference test: no response (check API keys)"
    fi
  else
    warn "Inference test skipped: no API keys in .env"
  fi

  echo ""
  echo -e "  Results: ${G}${PASS} passed${N}, ${R}${FAIL} failed${N}"
  [ "$FAIL" -gt 0 ] && echo "  Run ${B}./deploy.sh logs${N} to debug"
}

# ─── Route ───
case "${1:-help}" in
  up)     cmd_up "$@" ;;
  down)   cmd_down ;;
  nuke)   cmd_nuke ;;
  status) cmd_status ;;
  logs)   cmd_logs ;;
  test)   cmd_test ;;
  env)    cmd_env ;;
  *)
    echo ""
    echo -e "${B}Rhea Commander Stack${N}"
    echo ""
    echo "  ./deploy.sh env        Create .env with API keys"
    echo "  ./deploy.sh up         Start full stack"
    echo "  ./deploy.sh up --lite  Start without ComfyUI"
    echo "  ./deploy.sh down       Stop (preserves data)"
    echo "  ./deploy.sh nuke       Remove everything"
    echo "  ./deploy.sh status     Check health"
    echo "  ./deploy.sh logs       Tail logs"
    echo "  ./deploy.sh test       Run verification tests"
    echo ""
    ;;
esac
