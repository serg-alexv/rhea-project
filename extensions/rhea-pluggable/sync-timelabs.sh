#!/bin/bash
# sync-timelabs.sh — clone and link a timelabs repo into Rhea

set -euo pipefail

REPO_NAME=${1:?Specify timelabs repo name (e.g. rhea-ios)}
BASE_DIR=$(pwd)
EXT_DIR="$BASE_DIR/extensions/$REPO_NAME"

if [[ -d "$EXT_DIR" ]]; then
  echo "Extension $REPO_NAME already exists. Pulling latest changes..."
  git -C "$EXT_DIR" pull
else
  echo "Cloning timelabs/$REPO_NAME..."
  git clone "https://github.com/timelabs/$REPO_NAME" "$EXT_DIR"
fi

echo "Registering repo in extensions registry..."
REG_FILE="$BASE_DIR/extensions/registry.json"
mkdir -p "$(dirname "$REG_FILE")"
cat <<EOF > "$REG_FILE"
{
  "last_synced": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "repo": "$REPO_NAME",
  "path": "$EXT_DIR"
}
EOF

echo "Linking entrypoints for $REPO_NAME..."
# Example: add to scripts/rhea.sh `extensions/$REPO_NAME/entry.sh`

echo "Clone registered in extensions/registry.json. Update scripts/rhea.sh or deploy pipeline as needed."
