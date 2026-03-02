# OpenClaw Patterns as Flows

Purpose: treat organizational workflows as executable state flows, not ad-hoc prompts.

Runtime:
- Flow engine: [openclaw_flow_engine.py](/Users/sa/rh.1/src/flows/openclaw_flow_engine.py)
- CLI: [rhea_flow.py](/Users/sa/rh.1/scripts/rhea_flow.py)
- Interactive shell: [rhea_shell.py](/Users/sa/rh.1/scripts/rhea_shell.py)

## Available Flow IDs

1. `openclaw.org.sync`
- Goal: send critical org message to family ring and wait for ack.
- Steps: `taskdb_health -> relay_send -> relay_wait_ack -> wake_rex -> boot_rex -> relay_wait_ack`.

2. `openclaw.continuity.smoke`
- Goal: verify portability continuity path end-to-end.
- Steps: `continuity_pack -> continuity_verify_latest`.

3. `openclaw.p0.recovery`
- Goal: recover from communication stall quickly.
- Steps: `taskdb_health -> wake_rex -> boot_rex`.

## Commands

```bash
# list specs
python3 scripts/rhea_flow.py list

# run org sync (Rex requirements request)
python3 scripts/rhea_flow.py run openclaw.org.sync \
  --targets REX --source ORION --priority P0 --ack-timeout 45 \
  --message "Reqs for rhea_shell/workflows..."

# run continuity smoke
python3 scripts/rhea_flow.py run openclaw.continuity.smoke --label nightly

# latest workflow completions
python3 scripts/rhea_flow.py latest --limit 10
```

## Ledger

- Append-only run telemetry: `opera/metrics/workflow_runs.jsonl`
- Each run writes:
  - `workflow.start`
  - `workflow.step` per transition
  - `workflow.end`

This gives post-mortem traceability and deterministic replay of org flows.

