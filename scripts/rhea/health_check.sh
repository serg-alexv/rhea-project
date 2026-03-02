#!/usr/bin/env bash
# Rhea Health Check — post-deploy smoke test for all critical endpoints
# Usage: bash scripts/rhea/health_check.sh [base_url]
#   base_url defaults to https://rhea-tribunal.fly.dev

set -euo pipefail

BASE="${1:-https://rhea-tribunal.fly.dev}"
PASS=0
FAIL=0
TOTAL=0

check() {
    local name="$1" method="$2" path="$3" expect_status="${4:-200}"
    TOTAL=$((TOTAL + 1))
    local url="${BASE}${path}"
    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$url" \
        -H "Content-Type: application/json" 2>/dev/null || echo "000")
    if [ "$status" = "$expect_status" ]; then
        printf "  ✓ %-30s %s %s → %s\n" "$name" "$method" "$path" "$status"
        PASS=$((PASS + 1))
    else
        printf "  ✗ %-30s %s %s → %s (expected %s)\n" "$name" "$method" "$path" "$status" "$expect_status"
        FAIL=$((FAIL + 1))
    fi
}

check_json() {
    local name="$1" path="$2" key="$3" expect="$4"
    TOTAL=$((TOTAL + 1))
    local url="${BASE}${path}"
    local val
    val=$(curl -s "$url" 2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin).get('$key',''))" 2>/dev/null || echo "")
    if [ "$val" = "$expect" ]; then
        printf "  ✓ %-30s %s.%s = %s\n" "$name" "$path" "$key" "$val"
        PASS=$((PASS + 1))
    else
        printf "  ✗ %-30s %s.%s = '%s' (expected '%s')\n" "$name" "$path" "$key" "$val" "$expect"
        FAIL=$((FAIL + 1))
    fi
}

echo "═══ Rhea Health Check ═══"
echo "  Target: $BASE"
echo "  Time:   $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo ""

echo "── Core ──"
check "health"          GET  /health
check_json "health.status" /health status ok
check "landing page"    GET  /

echo ""
echo "── Auth ──"
check "login page"      GET  /auth/login-page
check "signup (no body)" POST /auth/signup 422
check "login (no body)"  POST /auth/login 422

echo ""
echo "── Tribunal ──"
check "tribunal (auth req)" POST /tribunal 401
check "models"          GET  /models

echo ""
echo "── Clipboard ──"
check "clipboard list"  GET  /clipboard 401
check "clipboard push"  POST /clipboard 401

echo ""
echo "── Aletheia ──"
check "proofs list"     GET  /aletheia/proofs
check "ontology"        GET  /aletheia/ontology/tree

echo ""
echo "── Operational ──"
check "agents status"   GET  /agents/status
check "governor"        GET  /governor
check "tasks"           GET  /tasks

echo ""
echo "── Feed ──"
check "feed"            GET  /feed
check "session history"  GET  /session/history 401

echo ""
echo "═══════════════════════════"
printf "  Results: %d passed, %d failed, %d total\n" "$PASS" "$FAIL" "$TOTAL"

if [ "$FAIL" -gt 0 ]; then
    echo "  STATUS: DEGRADED"
    exit 1
else
    echo "  STATUS: ALL GREEN"
    exit 0
fi
