# PROC-002 — Bridge Provider Probe + Error Mapping
Symptom: Unknown which bridge providers are alive before starting work
Cause (guess): Keys expire, quotas hit, geo-blocks, URL changes
Fix (exact commands):
```bash
export $(grep -v '^#' /Users/sa/rh.1/.env | xargs)
bash /Users/sa/rh.1/ops/bridge-probe.sh
```
Verify: Table shows LIVE/DOWN status for all 6 providers
Rollback: Manual test: `python3 src/rhea_bridge.py ask openai/gpt-4o-mini "ping"`
Notes:
- Error categories: 401=bad creds, 402=no balance, 404=wrong URL, 429=quota, 400=geo-block
- See docs/procedures/auth-errors.md for per-provider fix steps
- Probe uses /usr/bin/python3 to avoid pyenv hashlib bug
