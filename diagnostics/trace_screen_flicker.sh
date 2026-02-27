#!/usr/bin/env bash
set -euo pipefail

OUTFILE="${1:-/Users/sa/rh.1/diagnostics/screen-flicker-live-$(date +%Y%m%d_%H%M%S).log}"
DURATION="${2:-180}"

PRED='(process == "replayd" AND (eventMessage CONTAINS "captureScreenshot" OR eventMessage CONTAINS "SCScreenShotSession" OR eventMessage CONTAINS "accepted client connection PID")) OR (process == "WindowServer" AND eventMessage CONTAINS "commitBrightness") OR process == "screencapture" OR process == "screencaptureui" OR process == "ScreenshotControls" OR (process == "runningboardd" AND eventMessage CONTAINS "anon<screencapture>")'

{
  echo "# trace start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "# duration_sec: $DURATION"
  echo "# predicate: $PRED"
} > "$OUTFILE"

/usr/bin/log stream --style compact --predicate "$PRED" >> "$OUTFILE" 2>&1 &
LOG_PID=$!

sleep "$DURATION"
kill "$LOG_PID" 2>/dev/null || true
wait "$LOG_PID" 2>/dev/null || true

echo "# trace end: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUTFILE"
echo "$OUTFILE"
