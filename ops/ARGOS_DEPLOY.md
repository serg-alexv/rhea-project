# Argos Deployment Guide

> COWORK desk observation daemon — the hundred-eyed watchman.

## What It Does

`argos_pager.py` gives the COWORK/Argos desk continuous observation of all Rhea office activity without relying on the human as intermediary. It watches git, relay messages, inbox files, and desk leases/snapshots.

## Quick Start

```bash
# One-shot scan (safest — see everything, change nothing)
python3 ops/argos_pager.py scan

# Watchtower view (all desks at a glance)
python3 ops/argos_pager.py status

# Full boot (lease + drain + snapshot)
python3 ops/argos_pager.py boot

# Daemon mode (continuous — runs until Ctrl+C)
python3 ops/argos_pager.py watch --interval 120
```

## Deployment Options

### Option 1: Cowork Scheduled Shortcut (easiest)

Create a shortcut in Cowork Desktop that runs `scan` periodically:

```
Shortcut: argos-scan
Schedule: every 5 minutes
Command: python3 /path/to/rhea-project/ops/argos_pager.py scan
```

Limitation: Only runs when Cowork is open. No true daemon.

### Option 2: Host cron (recommended for now)

```bash
# Add to crontab (every 2 minutes)
crontab -e
*/2 * * * * cd /path/to/rhea-project && python3 ops/argos_pager.py scan >> /tmp/argos.log 2>&1
```

### Option 3: systemd service (production)

```ini
# /etc/systemd/system/rhea-agent@COWORK.service
[Unit]
Description=Rhea Agent (COWORK/Argos)
After=network-online.target

[Service]
Type=simple
User=agent
WorkingDirectory=/opt/rhea-project
ExecStartPre=/bin/bash -lc 'test ! -f ./STOP'
ExecStart=/usr/bin/python3 ops/argos_pager.py watch --interval 120
Restart=always
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ReadWritePaths=/opt/rhea-project
Environment=PYTHONUNBUFFERED=1
Environment=RHEA_AGENT_ID=COWORK

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now rhea-agent@COWORK.service
sudo journalctl -u rhea-agent@COWORK.service -f
```

### Option 4: Terminal companion to Claude Code (best for B2 co-operation)

```bash
# In a tmux pane alongside B2's terminal
tmux new-session -s argos
python3 ops/argos_pager.py watch --interval 60
```

## Commands Reference

| Command | Description |
|---------|-------------|
| `watch` | Daemon: poll git + inbox + desks, alert on changes |
| `scan` | One-shot: scan everything, print report |
| `inbox` | Show pending COWORK relay messages + inbox files |
| `status` | All-desks watchtower view |
| `report` | Generate markdown observation report |
| `alert <target> <msg>` | Send alert via relay (triple-write) |
| `heartbeat` | Update COWORK lease + Firestore |
| `boot` | Full boot protocol (lease + drain + snapshot) |

## Architecture

```
argos_pager.py
├── Git monitoring (pull + log diff)
├── Relay inbox (COWORK-targeted messages)
├── Desk aggregation (leases + snapshots for all desks)
├── Alert system (triple-write: JSONL + Firestore + markdown)
├── Hash-chained audit (shared relay_chain.jsonl)
├── Watcher state (argos/watcher_state.json — survives restarts)
└── Observations log (argos/observations.jsonl)
```

Compatible with QWRR infrastructure (docs/qwrr-layer.md):
- Shared envelope v1 format
- Shared relay_mailbox.jsonl + relay_chain.jsonl
- Shared lease/snapshot directories
- Same Firestore project (rhea-office-sync)

## State Files

| File | Purpose |
|------|---------|
| `ops/virtual-office/argos/watcher_state.json` | Persistent watcher state |
| `ops/virtual-office/argos/observations.jsonl` | Observation log |
| `ops/virtual-office/leases/COWORK.json` | COWORK desk lease |
| `ops/virtual-office/snapshots/COWORK.json` | COWORK desk snapshot |

---
**Author:** Argos (COWORK desk)
