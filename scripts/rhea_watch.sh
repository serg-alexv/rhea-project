#!/usr/bin/env bash
# rhea_watch.sh — entire.io 1-minute save cycle
# Resilient: no set -e, tolerates git lock files, logs all errors

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

INTERVAL="${ENTIRE_SAVE_INTERVAL_SEC:-60}"
LOG=".entire/logs/watch.log"
OPS=".entire/logs/ops.jsonl"
mkdir -p .entire/logs .entire/snapshots

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" >> "$LOG"; }

log "rhea_watch started (interval=${INTERVAL}s, pid=$$)"

while true; do
    sleep "$INTERVAL" || break

    GIT_REV=$(git rev-parse --short HEAD 2>/dev/null || echo "no-git")
    DIRTY=$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ')
    TS=$(date -u +%Y-%m-%dT%H-%M-%SZ)
    SNAP_FILE=".entire/snapshots/AUTO-${TS}-${GIT_REV}.json"

    # Build snapshot with inline python — tolerant
    python3 -c "
import json, glob, datetime
snap = {
    'type': 'auto',
    'ts': datetime.datetime.utcnow().isoformat() + 'Z',
    'git_rev': '${GIT_REV}',
    'dirty_files': int('${DIRTY}' or '0'),
    'docs': sorted(glob.glob('docs/*.md')),
    'src': sorted(glob.glob('src/*.py')),
    'scripts': sorted(glob.glob('scripts/*.sh')),
    'config': sorted(glob.glob('.rhea/*.json')),
}
with open('${SNAP_FILE}', 'w') as f:
    json.dump(snap, f, indent=2)
" 2>>"$LOG" && log "snapshot → ${SNAP_FILE} (dirty=${DIRTY})" || log "WARN snapshot failed"

    # Append ops event
    python3 -c "
import json, datetime
evt = {
    'ts': datetime.datetime.utcnow().isoformat() + 'Z',
    'op': 'auto_snapshot',
    'snapshot': '${SNAP_FILE}',
    'dirty': int('${DIRTY}' or '0'),
    'git_rev': '${GIT_REV}'
}
with open('${OPS}', 'a') as f:
    f.write(json.dumps(evt) + '\n')
" 2>>"$LOG" || log "WARN ops append failed"

    # Prune: keep last 60 AUTO snapshots
    ls -1t .entire/snapshots/AUTO-*.json 2>/dev/null | tail -n +61 | xargs rm -f 2>/dev/null || true

    log "cycle done"
done

log "rhea_watch exited"
