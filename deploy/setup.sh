#!/usr/bin/env bash
## Rhea — Universal Server Setup
##
## Run from any Unix machine:
##   curl -sL https://raw.githubusercontent.com/serg-alexv/rhea-project/main/deploy/setup.sh | bash
##
## Or clone and run:
##   git clone https://github.com/serg-alexv/rhea-project.git
##   cd rhea-project && bash deploy/setup.sh
##
## What it does:
##   1. Installs Python 3.11+ (if missing)
##   2. Creates virtualenv
##   3. Installs dependencies
##   4. Creates .env from template
##   5. Initializes databases
##   6. Starts the Tribunal API server on :8400
##
## Environment variables (optional):
##   RHEA_PORT=8400          API port (default: 8400)
##   RHEA_HOST=0.0.0.0      Bind address (default: 0.0.0.0)
##   GEMINI_API_KEY=...      Google Gemini key (free tier available)
##   SKIP_VENV=1             Skip virtualenv creation
##
## Works on: Ubuntu/Debian, macOS, Alpine, Amazon Linux, Arch

set -euo pipefail

GREEN='\033[0;32m'
AMBER='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'
log()  { echo -e "${GREEN}[rhea]${NC} $*"; }
warn() { echo -e "${AMBER}[rhea]${NC} $*"; }
err()  { echo -e "${RED}[rhea]${NC} $*" >&2; }

RHEA_PORT="${RHEA_PORT:-8400}"
RHEA_HOST="${RHEA_HOST:-0.0.0.0}"

# ── 1. Detect environment ──
log "Detecting environment..."
OS="$(uname -s)"
ARCH="$(uname -m)"
log "  OS: $OS ($ARCH)"

# ── 2. Find or install Python ──
PYTHON=""
for cmd in python3.12 python3.11 python3.10 python3; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    warn "Python 3.10+ not found. Installing..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
        PYTHON="python3"
    elif command -v brew &>/dev/null; then
        brew install python@3.12
        PYTHON="python3.12"
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3 python3-pip
        PYTHON="python3"
    elif command -v apk &>/dev/null; then
        apk add --no-cache python3 py3-pip
        PYTHON="python3"
    else
        err "Cannot install Python automatically. Install Python 3.10+ manually."
        exit 1
    fi
fi

log "  Python: $($PYTHON --version)"

# ── 3. Clone repo if not in one ──
REPO_DIR=""
if [ -f "src/tribunal_api.py" ]; then
    REPO_DIR="$(pwd)"
    log "  Already in Rhea repo"
elif [ -f "../src/tribunal_api.py" ]; then
    REPO_DIR="$(cd .. && pwd)"
else
    log "Cloning Rhea..."
    if command -v git &>/dev/null; then
        git clone --depth 1 https://github.com/serg-alexv/rhea-project.git /tmp/rhea-project
        REPO_DIR="/tmp/rhea-project"
    else
        err "git not found. Install git or run from inside the repo."
        exit 1
    fi
fi

cd "$REPO_DIR"
log "  Repo: $REPO_DIR"

# ── 4. Create virtualenv ──
if [ "${SKIP_VENV:-}" != "1" ]; then
    if [ ! -d ".venv" ]; then
        log "Creating virtualenv..."
        $PYTHON -m venv .venv
    fi
    source .venv/bin/activate
    log "  venv: $(which python3)"
fi

# ── 5. Install dependencies ──
log "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# ── 6. Create .env if missing ──
if [ ! -f ".env" ]; then
    log "Creating .env from template..."
    cat > .env << 'ENVEOF'
# Rhea Environment — API Keys
# At minimum, set ONE provider key. Gemini free tier is recommended to start.

# Google Gemini (free tier: 60 RPM)
GEMINI_API_KEY=

# OpenAI (optional)
OPENAI_API_KEY=

# Anthropic (optional)
ANTHROPIC_API_KEY=

# JWT secret for auth (auto-generated if empty)
JWT_SECRET=

# Tribunal API keys (comma-separated, for external access)
TRIBUNAL_API_KEYS=dev-local

# Server config
RHEA_HOST=0.0.0.0
RHEA_PORT=8400
ENVEOF

    # Auto-generate JWT secret
    JWT=$(openssl rand -hex 32 2>/dev/null || $PYTHON -c "import secrets; print(secrets.token_hex(32))")
    sed -i.bak "s/^JWT_SECRET=$/JWT_SECRET=$JWT/" .env 2>/dev/null || \
    sed -i '' "s/^JWT_SECRET=$/JWT_SECRET=$JWT/" .env
    rm -f .env.bak

    # Pre-fill from environment if available
    if [ -n "${GEMINI_API_KEY:-}" ]; then
        sed -i.bak "s/^GEMINI_API_KEY=$/GEMINI_API_KEY=$GEMINI_API_KEY/" .env 2>/dev/null || \
        sed -i '' "s/^GEMINI_API_KEY=$/GEMINI_API_KEY=$GEMINI_API_KEY/" .env
        rm -f .env.bak
    fi

    warn ".env created at $REPO_DIR/.env"
    warn "Edit it to add your API keys (at minimum: GEMINI_API_KEY)"
fi

# ── 7. Initialize databases ──
log "Initializing databases..."
mkdir -p data
$PYTHON -c "
import sys; sys.path.insert(0, 'src')
from auth_api import _ensure_users_table
_ensure_users_table()
print('  users.db: OK')
" 2>/dev/null || warn "  users.db: skipped (will create on first auth)"

$PYTHON -c "
import sys; sys.path.insert(0, 'src')
from aletheia_api import _init_db
_init_db()
print('  proof.db: OK')
" 2>/dev/null || warn "  proof.db: skipped (will create on first proof)"

# ── 8. Start server ──
log ""
log "============================================"
log "  Rhea Tribunal API"
log "  http://${RHEA_HOST}:${RHEA_PORT}"
log "  Health: http://localhost:${RHEA_PORT}/health"
log "============================================"
log ""
log "Starting server..."

exec $PYTHON src/tribunal_api.py
