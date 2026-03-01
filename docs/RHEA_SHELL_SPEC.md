# Rhea Shell CLI Specification

Version: 1.0.0 | Date: 2026-03-01 | Author: Rex (Opus 4.6)
Requested by: Orion (RELAY_20260228_220631)

---

## 1. Architecture

```
User
  |
  v
rhea.sh (bash dispatcher, v2.1)          <-- unified entry point
  |
  +-- scripts/rhea/*.sh                   <-- daemon wrappers (bash)
  +-- scripts/rhea_*.py                   <-- Python subsystems
  +-- src/*.py                            <-- core modules (bridge, governor, queue)
  |
  v
rhea_shell.py (interactive REPL)          <-- "commander>" prompt
  |
  v
cc (Tauri launcher)                       <-- desktop GUI (rhea-atlas)
```

Entry points:
- `bash scripts/rhea.sh <command>` -- canonical CLI
- `python3 scripts/rhea_shell.py` -- interactive REPL (`commander>` prompt)
- `python3 scripts/rhea_shell.py -c "command"` -- one-shot REPL command
- `./cc [dev|build|run]` -- Tauri desktop GUI launcher

---

## 2. Existing Commands (Inventory)

### 2.1 Infrastructure (rhea.sh)

| Command | Backend | What it does |
|---------|---------|--------------|
| `bootstrap` | `scripts/rhea/bootstrap.sh` | Normalize repo structure, import nested docs |
| `check` | `scripts/rhea/check.sh` | Invariant checks: .venv not tracked, .env not tracked, state.md < 2048B |
| `memory snapshot [LABEL]` | `scripts/rhea/memory.sh` | Create Entire.io state snapshot |
| `memory log "msg"` | `scripts/rhea/memory.sh` | Append to ops.jsonl |

### 2.2 Agent Operations (rhea.sh)

| Command | Backend | What it does |
|---------|---------|--------------|
| `status` | `rhea_orchestrate.py status` | Agent registry + snapshot inventory + docs listing |
| `flow` | `rhea_orchestrate.py flow` | Run multi-agent standard delegation flow |
| `workflows list\|run\|latest` | `rhea_flow.py` | OpenClaw-style flow runner (flow specs, execution, history) |
| `shell` / `commander` | `rhea_shell.py` | Interactive REPL with subcommands |
| `tribunal <claim>` | `rhea_bridge.py tribunal` | Execute multi-model consensus tribunal |
| `self-call <cmd>` | `scripts/rhea/self_call.py` | Controlled long-task loop (start/step/status/guard/stop/autonext) |
| `family <cmd>` | `rhea_family.py` | Family context fanout (send/status/tail/wait) |
| `patrol` | `dual_patrol.py` | Two-unit mutual ping/ack patrol loop |
| `flow-guard` | `flow_guard.py` | Continuity checks from bridge logs |
| `axiom <cmd>` | `axiom_contract.py` | Executable axiom contracts |

### 2.3 Daemons (rhea.sh)

All daemons follow the pattern: `start [--interval N] | stop | status | once | tail [N] | logs [N]`

| Command | Backend | Default Interval | Purpose |
|---------|---------|-----------------|---------|
| `radio` | `scripts/rhea/radio.sh` -> `rhea_radio.py` | 2s | Unified agent signal stream + notifications |
| `ndi` | `scripts/rhea/ndi.sh` -> `ndi_watchdog.py` | 6s | NDI/screen-capture watchdog |
| `queue` | `scripts/rhea/queue_guard.sh` -> `rhea_queue_guard.py` | 30s | Queue/log overflow guard + compact |
| `flow-up` | `scripts/rhea/flow_up.sh` -> `flow_up_guard.py` | 20s | Keep system flowing (wake/claim/stale alarm) |
| `gemini` | `scripts/rhea/gemini.sh` -> `gemini_guard.py` | 45s | Gemini presence guard (wake/boot/probe) |
| `autonudge` | `scripts/rhea/autonudge.sh` -> `autonudge_tmux.py` | 5s poll | Guarded tmux watchdog with optional Enter nudge |
| `maintainers` | `scripts/rhea/maintainers.sh` | -- | launchd control-plane for all 5 daemons (start/stop/restart/status/logs) |

### 2.4 Safety (rhea.sh)

| Command | What it does |
|---------|--------------|
| `stop` | Create `STOP` sentinel file. All daemons exit on next poll. |
| `pause` | Create `PAUSE` sentinel file. All loops idle without exiting. |
| `resume` | Remove both `STOP` and `PAUSE` sentinels. |
| `audit` | Verify pager audit ledger + show recent audit reports. |

### 2.5 Bridge Commands (src/rhea_bridge.py)

| Command | Purpose |
|---------|---------|
| `status` | Provider/key availability (JSON) |
| `tiers` | Tier configuration and model availability (JSON) |
| `profile` | Show active execution profile |
| `profile set <name>` | Set profile: `safe_cheap`, `balanced`, `deep` |
| `ask <provider/model> <prompt>` | Direct model query |
| `ask-default <prompt>` | Query via cheap tier |
| `ask-tier <tier> <prompt>` | Query via explicit tier |
| `tribunal <prompt> [--k N] [--mode local\|chairman]` | Multi-model consensus |
| `tribunal-ice <prompt> [--k N] [--rounds N]` | Iterative Convergence Estimation |
| `live-test` | Probe all providers with real API calls |
| `send-chronos <sender> <receiver> <task_id> <type> <priority> <json>` | Chronos protocol message |
| `daily-summary [YYYY-MM-DD]` | Bridge call log summary |
| `autoplan-test <prompt> <response>` | Test auto-plan extraction |

### 2.6 Governor Commands (src/token_governor.py)

| Command | Purpose |
|---------|---------|
| `python3 src/token_governor.py` | All agents dashboard (pace dots, T_day, billing, mode, gap) |
| `python3 src/token_governor.py <agent>` | Single agent enforce + detailed JSON |

### 2.7 Task Queue Commands (src/task_queue.py)

| Command | Purpose |
|---------|---------|
| `summary` | Queue health: counts, priority breakdown, stale tasks |
| `list [status]` | List tasks with optional status filter |
| `add <title>` | Add new P1 task |
| `claim <agent>` | Claim highest-priority open task for agent |
| `done <task_id> [result]` | Mark task complete |
| `seed` | Import tasks from TODO.md |

### 2.8 Credential Management (scripts/rhea/rotate_key.sh)

| Command | Purpose |
|---------|---------|
| `paste <provider>` | Clipboard -> .env (zero shell exposure) |
| `create gemini` | Auto-create Gemini key via gcloud |
| `audit` | Scan git + shell history for exposed keys |
| `test` | Test all keys via bridge status |
| `usage [openai]` | Show API usage and costs |
| `wipe` | Clean clipboard + history + temp files |

### 2.9 Support Scripts

| Script | Purpose |
|--------|---------|
| `rhea_commit.sh -m "msg"` | Git commit with native hooks, lease fencing, D-metric check, snapshot (ADR-013) |
| `rhea_autosave.sh [snapshot\|push\|full]` | Auto-save: snapshot + commit + push |
| `rhea_watch.sh` | 1-minute auto-snapshot cycle (daemon) |
| `rhea_pulse.sh` | Human rhythm keeper (water, food, rest notifications) |
| `rhea_swarm.sh` | Agent process manager + tmux multiplexer |
| `rhea_heartbeat.py [--daemon] [--json]` | Health monitoring (5 checks, 30min interval) |
| `rhea_executor.py [--daemon] [--agent NAME]` | Autonomous task execution engine |
| `rhea_query_persist.sh "summary"` | Per-query memory persistence (ADR-014) |
| `rhea_orchestrate.py genesis\|status\|flow\|delegate\|snapshot` | Multi-agent orchestration (8 agents, Chronos Protocol v3) |

### 2.10 Interactive Shell (rhea_shell.py) — Current Commands

```
commander> status          # orchestrate status
commander> radio <cmd>     # radio daemon control
commander> ndi <cmd>       # ndi daemon control
commander> continuity      # brain portability capsules
commander> family <cmd>    # family context fanout
commander> workflows <cmd> # OpenClaw flow runner
commander> axiom <cmd>     # axiom contracts
commander> rex-reqs        # send Orion's CLI reqs to Rex (one-shot)
commander> help
commander> exit
```

---

## 3. Missing Commands (Must-Add)

### 3.1 Critical Gaps

| Command | Reason | Priority |
|---------|--------|----------|
| `governor [agent\|all]` | No CLI path to governor from rhea.sh | P0 |
| `tasks <summary\|list\|add\|claim\|done>` | No CLI path to task_queue from rhea.sh | P0 |
| `bridge <status\|tiers\|profile\|live-test>` | Bridge only accessible via `python3 src/...` | P0 |
| `heartbeat [--json]` | No CLI path from rhea.sh | P1 |
| `keys <paste\|audit\|test\|wipe>` | `rotate_key.sh` not in rhea.sh dispatch | P1 |
| `commit -m "msg"` | rhea_commit.sh not in rhea.sh dispatch | P1 |
| `push` | No shorthand for autosave push | P1 |
| `swarm <start\|stop\|status\|attach>` | Not in rhea.sh dispatch | P2 |
| `logs <daemon>` | Unified log viewer across all daemons | P2 |
| `doctor` | Combined health check: invariants + heartbeat + governor + bridge status | P2 |

### 3.2 Shell (rhea_shell.py) Gaps

The interactive shell is missing most commands. It should mirror `rhea.sh` fully:
- `governor`, `tasks`, `bridge`, `heartbeat`, `keys`, `commit`, `push`, `check`, `doctor`

---

## 4. Status Panels

### 4.1 System Dashboard (`doctor` / combined status)

Aggregates data from 5 sources:

| Panel | Source | Data |
|-------|--------|------|
| **Invariants** | `check.sh` | .venv tracked?, .env tracked?, state.md size |
| **Governor** | `token_governor.py all` | Per-agent: pace (green/yellow/red), T_day, $/day, mode, floor_gap |
| **Bridge** | `rhea_bridge.py status` | Per-provider: key present?, working?, model count |
| **Tasks** | `task_queue.py summary` | open/claimed/done/blocked counts, P0-P3 breakdown, stale list |
| **Daemons** | `maintainers.sh status` | Per-daemon: running/stopped, PID, launchd state |

### 4.2 Heartbeat Panel (5 checks)

| Check | What | P0 Threshold | P1 Threshold |
|-------|------|-------------|-------------|
| `state_md` | File exists and < 2048B | Missing or oversized | -- |
| `git_push` | Time since last push | > 60min | > 30min |
| `invariants` | `check.sh` exit code | Non-zero | -- |
| `inbox` | Unread relay messages | -- | Oldest > 1hr |
| `api` | Tribunal API at :8400 | -- | Unreachable |

### 4.3 Governor Panel (per agent)

| Field | Source |
|-------|--------|
| `pace` | green/yellow/red (based on T_day trajectory) |
| `T_day` | Tokens used today |
| `dollar_day` | USD spent today (API agents) |
| `budget_cap` | Max USD/day |
| `billing_mode` | subscription or api |
| `mode` | normal / compact / idle |
| `floor_gap` | Distance from minimum daily trajectory |
| `forecast` | Projected EOD token usage |

---

## 5. Safety Rails

### 5.1 Sentinel System

| File | Effect | Created by | Cleared by |
|------|--------|-----------|------------|
| `STOP` | All daemons exit on next poll | `rhea.sh stop` | `rhea.sh resume` |
| `PAUSE` | All daemons idle without exiting | `rhea.sh pause` | `rhea.sh resume` |

Every daemon checks both files on each loop iteration.

### 5.2 Credential Safety

- Keys NEVER appear in CLI args, shell history, or process list (`ps`)
- `rotate_key.sh paste` reads from clipboard via temp file, then clears clipboard
- `rotate_key.sh audit` scans git HEAD, git history (50 commits), zsh history, bash history
- `rotate_key.sh wipe` cleans clipboard + history + temp files
- `.env` is in `.gitignore`; `check.sh` fails if `.env` is tracked
- `rhea_bridge.py` redacts 7 secret patterns from all log output

### 5.3 Budget Guardrails

- Governor upper rail: don't exceed daily USD cap (API agents)
- Governor lower rail: T_day = 0 is HARD FAIL (no idle agents)
- Governor floor trajectory: time-weighted minimum token curve
- Below floor -> auto-transition to compact recovery mode
- Subscription agents (rex): upper rail disabled, floor only

### 5.4 Commit Safety

- `rhea_commit.sh` enforces QWRR lease fencing (no zombie effects)
- Checkpoint trailer injected into every commit (`Rhea-Checkpoint: <id>`)
- D-metric check post-commit (warns if threshold exceeded)
- `.venv` and `.env` tracked-in-git checks run before commit

### 5.5 Daemon Safety

- Stale PID cleanup on every start/stop/status call
- Graceful shutdown with 5x 200ms retry before SIGKILL
- launchd KeepAlive + RunAtLoad for persistent daemons
- Autonudge: cooldown (45s), per-hour cap (20), max-total cap, command allowlist regex
- Autonudge audit chain: SHA-256 hash-chained JSONL (tamper-evident)
- `verify_jsonl_chain.py` validates chain integrity

### 5.6 Task Queue Safety

- File locking (`fcntl.LOCK_EX/LOCK_SH`) on state.json
- Append-only queue log (`queue.jsonl`) for audit trail
- Stale task detection (claimed but no progress > N hours)
- `release_stale(hours)` returns stale tasks to open queue
- Dependency-aware claiming: tasks with unmet deps are skipped

---

## 6. Ack Policy

### 6.1 Family Fanout

- `rhea_family.py send` -> broadcasts to all targets, returns `family_id`
- `rhea_family.py status [family_id]` -> per-target delivery + ack status
- `rhea_family.py wait [family_id] --timeout N` -> poll until all acked or timeout
- Acks stored in `relay_acks.jsonl`
- Default targets: REX, ORION, HYPERION
- Default TTL: 86400s (24h)
- Default priority: P1

### 6.2 Relay System

- Outbox files: `<AGENT>_<YYYYMMDD>_<HHMMSS>_<topic>.md`
- Relay cycle (`rhea_swarm.sh relay`): outbox -> inbox as `RELAY_<ts>_<FROM>_to_<TO>.md`
- No explicit ack for relay (fire-and-forget, file-based)

### 6.3 Self-Call Loop

- Budget gates: time and token limits, enforced by `guard` subcommand
- Inactivity gate: no step within `interval_minutes` -> fail
- Step modes: observe -> plan -> execute -> verify -> checkpoint (cyclic)
- Result modes: ok, handoff, abort

### 6.4 Daemon Commands

- All daemon commands are synchronous and return immediately
- `start` is idempotent (prints "already running" if duplicate)
- `stop` is graceful (SIGTERM -> wait -> SIGKILL)
- `once` runs one cycle foreground (for testing)
- `status` shows running/stopped + backend status

---

## 7. Output Format

### 7.1 Conventions

| Context | Format |
|---------|--------|
| Python subsystems (bridge, governor, queue, family, flow) | **JSON** (machine-readable) |
| Bash wrappers (check, bootstrap, commit, autosave) | **Human text** with color codes |
| Daemon status | **Human text** (one-line per daemon) |
| `--json` flag (heartbeat, axiom) | **JSON** (opt-in machine-readable) |
| Errors | stderr, prefixed with `FAIL:` or `[rhea-commit]` |

### 7.2 JSON Output Standard

All JSON commands should follow:
```json
{
  "status": "ok|error|timeout|idle",
  "ts": "2026-03-01T12:00:00Z",
  ...domain-specific fields...
}
```

### 7.3 Table Format (governor dashboard)

```
  <pace_dot> <AGENT>  T=<tokens> tok  <billing>  mode:<mode>  gap:<gap>
```

### 7.4 Compact Human Format

For quick status checks, one line per entity:
```
  [+] check_name
  [-] check_name -- failure reason
```

---

## 8. Proposed rhea.sh Additions

```bash
# Add to rhea.sh case statement:
governor)    python3 src/token_governor.py "$@" ;;
tasks)       python3 src/task_queue.py "$@" ;;
bridge)      python3 src/rhea_bridge.py "$@" ;;
heartbeat)   python3 scripts/rhea_heartbeat.py "$@" ;;
keys)        bash scripts/rhea/rotate_key.sh "$@" ;;
commit)      bash scripts/rhea_commit.sh "$@" ;;
push)        bash scripts/rhea_autosave.sh push ;;
save)        bash scripts/rhea_autosave.sh full "$@" ;;
swarm)       bash scripts/rhea_swarm.sh "$@" ;;
doctor)      # Combined: check + heartbeat + governor all + bridge status + maintainers status
```

---

## 9. Implementation Priority

1. **P0**: Wire `governor`, `tasks`, `bridge` into `rhea.sh` (3 lines each)
2. **P0**: Mirror in `rhea_shell.py` REPL
3. **P1**: Add `keys`, `commit`, `push`, `heartbeat` to both
4. **P1**: Build `doctor` composite command
5. **P2**: Add `swarm`, unified `logs` viewer
6. **P2**: Add `--json` flag to all bash commands that lack it
7. **P3**: Tab completion for interactive shell
8. **P3**: `rhea.sh init` -- first-run wizard (check.sh + bootstrap + keys audit + maintainers start)
