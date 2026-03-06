#!/bin/bash
# scripts/stage4_deploy.sh - One-command deploy for all 3 services
# Usage: bash scripts/stage4_deploy.sh [start|stop|status|logs]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDFILE_SERVER="$REPO_ROOT/.pids/server.pid"
PIDFILE_AUTH="$REPO_ROOT/.pids/auth.pid"
PIDFILE_ANGEL="$REPO_ROOT/.pids/angel.pid"
LOGDIR="$REPO_ROOT/logs/stage4"

mkdir -p "$REPO_ROOT/.pids" "$LOGDIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}✓${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

build_all() {
  echo "Building all services..."
  
  cd "$REPO_ROOT/rhea-session-server"
  cargo build --release 2>&1 | grep -E "Compiling|Finished" || true
  log_info "Session server built"
  
  cd "$REPO_ROOT/rhea-ai-auth"
  cargo build --release 2>&1 | grep -E "Compiling|Finished" || true
  log_info "AI Auth built"
  
  cd "$REPO_ROOT/rhea-cli"
  cargo build --release 2>&1 | grep -E "Compiling|Finished" || true
  log_info "CLI built"
  
  cd "$REPO_ROOT/rhea-angel-game"
  cargo build --release 2>&1 | grep -E "Compiling|Finished" || true
  log_info "Angel Game built"
}

start() {
  log_info "Starting Rhea Stage 4 services..."
  
  # Session Server
  if [ -f "$PIDFILE_SERVER" ] && kill -0 "$(cat $PIDFILE_SERVER)" 2>/dev/null; then
    log_warn "Session server already running (PID: $(cat $PIDFILE_SERVER))"
  else
    cd "$REPO_ROOT/rhea-session-server"
    nohup ./target/release/server > "$LOGDIR/server.log" 2>&1 &
    echo $! > "$PIDFILE_SERVER"
    sleep 1
    if curl -s http://127.0.0.1:3000/health > /dev/null; then
      log_info "Session server started (PID: $(cat $PIDFILE_SERVER))"
    else
      log_error "Session server failed to start. Check logs: $LOGDIR/server.log"
      exit 1
    fi
  fi
  
  # AI Auth Service
  if [ -f "$PIDFILE_AUTH" ] && kill -0 "$(cat $PIDFILE_AUTH)" 2>/dev/null; then
    log_warn "AI Auth already running (PID: $(cat $PIDFILE_AUTH))"
  else
    cd "$REPO_ROOT/rhea-ai-auth"
    nohup ./target/release/ai-auth > "$LOGDIR/auth.log" 2>&1 &
    echo $! > "$PIDFILE_AUTH"
    sleep 2
    if curl -s http://127.0.0.1:3001/health > /dev/null; then
      log_info "AI Auth started (PID: $(cat $PIDFILE_AUTH))"
    else
      log_error "AI Auth failed to start. Check logs: $LOGDIR/auth.log"
      cat "$LOGDIR/auth.log"
      exit 1
    fi
  fi
  
  # Angel Game
  if [ -f "$PIDFILE_ANGEL" ] && kill -0 "$(cat $PIDFILE_ANGEL)" 2>/dev/null; then
    log_warn "Angel Game already running (PID: $(cat $PIDFILE_ANGEL))"
  else
    cd "$REPO_ROOT/rhea-angel-game"
    nohup ./target/release/rhea-angel-game > "$LOGDIR/angel.log" 2>&1 &
    echo $! > "$PIDFILE_ANGEL"
    sleep 1
    if curl -s http://127.0.0.1:3002/health > /dev/null; then
      log_info "Angel Game started (PID: $(cat $PIDFILE_ANGEL))"
    else
      log_error "Angel Game failed to start. Check logs: $LOGDIR/angel.log"
      cat "$LOGDIR/angel.log"
      exit 1
    fi
  fi
  
  echo ""
  echo "  🚀 All services running!"
  echo ""
  echo "  Session Server: http://127.0.0.1:3000"
  echo "  AI Auth:        http://127.0.0.1:3001"
  echo "  Angel Game:     http://127.0.0.1:3002"
  echo ""
  echo "  To start CLI:   cd rhea-cli && cargo run --release"
  echo "  To stop:        bash scripts/stage4_deploy.sh stop"
  echo "  To check logs:  bash scripts/stage4_deploy.sh logs"
}

stop() {
  log_info "Stopping Rhea Stage 4 services..."
  
  if [ -f "$PIDFILE_SERVER" ]; then
    PID=$(cat "$PIDFILE_SERVER")
    if kill -0 "$PID" 2>/dev/null; then
      kill "$PID"
      log_info "Session server stopped"
    fi
    rm "$PIDFILE_SERVER"
  fi
  
  if [ -f "$PIDFILE_AUTH" ]; then
    PID=$(cat "$PIDFILE_AUTH")
    if kill -0 "$PID" 2>/dev/null; then
      kill "$PID"
      log_info "AI Auth stopped"
    fi
    rm "$PIDFILE_AUTH"
  fi
  
  if [ -f "$PIDFILE_ANGEL" ]; then
    PID=$(cat "$PIDFILE_ANGEL")
    if kill -0 "$PID" 2>/dev/null; then
      kill "$PID"
      log_info "Angel Game stopped"
    fi
    rm "$PIDFILE_ANGEL"
  fi
}

status() {
  echo "Rhea Stage 4 Status"
  echo "===================="
  echo ""
  
  if [ -f "$PIDFILE_SERVER" ] && kill -0 "$(cat $PIDFILE_SERVER)" 2>/dev/null; then
    if curl -s http://127.0.0.1:3000/health > /dev/null; then
      log_info "Session Server (PID: $(cat $PIDFILE_SERVER))"
    else
      log_error "Session Server not responding"
    fi
  else
    log_error "Session Server not running"
  fi
  
  if [ -f "$PIDFILE_AUTH" ] && kill -0 "$(cat $PIDFILE_AUTH)" 2>/dev/null; then
    if curl -s http://127.0.0.1:3001/health > /dev/null; then
      log_info "AI Auth (PID: $(cat $PIDFILE_AUTH))"
    else
      log_error "AI Auth not responding"
    fi
  else
    log_error "AI Auth not running"
  fi
  
  if [ -f "$PIDFILE_ANGEL" ] && kill -0 "$(cat $PIDFILE_ANGEL)" 2>/dev/null; then
    if curl -s http://127.0.0.1:3002/health > /dev/null; then
      log_info "Angel Game (PID: $(cat $PIDFILE_ANGEL))"
    else
      log_error "Angel Game not responding"
    fi
  else
    log_error "Angel Game not running"
  fi
  
  echo ""
  echo "Logs:"
  echo "  $LOGDIR/server.log"
  echo "  $LOGDIR/auth.log"
  echo "  $LOGDIR/angel.log"
}

logs() {
  echo "=== Session Server ==="
  tail -20 "$LOGDIR/server.log" || echo "(no log yet)"
  echo ""
  echo "=== AI Auth ==="
  tail -20 "$LOGDIR/auth.log" || echo "(no log yet)"
  echo ""
  echo "=== Angel Game ==="
  tail -20 "$LOGDIR/angel.log" || echo "(no log yet)"
}

case "${1:-start}" in
  build)
    build_all
    ;;
  start)
    build_all
    start
    ;;
  stop)
    stop
    ;;
  status)
    status
    ;;
  logs)
    logs
    ;;
  *)
    echo "Usage: bash scripts/stage4_deploy.sh [build|start|stop|status|logs]"
    exit 1
    ;;
esac
