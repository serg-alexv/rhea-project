#!/usr/bin/env bash
# testflight.sh — Archive + Export + Upload to TestFlight
# Usage: bash scripts/testflight.sh [--upload]
#   Without --upload: archive + export only (open in Xcode Organizer)
#   With --upload: archive + upload directly to App Store Connect via xcodebuild

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
IOS_DIR="$PROJECT_ROOT/ios/RheaApp"
BUILD_DIR="$IOS_DIR/build"
ARCHIVE_PATH="$BUILD_DIR/RheaApp.xcarchive"
EXPORT_PATH="$BUILD_DIR/export"
UPLOAD_PATH="$BUILD_DIR/upload"
EXPORT_OPTIONS="$IOS_DIR/ExportOptions.plist"
UPLOAD_OPTIONS="$IOS_DIR/UploadOptions.plist"
TEAM_ID="398XACWZ7G"

# --- Colors ---
GREEN='\033[0;32m'
AMBER='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[testflight]${NC} $*"; }
warn() { echo -e "${AMBER}[testflight]${NC} $*"; }
err() { echo -e "${RED}[testflight]${NC} $*" >&2; }

# --- Auto-increment build number + sync marketing version ---
bump_build() {
    local yml="$IOS_DIR/project.yml"
    local current
    current=$(grep "CURRENT_PROJECT_VERSION" "$yml" | head -1 | sed 's/.*: *"\{0,1\}\([0-9]*\)"\{0,1\}/\1/')
    local next=$((current + 1))
    sed -i '' "s/CURRENT_PROJECT_VERSION: .*/CURRENT_PROJECT_VERSION: \"$next\"/" "$yml"
    sed -i '' "s/MARKETING_VERSION: .*/MARKETING_VERSION: \"1.0.$next\"/" "$yml"
    log "Build number: $current → $next (v1.0.$next)" >&2
    echo "$next"
}

# --- Step 1: Bump build number (BEFORE xcodegen so it bakes into xcodeproj) ---
cd "$IOS_DIR"
BUILD_NUM=$(bump_build)

# --- Step 2: Regenerate Xcode project (now reads bumped version) ---
log "Regenerating Xcode project..."
xcodegen generate 2>&1 | grep -v "^$"

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

# --- Step 4: Upload or Export ---
if [[ "${1:-}" == "--upload" ]]; then
    # Direct upload via xcodebuild (uses Xcode's stored Apple ID credentials)
    log "Uploading to App Store Connect..."
    rm -rf "$UPLOAD_PATH"
    xcodebuild -exportArchive \
        -archivePath "$ARCHIVE_PATH" \
        -exportPath "$UPLOAD_PATH" \
        -exportOptionsPlist "$UPLOAD_OPTIONS" \
        -allowProvisioningUpdates \
        2>&1 | grep -E "(Progress|Upload|EXPORT|error:)" || true

    if [ $? -eq 0 ]; then
        log "Upload complete! Check App Store Connect → TestFlight for processing status."
    else
        err "Upload failed. Opening Organizer as fallback..."
        open "$ARCHIVE_PATH"
    fi
else
    # Export IPA locally
    log "Exporting IPA..."
    rm -rf "$EXPORT_PATH"
    xcodebuild -exportArchive \
        -archivePath "$ARCHIVE_PATH" \
        -exportPath "$EXPORT_PATH" \
        -exportOptionsPlist "$EXPORT_OPTIONS" \
        -allowProvisioningUpdates \
        2>&1 | grep -E "(EXPORT|error:)" || true

    IPA_PATH="$EXPORT_PATH/RheaApp.ipa"
    if [ -f "$IPA_PATH" ]; then
        log "IPA exported: $IPA_PATH ($(du -h "$IPA_PATH" | cut -f1))"
    else
        warn "Export failed. Opening Organizer..."
    fi
    open "$ARCHIVE_PATH"
fi

log "Done. Build #$BUILD_NUM"
