# Queue Maintainer + Pulse Applet

Date: 2026-02-28  
Owner: ORION  
Status: ACTIVE

## Goal
Provide a system utility that:
- shows queue/log health in UI
- prevents queue/log overflow
- stores compact archives automatically

## CLI
```bash
bash scripts/rhea.sh queue start --interval 30
bash scripts/rhea.sh queue status
bash scripts/rhea.sh queue compact
bash scripts/rhea.sh queue stop
```

## Applet UI
```bash
python3 scripts/rhea_queue_applet.py
# or:
bash scripts/rhea.sh queue-applet
```

The applet displays:
- risk + summary pulse from `opera/metrics/queue_health.json`
- per-file line/size pressure
- one-click actions: Start Guard, Stop Guard, Compact Now, Start Radio, Start/Stop NDI
- flicker controls: `Mark Flicker`, `Trace 60s`, `Trace 300s`

## Manual Flicker Marker (CLI)
```bash
bash scripts/rhea.sh flicker-mark "screen flicker observed near Script Editor popup"
```

This marker is written to `opera/metrics/ndi_trace.jsonl` and propagates to radio.

## iOS Module
`ios/RheaPreview.swiftpm` now includes `PulseMonitorView`:
- queue pulse (`/tasks/summary`)
- agent lease pulse (`/agents`)
- quick controls: `Mark Flicker`, `Wake REX`, `Create Trace Task`

## Compact Log Storage
- Archives are stored at `opera/metrics/compact/*.jsonl.gz`
- Hot logs are rewritten with only the latest `keep_lines`
- No event loss: old rows are moved, not dropped
