#!/usr/bin/env bash
# Bridge Probe — daily health check (CORE_COORDINATOR_DIRECTIVE requirement)
# Usage: bash ops/bridge-probe.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== RHEA BRIDGE PROBE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo ""

# Provider status
echo "--- PROVIDERS ---"
python3 src/rhea_bridge.py status 2>/dev/null || echo "BRIDGE UNREACHABLE"
echo ""

# Tier routing
echo "--- TIERS ---"
python3 src/rhea_bridge.py tiers 2>/dev/null || echo "TIERS UNREACHABLE"
echo ""

# Call stats (last 24h)
echo "--- 24H CALL STATS ---"
if [[ -f logs/bridge_calls.jsonl ]]; then
    CUTOFF=$(date -u -v-24H +%Y-%m-%dT%H:%M:%S 2>/dev/null || date -u -d "24 hours ago" +%Y-%m-%dT%H:%M:%S 2>/dev/null || echo "2000-01-01")
    TOTAL=$(grep -c "\"ts\"" logs/bridge_calls.jsonl 2>/dev/null || echo 0)
    RECENT=$(awk -v cutoff="$CUTOFF" -F'"ts":"' '{split($2,a,"\""); if(a[1]>=cutoff) c++} END{print c+0}' logs/bridge_calls.jsonl 2>/dev/null || echo 0)
    ERRORS=$(awk -v cutoff="$CUTOFF" -F'"ts":"' '{split($2,a,"\""); if(a[1]>=cutoff && /error/) e++} END{print e+0}' logs/bridge_calls.jsonl 2>/dev/null || echo 0)
    echo "Total calls (all time): $TOTAL"
    echo "Calls (24h): $RECENT"
    echo "Errors (24h): $ERRORS"
    if [[ $RECENT -gt 0 ]]; then
        ERR_RATE=$((ERRORS * 100 / RECENT))
        echo "Error rate: ${ERR_RATE}%"
    fi
else
    echo "No call log found"
fi
echo ""

# NDI status
echo "--- NDI ---"
python3 src/ndi_bridge.py status 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Available: {d.get(\"available\")}, Sources: {d.get(\"sources_on_network\",0)}')" 2>/dev/null || echo "NDI UNAVAILABLE"
echo ""

# Task queue
echo "--- TASKS ---"
python3 -c "
import sys; sys.path.insert(0,'src')
from task_db import TaskDB
s = TaskDB().summary()
for k,v in s['counts'].items(): print(f'  {k}: {v}')
print(f'  stale: {s[\"stale_count\"]}')
" 2>/dev/null || echo "TASK DB UNAVAILABLE"
echo ""

# Governor
echo "--- GOVERNOR ---"
python3 -c "
import sys; sys.path.insert(0,'src')
from token_governor import TokenGovernor
g = TokenGovernor()
for agent in ['rex','orion','gemini','shared']:
    s = g.status(agent)
    print(f'  {agent}: T={s.get(\"T_day\",0)} \$={s.get(\"dollar_day\",0):.4f} mode={s.get(\"mode\",\"?\")}')
" 2>/dev/null || echo "GOVERNOR UNAVAILABLE"

echo ""
echo "=== PROBE COMPLETE ==="
