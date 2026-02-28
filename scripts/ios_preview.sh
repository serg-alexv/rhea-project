#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

atlas_url="${RHEA_ATLAS_URL:-http://localhost:3000}"
api_url="${RHEA_API_URL:-http://localhost:8400}"

check_url() {
  local name="$1" url="$2"
  if curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then
    echo "[ok]   $name reachable: $url"
  else
    echo "[warn] $name not reachable: $url"
  fi
}

print_ip_hint() {
  local ip=""
  if command -v ipconfig >/dev/null 2>&1; then
    ip="$(ipconfig getifaddr en0 2>/dev/null || true)"
    if [ -z "$ip" ]; then
      ip="$(ipconfig getifaddr en1 2>/dev/null || true)"
    fi
  fi
  if [ -n "$ip" ]; then
    echo "[hint] Physical device URLs usually look like:"
    echo "       Atlas: http://$ip:3000"
    echo "       API:   http://$ip:8400"
  fi
}

case "${1:-open}" in
  status)
    check_url "Atlas" "$atlas_url"
    check_url "API" "$api_url/health"
    print_ip_hint
    ;;
  open)
    check_url "Atlas" "$atlas_url"
    check_url "API" "$api_url/health"
    print_ip_hint
    echo "[info] Opening SwiftPM iOS app in Xcode..."
    open "$ROOT/ios/RheaPreview.swiftpm"
    ;;
  *)
    echo "Usage: bash scripts/ios_preview.sh [open|status]"
    exit 1
    ;;
esac
