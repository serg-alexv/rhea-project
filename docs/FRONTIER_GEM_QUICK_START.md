# Frontier Gem — Quick Start Guide

## One-Command Installation

```bash
bash scripts/setup_frontier_gem.sh
```

This script:
1. ✅ Builds the frontier-gem binary
2. ✅ Installs to `/usr/local/bin/`
3. ✅ Creates native messaging host manifest
4. ✅ Prompts for extension ID and updates manifest
5. ✅ Provides next steps

## Manual Installation (if needed)

### 1. Build & Install Binary

```bash
cd frontier-gem
cargo build --release
sudo cp target/release/frontier-gem /usr/local/bin/
sudo codesign --force -s - /usr/local/bin/frontier-gem
```

### 2. Create Native Messaging Manifest

```bash
mkdir -p ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts

cat > ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts/com.rhea.frontier_gem.json << 'EOF'
{
  "name": "com.rhea.frontier_gem",
  "description": "Rhea Frontier Gem - native messaging host",
  "path": "/usr/local/bin/frontier-gem",
  "type": "stdio",
  "allowed_extensions": ["chrome-extension://YOUR_EXTENSION_ID_HERE"]
}
EOF
```

### 3. Load Extension

1. Open `chrome://extensions`
2. Enable "Developer mode" (top-right toggle)
3. Click "Load unpacked"
4. Select `frontier-gem/gem-extension/`
5. Copy the Extension ID

### 4. Update Manifest with Extension ID

```bash
MANIFEST=~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts/com.rhea.frontier_gem.json
sed -i '' 's/YOUR_EXTENSION_ID_HERE/chrome-extension:\/\/YOUR_ID_HERE/' "$MANIFEST"
```

## Usage

### Start the Daemon

```bash
frontier-gem daemon
```

Output:
```
📡 Gem Daemon Starting...
🌐 HTTP Server Online at 127.0.0.1:3456
🚌 Bus Online at TCP 127.0.0.1:4444
💓 mDNS Broadcasting as GemNode.gem.local
```

### Test HTTP Endpoint

```bash
# POST with JSON body
curl -X POST http://localhost:3456/api/test \
  -H "Content-Type: application/json" \
  -d '{"event": "test", "timestamp": 1709707289}'

# Response:
# {"status": "ok", "path": "/api/test", "timestamp": 1709707289}
```

### Test CORS Headers

```bash
curl -X OPTIONS http://localhost:3456/api/test -v

# Look for:
# Access-Control-Allow-Origin: *
# Access-Control-Allow-Methods: GET, POST, OPTIONS
```

### Check Extension Logs

1. Open `chrome://extensions`
2. Click "Service Workers" next to Gem Observer
3. Check console for:
   - `🔌 Attempting native connection...` (startup)
   - `💓 Heartbeat sent @ 2:45 PM` (every 5 minutes)
   - `😴 Service Worker idle` (after 30 minutes of inactivity)

## Configuration

### Heartbeat Interval

Edit `frontier-gem/gem-extension/background.js`:

```javascript
const HEARTBEAT_INTERVAL = 5 * 60 * 1000;  // Change this value (ms)
```

### Idle Timeout

```javascript
const IDLE_TIMEOUT = 30 * 60 * 1000;  // Change this value (ms)
```

### HTTP Server Port

Edit `frontier-gem/src/main.rs`, find `run_http_server()`:

```rust
let listener = TcpListener::bind("127.0.0.1:3456").await?;  // Change port here
```

Then rebuild:
```bash
cargo build --release
```

## Troubleshooting

### "Native host not found"

```bash
# Verify binary exists
ls -la /usr/local/bin/frontier-gem

# Verify manifest location
ls -la ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts/

# Restart Chrome completely (all windows)
```

### HTTP Server Returns 404

```bash
# Verify daemon is running
ps aux | grep frontier-gem

# Check if port is listening
lsof -i :3456

# Start daemon
frontier-gem daemon
```

### Heartbeat Not Showing

```bash
# Open Chrome DevTools for extension
chrome://extensions → Service Workers → Click "Gem Observer"

# Check console for errors
# Heartbeat sends every 5 minutes (look for 💓 emoji)
```

### CORS Headers Missing

```bash
# Verify response includes headers
curl -X OPTIONS http://localhost:3456/ -i | grep Access-Control

# All responses should include:
# Access-Control-Allow-Origin: *
```

## Files Overview

```
frontier-gem/
├── src/main.rs                          # HTTP server + TCP bus + mDNS
├── gem-extension/
│   ├── manifest.json                    # Chrome extension config (v3)
│   └── background.js                    # Heartbeat + native messaging
└── Support/Google/Chrome/NativeMessagingHosts/
    └── com.rhea.frontier_gem.json       # Native host registration
```

## Next Steps

1. **Monitor Real-Time Events**
   ```bash
   tail -f /tmp/0.log  # Event log
   ```

2. **Send Custom Events**
   ```javascript
   // From extension
   port.postMessage({
       type: "custom_event",
       data: "your_data_here",
       timestamp: Date.now()
   });
   ```

3. **Extend HTTP API**
   - Add `/api/events` endpoint to retrieve history
   - Add `/api/health` for daemon status
   - Add `/api/stats` for metrics

## Full Documentation

See `docs/FRONTIER_GEM_SETUP.md` for comprehensive guide including:
- Architecture diagrams
- Security considerations
- Event flow documentation
- Development instructions
- Future enhancements

---

**Status:** ✅ Ready for Production  
**Last Updated:** 2026-03-06  
**Version:** 1.0
