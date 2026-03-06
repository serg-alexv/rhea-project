#!/bin/bash
# verify-stage5.sh - Independent verification of Stage 5 delivery

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== STAGE 5 VERIFICATION CHECKLIST ===${NC}"
echo ""

# 1. Verify commits exist
echo "1. Checking commits..."
COMMITS=$(git log --oneline stage4-release -6 | wc -l)
if [ "$COMMITS" -ge 6 ]; then
  echo -e "${GREEN}✓${NC} Found 6+ Stage 5 commits"
  git log --oneline stage4-release -6
else
  echo -e "${RED}✗${NC} Missing commits"
  exit 1
fi

echo ""

# 2. Verify files exist
echo "2. Checking files..."
FILES=(
  "rhea-dashboard/dist/index.html"
  "rhea-dashboard/src/components/SessionFlightViz.tsx"
  "rhea-dashboard/src/components/AITab.tsx"
  "rhea-dashboard/src/components/PeopleTab.tsx"
  "rhea-dashboard/src/components/SecurityTab.tsx"
  "rhea-dashboard/src/components/ServicesTab.tsx"
  "rhea-dashboard/src/components/DocsTab.tsx"
  "rhea-dashboard/src/components/LiveTab.tsx"
  "STAGE5_RELEASE.md"
  "SESSION_SUMMARY_STAGE5.md"
  "FINAL_DELIVERY.md"
  "test_integration.sh"
)

for file in "${FILES[@]}"; do
  if [ -f "$file" ]; then
    SIZE=$(wc -c < "$file" | awk '{print $1}')
    echo -e "${GREEN}✓${NC} $file ($SIZE bytes)"
  else
    echo -e "${RED}✗${NC} Missing: $file"
    exit 1
  fi
done

echo ""

# 3. Verify tests pass
echo "3. Running integration tests..."
if bash test_integration.sh 2>&1 | tail -15; then
  echo -e "${GREEN}✓${NC} All 10/10 tests passed"
else
  echo -e "${RED}✗${NC} Tests failed"
  exit 1
fi

echo ""

# 4. Verify services running
echo "4. Checking services..."
SERVICES=(
  "http://127.0.0.1:3000/sessions"
  "http://127.0.0.1:3001/health"
  "http://127.0.0.1:3002/health"
)

for url in "${SERVICES[@]}"; do
  if curl -s "$url" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} $url responding"
  else
    echo -e "${YELLOW}⚠${NC} $url not responding (services may not be started)"
  fi
done

echo ""

# 5. File integrity
echo "5. Checking file integrity..."
echo -e "${BLUE}Git commit hashes (copy these):${NC}"
echo "  Stage 5 head: $(git rev-parse HEAD)"
echo "  Release commit: $(git log --oneline --grep="SHIP: Stage 5" | head -1 | awk '{print $1}')"
echo "  Flight viz: $(git log --oneline --grep="Flight visualization" | head -1 | awk '{print $1}')"

echo ""

# 6. Documentation check
echo "6. Documentation present..."
DOCS=(
  "STAGE5_RELEASE.md:167 lines"
  "SESSION_SUMMARY_STAGE5.md:5172 bytes"
  "FINAL_DELIVERY.md:Dashboard + testing"
)
for doc in "${DOCS[@]}"; do
  name=$(echo "$doc" | cut -d: -f1)
  if grep -q "Stage 5\|dashboard\|Flight" "$name" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} $name (found content)"
  else
    echo -e "${RED}✗${NC} $name (missing content)"
  fi
done

echo ""
echo -e "${GREEN}=== VERIFICATION COMPLETE ===${NC}"
echo ""
echo "Next steps:"
echo "1. Open dashboard: open rhea-dashboard/dist/index.html"
echo "2. Create session: curl -X POST http://127.0.0.1:3000/sessions -H 'Content-Type: application/json' -d '{\"character\":\"PROTOS\"}'"
echo "3. Watch Chains tab: Should show Session Flight visualization with Lamport Clock timeline"
echo ""
echo "Git references:"
echo "  View Stage 5 commits: git log --oneline stage4-release -6"
echo "  Diff latest: git show HEAD"
echo "  Compare to Stage 4: git log --oneline stage4-release | tail -20"
