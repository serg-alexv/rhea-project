#!/bin/bash
# Frontier Gem Installation Script
# Installs native messaging host and Chrome extension

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GEM_DIR="$REPO_ROOT/frontier-gem"
MANIFEST_SOURCE="$GEM_DIR/Support/Google/Chrome/NativeMessagingHosts/com.rhea.frontier_gem.json"
MANIFEST_DEST="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"

echo "🎯 Frontier Gem Setup Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Step 1: Build frontier-gem binary
echo ""
echo "📦 Step 1: Building frontier-gem binary..."
cd "$GEM_DIR"
cargo build --release 2>&1 | tail -5
BINARY="$GEM_DIR/target/release/frontier-gem"

if [ ! -f "$BINARY" ]; then
    echo "❌ Build failed. Binary not found at $BINARY"
    exit 1
fi
echo "✅ Binary built successfully"

# Step 2: Install binary to /usr/local/bin
echo ""
echo "🔧 Step 2: Installing binary to /usr/local/bin..."
sudo cp "$BINARY" /usr/local/bin/frontier-gem
sudo chmod +x /usr/local/bin/frontier-gem

# Code sign the binary (macOS)
if command -v codesign &> /dev/null; then
    echo "   Signing binary..."
    sudo codesign --force -s - /usr/local/bin/frontier-gem 2>/dev/null || true
fi

which frontier-gem > /dev/null && echo "✅ Binary installed and in PATH"

# Step 3: Create native messaging manifest directory
echo ""
echo "📁 Step 3: Setting up native messaging host manifest..."
mkdir -p "$MANIFEST_DEST"
echo "   Created directory: $MANIFEST_DEST"

# Step 4: Copy manifest (user must update with extension ID)
if [ -f "$MANIFEST_SOURCE" ]; then
    cp "$MANIFEST_SOURCE" "$MANIFEST_DEST/com.rhea.frontier_gem.json"
    echo "✅ Manifest installed"
    echo ""
    echo "⚠️  IMPORTANT: Update the manifest with your extension ID:"
    echo "   File: $MANIFEST_DEST/com.rhea.frontier_gem.json"
    echo ""
    echo "   1. Open chrome://extensions"
    echo "   2. Load 'gem-extension' unpacked"
    echo "   3. Copy the extension ID"
    echo "   4. Edit manifest file and replace [EXTENSION_ID_HERE] with your ID"
else
    echo "❌ Manifest source not found: $MANIFEST_SOURCE"
    exit 1
fi

# Step 5: Display extension installation instructions
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔌 Extension Installation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Open Chrome and go to chrome://extensions"
echo "2. Enable 'Developer mode' (toggle in top-right)"
echo "3. Click 'Load unpacked'"
echo "4. Select: $GEM_DIR/gem-extension"
echo "5. Copy the Extension ID (shown after loading)"
echo ""

# Step 6: Prompt for extension ID
echo ""
read -p "Enter the Extension ID from chrome://extensions: " EXT_ID

if [ -z "$EXT_ID" ]; then
    echo "❌ Extension ID is required. Skipping manifest update."
    echo "   You can update it manually later:"
    echo "   $MANIFEST_DEST/com.rhea.frontier_gem.json"
else
    # Update manifest with extension ID
    sed -i '' "s|\[EXTENSION_ID_HERE\]|$EXT_ID|g" "$MANIFEST_DEST/com.rhea.frontier_gem.json"
    echo "✅ Manifest updated with extension ID: $EXT_ID"
fi

# Step 7: Verify installation
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check binary
if frontier-gem --version > /dev/null 2>&1; then
    echo "✅ Binary is installed and accessible"
else
    echo "⚠️  Binary not in PATH. Check /usr/local/bin/frontier-gem"
fi

# Check manifest
if [ -f "$MANIFEST_DEST/com.rhea.frontier_gem.json" ]; then
    echo "✅ Native messaging manifest installed"
    if grep -q "EXTENSION_ID_HERE" "$MANIFEST_DEST/com.rhea.frontier_gem.json"; then
        echo "⚠️  Manifest still contains [EXTENSION_ID_HERE]. Update with your extension ID."
    else
        echo "✅ Manifest contains extension ID"
    fi
else
    echo "❌ Native messaging manifest not found"
fi

# Check extension
if [ -d "$GEM_DIR/gem-extension" ]; then
    echo "✅ Extension source directory exists"
else
    echo "❌ Extension directory not found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Next Steps"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Restart Chrome completely (close all windows)"
echo "2. Start the daemon:"
echo "   frontier-gem daemon"
echo ""
echo "3. Open Chrome DevTools (Ctrl+Shift+J) to view extension logs"
echo "   Look for: '🔌 Attempting native connection...'"
echo ""
echo "4. Test HTTP endpoint:"
echo "   curl -X POST http://localhost:3456/api/test \\\\
echo "     -H 'Content-Type: application/json' \\\\
echo "     -d '{\"test\": \"data\"}'"
echo ""
echo "5. Verify heartbeat (every 5 minutes):"
echo "   Check extension console for: '💓 Heartbeat sent @ ...'"
echo ""
echo "✅ Setup complete!"
