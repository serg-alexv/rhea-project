#!/usr/bin/env bash
# testflight.sh — Archive + Export + Upload to TestFlight
# Usage: bash scripts/testflight.sh [--upload]
#   Without --upload: archive + export only (open in Xcode Organizer)
#   With --upload: full pipeline to App Store Connect (requires API key)
#
# API Key setup (one time):
#   1. App Store Connect → Users → Keys → Generate API Key
#   2. Save .p8 file to ~/private/keys/AuthKey_XXXX.p8
#   3. Set env vars or edit below:
#      export ASC_KEY_ID="your-key-id"
#      export ASC_ISSUER_ID="your-issuer-id"
#      export ASC_KEY_PATH="~/private/keys/AuthKey_XXXX.p8"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
IOS_DIR="$PROJECT_ROOT/ios/RheaApp"
BUILD_DIR="$IOS_DIR/build"
ARCHIVE_PATH="$BUILD_DIR/RheaApp.xcarchive"
EXPORT_PATH="$BUILD_DIR/export"
EXPORT_OPTIONS="$IOS_DIR/ExportOptions.plist"
TEAM_ID="398XACWZ7G"

# --- Colors ---
GREEN='\033[0;32m'
AMBER='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[testflight]${NC} $*"; }
warn() { echo -e "${AMBER}[testflight]${NC} $*"; }
err() { echo -e "${RED}[testflight]${NC} $*" >&2; }

# --- Auto-increment build number ---
bump_build() {
    local yml="$IOS_DIR/project.yml"
    local current
    current=$(grep "CURRENT_PROJECT_VERSION" "$yml" | head -1 | sed 's/.*: *"\{0,1\}\([0-9]*\)"\{0,1\}/\1/')
    local next=$((current + 1))
    sed -i '' "s/CURRENT_PROJECT_VERSION: .*/CURRENT_PROJECT_VERSION: \"$next\"/" "$yml"
    log "Build number: $current → $next"
    echo "$next"
}

# --- Step 1: Regenerate Xcode project ---
log "Regenerating Xcode project..."
cd "$IOS_DIR"
xcodegen generate 2>&1 | grep -v "^$"

# --- Step 2: Bump build number ---
BUILD_NUM=$(bump_build)

# --- Step 3: Archive ---
log "Archiving (Release)..."
rm -rf "$ARCHIVE_PATH"
xcodebuild archive \
    -scheme RheaApp \
    -configuration Release \
    -archivePath "$ARCHIVE_PATH" \
    -derivedDataPath "$BUILD_DIR/DerivedData" \
    -destination "generic/platform=iOS" \
    -allowProvisioningUpdates \
    CODE_SIGN_STYLE=Automatic \
    DEVELOPMENT_TEAM="$TEAM_ID" \
    2>&1 | grep -E "(ARCHIVE|error:|warning:)" || true

if [ ! -d "$ARCHIVE_PATH" ]; then
    err "Archive FAILED. Check full output above."
    exit 1
fi
log "Archive succeeded: $ARCHIVE_PATH"

# --- Step 4: Export IPA ---
log "Exporting IPA..."
rm -rf "$EXPORT_PATH"
xcodebuild -exportArchive \
    -archivePath "$ARCHIVE_PATH" \
    -exportPath "$EXPORT_PATH" \
    -exportOptionsPlist "$EXPORT_OPTIONS" \
    -allowProvisioningUpdates \
    2>&1 | grep -E "(EXPORT|error:)" || true

IPA_PATH="$EXPORT_PATH/RheaApp.ipa"
if [ ! -f "$IPA_PATH" ]; then
    err "Export FAILED."
    exit 1
fi
log "IPA exported: $IPA_PATH ($(du -h "$IPA_PATH" | cut -f1))"

# --- Step 5: Upload or open Organizer ---
if [[ "${1:-}" == "--upload" ]]; then
    KEY_ID="${ASC_KEY_ID:-}"
    ISSUER_ID="${ASC_ISSUER_ID:-}"
    KEY_PATH="${ASC_KEY_PATH:-}"

    if [ -z "$KEY_ID" ] || [ -z "$ISSUER_ID" ] || [ -z "$KEY_PATH" ]; then
        warn "API key not configured. Set ASC_KEY_ID, ASC_ISSUER_ID, ASC_KEY_PATH env vars."
        warn "Opening Xcode Organizer instead — use Distribute App manually."
        open "$ARCHIVE_PATH"
        exit 0
    fi

    log "Uploading to App Store Connect..."
    xcrun altool --upload-app \
        -f "$IPA_PATH" \
        -t ios \
        --apiKey "$KEY_ID" \
        --apiIssuer "$ISSUER_ID" \
        2>&1

    log "Upload complete! Check App Store Connect → TestFlight for processing status."
else
    log "Opening Xcode Organizer (use --upload flag for automatic upload)..."
    open "$ARCHIVE_PATH"
fi

log "Done. Build #$BUILD_NUM"
