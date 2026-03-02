#!/usr/bin/env bash
# Rhea Reboot Test — verify everything recovers after restart/deploy
# Usage: bash scripts/rhea/reboot_test.sh [cloud|local|full]
#   cloud = test production endpoints only
#   local = test local services only
#   full  = both (default)

set -euo pipefail
MODE="${1:-full}"
PASS=0; FAIL=0; TOTAL=0

ok()   { TOTAL=$((TOTAL+1)); PASS=$((PASS+1)); printf "  ✓ %s\n" "$1"; }
fail() { TOTAL=$((TOTAL+1)); FAIL=$((FAIL+1)); printf "  ✗ %s\n" "$1"; }

test_binary() {
    local name="$1" path="$2"
    if command -v "$path" &>/dev/null; then
        ok "$name binary exists at $(command -v "$path")"
    else
        fail "$name binary not found"
    fi
}

test_port() {
    local name="$1" port="$2"
    if lsof -i ":$port" -sTCP:LISTEN &>/dev/null; then
        ok "$name listening on :$port"
    else
        fail "$name not listening on :$port"
    fi
}

echo "═══ Rhea Reboot Test ═══"
echo "  Mode: $MODE"
echo "  Time: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo ""

# ── Cloud tests ──
if [ "$MODE" = "cloud" ] || [ "$MODE" = "full" ]; then
    echo "── Cloud (rhea-tribunal.fly.dev) ──"
    if bash scripts/rhea/health_check.sh https://rhea-tribunal.fly.dev 2>/dev/null; then
        ok "cloud health check ALL GREEN"
    else
        fail "cloud health check has failures (see above)"
    fi
    echo ""
fi

# ── Local tests ──
if [ "$MODE" = "local" ] || [ "$MODE" = "full" ]; then
    echo "── CLI Tools ──"
    test_binary "rhea (Rust TUI)" "rhea"
    test_binary "python3" "python3"
    test_binary "pip3" "pip3"

    # Check python packages
    if python3 -c "import rhea_clipboard" 2>/dev/null; then
        ok "rhea-clipboard package importable"
    else
        fail "rhea-clipboard not installed (pip3 install -e packages/rhea-clipboard/)"
    fi

    if python3 -c "import rhea_memory" 2>/dev/null; then
        ok "rhea-memory package importable"
    else
        fail "rhea-memory not installed (pip3 install -e packages/rhea-memory/)"
    fi

    echo ""
    echo "── Local Services ──"
    test_port "tribunal API" 8400
    test_port "Atlas (Next.js)" 3000

    echo ""
    echo "── Daemon ──"
    PLIST="$HOME/Library/LaunchAgents/com.rhea.clipboard.plist"
    if [ -f "$PLIST" ]; then
        ok "clipboard daemon plist installed"
        if launchctl list com.rhea.clipboard 2>/dev/null | grep -q '"PID"'; then
            ok "clipboard daemon running"
        else
            fail "clipboard daemon installed but not running"
        fi
    else
        fail "clipboard daemon not installed"
    fi

    echo ""
    echo "── Git ──"
    BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
    ok "branch: $BRANCH"
    BEHIND=$(git rev-list --count HEAD..origin/"$BRANCH" 2>/dev/null || echo "?")
    AHEAD=$(git rev-list --count origin/"$BRANCH"..HEAD 2>/dev/null || echo "?")
    if [ "$BEHIND" = "0" ]; then
        ok "up to date with remote"
    else
        fail "behind remote by $BEHIND commits"
    fi

    echo ""
    echo "── Repo Invariants ──"
    if bash scripts/rhea/check.sh 2>/dev/null | grep -q "OK"; then
        ok "check.sh passed"
    else
        fail "check.sh failed"
    fi

    echo ""
    echo "── Databases ──"
    for db in data/proof.db data/tasks.db data/users.db; do
        if [ -f "$db" ]; then
            TABLES=$(sqlite3 "$db" ".tables" 2>/dev/null | wc -w)
            ok "$db exists ($TABLES tables)"
        else
            fail "$db missing"
        fi
    done
fi

echo ""
echo "═══════════════════════════"
printf "  Results: %d passed, %d failed, %d total\n" "$PASS" "$FAIL" "$TOTAL"

if [ "$FAIL" -gt 0 ]; then
    echo "  VERDICT: NEEDS ATTENTION"
    exit 1
else
    echo "  VERDICT: REBOOT-SAFE"
    exit 0
fi
