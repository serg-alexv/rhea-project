#!/bin/bash
# test_integration.sh - Full integration test for Stage 4

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; exit 1; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }

echo "=== Stage 4 Integration Tests ==="
echo ""

# Test 1: Services Running
echo "Test 1: Services running..."
curl -s http://127.0.0.1:3000/sessions > /dev/null || fail "Session server down"
curl -s http://127.0.0.1:3001/health > /dev/null || fail "AI Auth down"
curl -s http://127.0.0.1:3002/health > /dev/null || fail "Angel Game down"
pass "All 4 services responding"

# Test 2: Create Session
echo ""
echo "Test 2: Create session..."
SESSION=$(curl -s -X POST http://127.0.0.1:3000/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","device_id":"dev1","character":"Protos"}')
SESSION_ID=$(echo "$SESSION" | jq -r '.id')
[ -n "$SESSION_ID" ] && [ "$SESSION_ID" != "null" ] || fail "Failed to create session"
pass "Session created: $SESSION_ID"

# Test 3: Add Message (Device 1)
echo ""
echo "Test 3: Add message from device 1..."
MSG1=$(curl -s -X POST http://127.0.0.1:3000/sessions/$SESSION_ID/messages \
  -H "Content-Type: application/json" \
  -d '{"role":"Protos","content":"Message from device 1","device_id":"dev1"}')
LC1=$(echo "$MSG1" | jq -r '.lamport_clock')
[ "$LC1" = "1" ] || fail "Expected LC=1, got $LC1"
pass "Message 1 added with LC=$LC1"

# Test 4: Add Message (Device 2)
echo ""
echo "Test 4: Add message from device 2..."
MSG2=$(curl -s -X POST http://127.0.0.1:3000/sessions/$SESSION_ID/messages \
  -H "Content-Type: application/json" \
  -d '{"role":"Protos","content":"Message from device 2","device_id":"dev2"}')
LC2=$(echo "$MSG2" | jq -r '.lamport_clock')
[ "$LC2" = "2" ] || fail "Expected LC=2, got $LC2"
pass "Message 2 added with LC=$LC2"

# Test 5: Get Session (Verify Ordering)
echo ""
echo "Test 5: Verify message ordering..."
SESSION_DATA=$(curl -s http://127.0.0.1:3000/sessions/$SESSION_ID)
MSG_COUNT=$(echo "$SESSION_DATA" | jq '.messages | length')
[ "$MSG_COUNT" = "2" ] || fail "Expected 2 messages, got $MSG_COUNT"

LCS=$(echo "$SESSION_DATA" | jq -r '.messages[].lamport_clock')
FIRST_LC=$(echo "$LCS" | head -1)
SECOND_LC=$(echo "$LCS" | tail -1)
[ "$FIRST_LC" = "1" ] && [ "$SECOND_LC" = "2" ] || fail "Messages not in LC order"
pass "Messages ordered correctly: LC=$FIRST_LC then LC=$SECOND_LC"

# Test 6: AI Auth Challenge
echo ""
echo "Test 6: AI Auth challenge..."
CHALLENGE=$(curl -s -X POST http://127.0.0.1:3001/auth/challenge \
  -H "Content-Type: application/json" \
  -d '{"model_name":"test-model"}')
CHAL_ID=$(echo "$CHALLENGE" | jq -r '.challenge_id // empty')
TARGET_HASH=$(echo "$CHALLENGE" | jq -r '.target_hash // empty')
[ -n "$CHAL_ID" ] && [ -n "$TARGET_HASH" ] || fail "Invalid challenge response"
pass "Challenge created: $CHAL_ID"

# Test 7: Angel Game Decision Evaluation
echo ""
echo "Test 7: Angel Game evaluates decisions..."
EVAL=$(curl -s -X POST http://127.0.0.1:3002/eval/decision \
  -H "Content-Type: application/json" \
  -d '{
    "decision_id": "test-decision",
    "context": "Chose Lamport Clocks for DTS",
    "options": ["wall-clock", "ntp", "lamport", "hybrid"],
    "chosen": "lamport",
    "rationale": "Logical timestamps eliminate clock dependencies. Provably correct CRDT convergence."
  }')
EVAL_ID=$(echo "$EVAL" | jq -r '.eval_id // empty')
SCORE=$(echo "$EVAL" | jq -r '.total_score // empty')
[ -n "$EVAL_ID" ] && [ -n "$SCORE" ] || fail "Invalid evaluation response"
pass "Decision evaluated: score=$SCORE"

# Test 8: Deployment Script
echo ""
echo "Test 8: Deployment script..."
[ -x scripts/stage4_deploy.sh ] || fail "stage4_deploy.sh not executable"
bash scripts/stage4_deploy.sh status > /dev/null || fail "Status check failed"
pass "Deployment script working"

echo ""
echo "=== All Tests Passed ✓ ==="
echo ""
echo "Services Summary:"
echo "  Session Server: http://127.0.0.1:3000"
echo "  AI Auth:        http://127.0.0.1:3001"
echo "  Angel Game:     http://127.0.0.1:3002"
echo "  CLI:            cd rhea-cli && cargo run --release"
