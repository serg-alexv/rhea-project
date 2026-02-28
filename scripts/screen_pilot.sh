#!/bin/bash
# screen_pilot.sh — Remote screen automation via iPhone Mirroring
# Uses: screencapture + cliclick + Read (Claude analyzes screenshots)
#
# Usage:
#   ./screen_pilot.sh screenshot         → capture to /tmp/pilot_screen.png
#   ./screen_pilot.sh tap X Y            → click at screen coords (x, y)
#   ./screen_pilot.sh type "text"        → type text at cursor
#   ./screen_pilot.sh swipe X1 Y1 X2 Y2 → drag from (x1,y1) to (x2,y2)
#   ./screen_pilot.sh find "window name" → get window position

set -euo pipefail
SCREENSHOT_DIR="/tmp/pilot"
mkdir -p "$SCREENSHOT_DIR"

case "${1:-help}" in
  screenshot|ss)
    FILE="$SCREENSHOT_DIR/screen_$(date +%s).png"
    screencapture -x "$FILE"
    echo "$FILE"
    ;;

  tap|click)
    X="${2:?'X coordinate required'}"
    Y="${3:?'Y coordinate required'}"
    cliclick "c:$X,$Y"
    echo "Tapped at ($X, $Y)"
    ;;

  type)
    TEXT="${2:?'Text required'}"
    cliclick "t:$TEXT"
    echo "Typed: $TEXT"
    ;;

  swipe|drag)
    X1="${2:?}" Y1="${3:?}" X2="${4:?}" Y2="${5:?}"
    cliclick "dd:$X1,$Y1" "du:$X2,$Y2"
    echo "Swiped ($X1,$Y1) → ($X2,$Y2)"
    ;;

  find)
    WINDOW="${2:-iPhone Mirroring}"
    osascript -e "
      tell application \"System Events\"
        set targetProcess to first process whose name is \"$WINDOW\"
        set w to first window of targetProcess
        set {posX, posY} to position of w
        set {sizeW, sizeH} to size of w
        return \"x=\" & posX & \" y=\" & posY & \" w=\" & sizeW & \" h=\" & sizeH
      end tell
    " 2>&1
    ;;

  key)
    KEY="${2:?'Key required'}"
    cliclick "kp:$KEY"
    echo "Pressed: $KEY"
    ;;

  help|*)
    echo "screen_pilot.sh — Remote screen automation"
    echo "  screenshot    Capture screen to /tmp/pilot/"
    echo "  tap X Y       Click at coordinates"
    echo "  type TEXT      Type text"
    echo "  swipe X1 Y1 X2 Y2  Drag gesture"
    echo "  find [window] Get window position"
    echo "  key KEY        Press keyboard key"
    ;;
esac
