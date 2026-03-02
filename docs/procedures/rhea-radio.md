# RHEA Radio

Date: 2026-02-28  
Owner: ORION  
Status: ACTIVE

## Objective
Duplicate agent work signals into a continuous local "radio" channel:
- live feed log
- macOS notifications

This is the operator-facing frequency for ongoing work visibility.

## Commands
```bash
bash scripts/rhea.sh radio start --interval 2
bash scripts/rhea.sh radio status
bash scripts/rhea.sh radio tail 40
bash scripts/rhea.sh radio listen
bash scripts/rhea.sh radio stop

# NDI/screen-capture watchdog (feeds radio)
bash scripts/rhea.sh ndi start --interval 6
bash scripts/rhea.sh ndi status
bash scripts/rhea.sh ndi tail 40
bash scripts/rhea.sh ndi stop

# Queue/log overflow maintainer + UI applet
bash scripts/rhea.sh queue start --interval 30
bash scripts/rhea.sh queue status
bash scripts/rhea.sh queue compact
bash scripts/rhea.sh queue-applet
```

## Signal Sources
- `opera/ops/virtual-office/relay_mailbox.jsonl`
- `opera/ops/virtual-office/relay_acks.jsonl`
- `logs/bridge_calls.jsonl`
- `opera/tasks/queue.jsonl`
- `opera/metrics/ndi_trace.jsonl`
- `opera/metrics/queue_guard_trace.jsonl`

## Artifacts
- Feed: `opera/metrics/radio_feed.jsonl`
- Pulse: `opera/metrics/radio_pulse.json`
- State: `.rhea/radio/state.json`
- Daemon stdout: `.rhea/radio/radio.stdout.log`
- NDI pulse: `opera/metrics/ndi_pulse.json`
- Queue health pulse: `opera/metrics/queue_health.json`
- Compact archives: `opera/metrics/compact/*.jsonl.gz`

## Behavior
- High-signal events notify by default (P0/P1 relay, bridge errors, task add/claim/complete/blocked).
- Dedup cooldown prevents duplicate spam.
- Full event stream is always appended to feed log.
- Every ~30s, radio writes a lossy-compressed `radio_pulse.json` health summary.
- Queue guard trims overflowing logs and archives old lines as gzip for compact retention.

## Rule
For operator-critical workflows, radio stays ON during active work blocks.
