#!/bin/bash
set -e

echo "🚀 Starting Rhea CLI integration test..."

# Build server
echo "📦 Building server..."
cd /Users/sa/rh.1/rhea-session-server && cargo build --bin server --release 2>&1 | grep -E "(Compiling|Finished)" || true

# Start server in background
echo "🌟 Starting server..."
/Users/sa/rh.1/rhea-session-server/target/release/server &
SERVER_PID=$!
sleep 2

# Build CLI
echo "📦 Building CLI..."
cd /Users/sa/rh.1/rhea-cli && cargo build 2>&1 | grep -E "(Compiling|Finished)" || true

# Test help
echo ""
echo "✅ Testing CLI --help:"
./target/debug/rhea-cli --help | head -8

# Clean up
echo ""
echo "🧹 Cleanup..."
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

echo ""
echo "✨ CLI is ready! Run it with:"
echo "   /Users/sa/rh.1/rhea-session-server/target/release/server &"
echo "   /Users/sa/rh.1/rhea-cli/target/debug/rhea-cli"
