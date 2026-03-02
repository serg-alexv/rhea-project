#!/usr/bin/env bash
set -euo pipefail

DURATION_SEC="${1:-1800}"
OUT_DIR="${2:-diagnostics/screen-flicker-$(date -u +%Y%m%dT%H%M%SZ)}"

mkdir -p "$OUT_DIR"

LOGFILE="$OUT_DIR/logstream.log"
SAMPLE="$OUT_DIR/sampler.tsv"
META="$OUT_DIR/meta.txt"

cat >"$META" <<EOF
started_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
duration_sec=$DURATION_SEC
out_dir=$OUT_DIR
host=$(hostname)
user=$(whoami)
EOF

log stream --style compact --predicate '(process == "screencapture" OR process == "WindowServer" OR process CONTAINS[c] "newtek" OR process CONTAINS[c] "obs" OR process CONTAINS[c] "chromeremotedesktop" OR process CONTAINS[c] "displaylink" OR process CONTAINS[c] "camerahub" OR eventMessage CONTAINS[c] "ScreenCapture" OR eventMessage CONTAINS[c] "NDI")' >"$LOGFILE" 2>&1 &
LOG_PID=$!

cleanup() {
  kill "$LOG_PID" 2>/dev/null || true
  wait "$LOG_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

{
  printf "ts_utc\tndi_596x_listen\tndi_596x_established\ttracked_processes\n"
  end_ts=$((SECONDS + DURATION_SEC))
  while [ "$SECONDS" -lt "$end_ts" ]; do
    ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    listen_count="$(netstat -anv -p tcp 2>/dev/null | rg -c '\.5960|\.5961' || true)"
    estab_count="$(netstat -anv -p tcp 2>/dev/null | rg '\.5960|\.5961' | rg -vc 'LISTEN' || true)"
    tracked="$(ps ax -o pid=,comm= | rg -i 'NDI|newtek|obs|chromeremotedesktop|DisplayLink|CameraHub|screencapture|WindowServer|claude|terminal' | tr '\n' ';' | sed 's/[[:space:]]\\+/ /g' || true)"
    printf "%s\t%s\t%s\t%s\n" "$ts" "$listen_count" "$estab_count" "$tracked"
    sleep 1
  done
} >"$SAMPLE"

echo "trace_complete out_dir=$OUT_DIR"
