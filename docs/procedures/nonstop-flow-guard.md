# Non-Stop Flow Guard (10 Checks)

Date: 2026-02-27
Owner: ORION
Status: ACTIVE

## Objective
Errors are expected. Stalls are not.
Flow Guard converts this rule into measurable checks over bridge call logs.

## CLI
```bash
python3 scripts/flow_guard.py
python3 scripts/flow_guard.py --window-hours 48 --json
bash scripts/rhea.sh flow-guard --window-hours 24
```

## Data Source
- `logs/bridge_calls.jsonl`
- Output artifact: `opera/metrics/flow_guard.json`

## Check Set (10)
- C1 Log parse integrity
- C2 Activity present
- C3 Success ratio
- C4 Error recovery ratio
- C5 Consecutive error cap
- C6 Recovery speed P95
- C7 Post-error continuation
- C8 Fallback agility
- C9 Terminal health
- C10 Observability coverage

## Operational Rule
- Green target: `checks_passed >= 8`
- Excellent target: `checks_passed == 10`
- If `checks_passed < 8`, trigger remediation block (rotate key, switch profile, reroute provider, audit queue).

## Notes
- This is continuity telemetry, not semantic correctness proof.
- Pair with reviewer evidence gate for final acceptance.
