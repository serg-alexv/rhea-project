# Autonudge Ops (Industrial Guardrails)

## Goal
Keep long-running terminal workflows alive without blind Enter-spam and without losing operator control.

## Components
- `scripts/rhea/autonudge_tmux.py`
- `scripts/rhea/autonudge.sh`
- `scripts/rhea/verify_jsonl_chain.py`

## Guarantees
- Explicit target scope: daemon can act only on the tmux pane passed via `--target-pane`.
- Command gate: stale nudges are blocked unless pane command matches `--allow-command` regex.
- Bounded actuation:
  - `--cooldown-sec`
  - `--max-nudges-per-hour`
  - `--max-total-nudges`
- Hard stop controls:
  - `STOP` sentinel: immediate daemon exit.
  - `PAUSE` sentinel: daemon idles, no actuation.
- Tamper-evident audit:
  - events append to `.entire/logs/autonudge.jsonl`
  - each record has `seq`, `prev_hash`, `entry_hash` (SHA-256 chain)
  - chain is machine-verifiable.

## Start
```bash
bash scripts/rhea.sh autonudge start \
  --target-pane %12 \
  --mode nudge \
  --idle-sec 90 \
  --cooldown-sec 45 \
  --max-nudges-per-hour 20 \
  --max-total-nudges 200
```

## Status / Stop
```bash
bash scripts/rhea.sh autonudge status
bash scripts/rhea.sh autonudge stop
```

## Verify Audit Integrity
```bash
bash scripts/rhea.sh autonudge verify
# strict mode (fails on any legacy unchained prefix)
bash scripts/rhea.sh autonudge verify --strict
```

## Rollback
- Stop daemon: `bash scripts/rhea.sh autonudge stop`
- Remove runtime state: `rm -rf .rhea/autonudge`
- Keep audit log by default; if needed, archive `.entire/logs/autonudge.jsonl`.
