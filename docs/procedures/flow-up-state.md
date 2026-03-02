# Flow-Up State

Objective: keep system continuously in `flowing-up` mode.

## Runtime

`flow_up_guard` runs as launchd service:

- label: `com.rhea.flowup`
- command: `python3 scripts/flow_up_guard.py run --interval 20 --notify --echo --alarm-mode adaptive`

Unified control:

```bash
bash scripts/rhea.sh flow-up status
bash scripts/rhea.sh flow-up logs 80
bash scripts/rhea.sh flow-up tail 40
```

## Behavior

Per cycle, guard does:

1. revive expired core agents (`wake` + `boot`)
2. auto-claim open tasks with round-robin distribution
3. wake stale task owners
4. publish pulse to `opera/metrics/flow_up.json`

State labels:

- `flowing-up` (score >= 80)
- `recovering` (50..79)
- `stalled` (< 50)

## Empty-Flow Alarm

If active tasks are zero (`open + claimed == 0`), alarm triggers.

Mode `adaptive`:

- if audio is already loud and Music is not playing -> mute audio channel
- otherwise -> alarm ping + notification

Tune options (manual run):

```bash
python3 scripts/flow_up_guard.py once --echo --notify --alarm-mode adaptive --loud-threshold 70
python3 scripts/flow_up_guard.py once --echo --notify --alarm-mode mute
python3 scripts/flow_up_guard.py once --echo --notify --alarm-mode ping
```
