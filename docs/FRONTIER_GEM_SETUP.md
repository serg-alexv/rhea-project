# Frontier Gem — Chrome Extension Native Messaging Bridge

## Overview

Frontier Gem is a native messaging bridge that connects a Chrome extension with a local HTTP/native daemon, enabling:
- QR scanning and observation from the browser
- Native application communication via stdio
- HTTP API endpoints with CORS support
- 5-minute heartbeat signals for connectivity monitoring
- Automatic idle detection after 30 minutes

## Architecture

```
Chrome Extension (background.js)
  │
  ├─ chrome.runtime.connectNative('com.rhea.frontier_gem')
  │
  └─ Native Messaging Host (frontier-gem binary)
       │
       ├─ TCP Bus (localhost:4444)
       │  └─ Event broadcast to mDNS nodes
       │
       └─ HTTP Server (localhost:3456)
          └─ CORS-enabled REST endpoints
```

## Components

### 1. Rust Backend (frontier-gem/src/main.rs)

**HTTP Server (Port 3456)**
- Listens on `127.0.0.1:3456`
- Responds to GET, POST, OPTIONS requests
- CORS headers: `Access-Control-Allow-Origin: *`
- CORS methods: `GET, POST, OPTIONS`
- Accepts JSON payloads and appends to event log

**TCP Bus (Port 4444)**
- Central message distribution
- Connects native messenger proxy
- Broadcasts events from all sources
- mDNS discovery integration

**mDNS Service Discovery**
- Registers as `_frontier-gem._tcp.local`
- Auto-discovery of peer frontier-gem nodes
- Service info: `GemNode.gem.local:4444`

### 2. Chrome Extension

**manifest.json (v3)**
```json
{
  "permissions": ["activeTab", "tabs", "nativeMessaging", "webRequest"],
  "host_permissions": ["<all_urls>"],
  "background": {"service_worker": "background.js"}
}
```

**background.js Features**
- Native connection: `chrome.runtime.connectNative('com.rhea.frontier_gem')`
- 5-minute heartbeat signals
- 30-minute idle timeout detection
- Tab activity tracking
- Auto-reconnect on disconnect

## Installation

### Step 1: Install Native Messaging Host

```bash
# Build frontier-gem
cd frontier-gem
cargo build --release
./target/release/frontier-gem install

# Or manually:
sudo cp target/release/frontier-gem /usr/local/bin/
sudo codesign --force -s - /usr/local/bin/frontier-gem
```

### Step 2: Install Native Messaging Manifest

```bash
mkdir -p ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts

cp Support/Google/Chrome/NativeMessagingHosts/com.rhea.frontier_gem.json \
   ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts/
```

### Step 3: Get Extension ID

1. Open `chrome://extensions`
2. Enable "Developer mode"
3. Load `gem-extension` unpacked
4. Copy the extension ID (e.g., `jkbicjdjcknffafabcdefghijk`)

### Step 4: Update Manifest Permission

Edit `com.rhea.frontier_gem.json`:
```json
{
  "allowed_extensions": [
    "chrome-extension://jkbicjdjcknffafabcdefghijk"
  ]
}
```

### Step 5: Start Daemon

```bash
frontier-gem daemon
# Output: 📡 Gem Daemon Starting...
#         🌐 HTTP Server Online at 127.0.0.1:3456
#         🚌 Bus Online at TCP 127.0.0.1:4444
```

## Usage

### Native Messaging (from extension)

```javascript
// Connect to native host
const port = chrome.runtime.connectNative('com.rhea.frontier_gem');

// Send observation
port.postMessage({
    event: "tab_focus",
    url: "https://example.com",
    title: "Page Title",
    timestamp: Date.now()
});

// Listen for messages
port.onMessage.addListener((msg) => {
    console.log("Received:", msg);
});
```

### HTTP API (from any browser/app)

```bash
# POST observation
curl -X POST http://localhost:3456/api/observe \
  -H "Content-Type: application/json" \
  -d '{
    "event": "page_view",
    "url": "https://example.com",
    "timestamp": 1234567890
  }'

# Response:
{
  "status": "ok",
  "path": "/api/observe",
  "timestamp": 1709707289
}

# OPTIONS request (CORS preflight)
curl -X OPTIONS http://localhost:3456/api/observe \
  -H "Origin: *"

# Response headers:
# Access-Control-Allow-Origin: *
# Access-Control-Allow-Methods: GET, POST, OPTIONS
# Access-Control-Allow-Headers: Content-Type
```

### CORS Headers

All HTTP responses include:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

## Heartbeat System

### 5-Minute Heartbeat

Every 5 minutes (300,000 ms), the extension sends:

```javascript
{
    type: "heartbeat",
    timestamp: 1709707289,
    uptime: 12345  // seconds since last activity
}
```

**Log Output:**
```
💓 Heartbeat sent @ 2:45:12 PM
💓 Heartbeat sent @ 2:50:12 PM
💓 Heartbeat sent @ 2:55:12 PM
```

### Idle Detection

After 30 minutes (1,800,000 ms) without tab activity:

```javascript
{
    type: "idle",
    timestamp: 1709707289,
    reason: "idle_timeout"
}
```

**Activity Triggers (reset idle timer):**
- Tab activated
- Tab updated
- Web request initiated
- Message received from daemon

### Configuration

Edit `background.js` to change intervals:
```javascript
const HEARTBEAT_INTERVAL = 5 * 60 * 1000;  // 5 minutes
const IDLE_TIMEOUT = 30 * 60 * 1000;       // 30 minutes
```

## Event Flow

### 1. Browser Activity → Extension

```
User clicks tab
    ↓
chrome.tabs.onActivated listener fires
    ↓
lastActivityTime = Date.now()
    ↓
resetIdleTimer() (clears 30-min timeout)
    ↓
port.postMessage({event: "tab_focus", ...})
```

### 2. Extension → Native Host

```
extension sends message via stdin
    ↓
frontier-gem proxy mode reads from stdin
    ↓
Connects to TCP bus (localhost:4444)
    ↓
Sends message to daemon
    ↓
Appends to event log (/tmp/0.log)
    ↓
Broadcasts to all subscribers
```

### 3. HTTP Server Receives Request

```
POST /api/observe (from browser/curl/app)
    ↓
HTTP server parses request
    ↓
Extracts JSON body
    ↓
Appends event with hash chain
    ↓
Responds with CORS headers + 200 OK
    ↓
Broadcast to all TCP subscribers
```

## File Structure

```
frontier-gem/
├── src/
│   └── main.rs                    # HTTP server + TCP bus + mDNS
├── gem-extension/
│   ├── manifest.json              # Chrome extension config (v3)
│   └── background.js              # Heartbeat + native messaging
├── Support/Google/Chrome/
│   └── NativeMessagingHosts/
│       └── com.rhea.frontier_gem.json   # Native host registration
├── Cargo.toml                     # Rust dependencies
└── daemon.log                     # Runtime logs
```

## Security

### Code Signing (macOS)

```bash
sudo codesign --force -s - /usr/local/bin/frontier-gem
```

### Permissions

**Extension Manifest:**
- `activeTab` — Read active tab info
- `tabs` — Read all tab info
- `nativeMessaging` — Communicate with native host
- `webRequest` — Monitor web requests (optional)

**Native Host Manifest:**
- Must be in user's Chrome directory (not system-wide)
- Only specified extension IDs can connect
- Type: `stdio` (stdin/stdout communication)

### Network

- HTTP server listens on `127.0.0.1:3456` (localhost only)
- TCP bus on `127.0.0.1:4444` (localhost only)
- No internet connectivity required
- CORS allows any origin (configure as needed)

## Troubleshooting

### "Native host not found" Error

```
Solution:
1. Verify binary exists: ls -la /usr/local/bin/frontier-gem
2. Check manifest location: 
   ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts/
3. Verify manifest has correct extension ID
4. Restart Chrome completely
```

### HTTP Server Not Responding

```
Solution:
1. Check if daemon is running: ps aux | grep frontier-gem
2. Verify port 3456 is listening: lsof -i :3456
3. Start daemon manually: frontier-gem daemon
4. Check logs: tail -f daemon.log
```

### Heartbeat Not Sending

```
Solution:
1. Open Chrome DevTools → Extensions → Service Workers
2. Check background.js console for errors
3. Verify native connection established ("🔌 Native connection...")
4. Check every 5 minutes for "💓 Heartbeat sent" message
```

### Idle Timeout Not Triggering

```
Solution:
1. Extension must have 30 minutes of inactivity
2. Check lastActivityTime in console
3. Idle triggers on: tab update, tab activation, web request
4. Check browser console for "😴 Service Worker idle" message
```

## Development

### Testing HTTP Endpoint

```bash
# Terminal 1: Start daemon
frontier-gem daemon

# Terminal 2: Send test requests
curl -X POST http://localhost:3456/api/test \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

curl -X OPTIONS http://localhost:3456/api/test
```

### Testing Native Messaging

```bash
# View background.js console
chrome://extensions → "Service Workers" → Click the running worker

# Watch logs in real-time
tail -f daemon.log
tail -f /tmp/0.log
```

## Future Enhancements

1. **HTTP Server Expansion**
   - Add `/api/health` endpoint
   - Implement `/api/events` (retrieve event history)
   - Add `/api/stats` for daemon metrics

2. **Heartbeat Customization**
   - Configurable interval via settings
   - Exponential backoff on failures
   - Health check responses

3. **Idle Handling**
   - Custom actions on idle (e.g., sync, upload)
   - Wake-up signals from daemon
   - Idle state persistence

4. **Security**
   - Certificate pinning
   - Message signing/encryption
   - Rate limiting on HTTP endpoints

5. **mDNS Enhancement**
   - Peer-to-peer communication
   - Distributed event log
   - Consensus mechanisms

## References

- [Chrome Extension Native Messaging](https://developer.chrome.com/docs/extensions/mv3/nativeMessaging/)
- [Manifest V3 Migration Guide](https://developer.chrome.com/docs/extensions/mv3/mv3-migration/)
- [Tokio Async Runtime](https://tokio.rs/)
- [mDNS Service Discovery](https://tools.ietf.org/html/rfc6763)

## Status

✅ HTTP Server with CORS headers (Access-Control-Allow-Origin: *, Methods: GET, POST, OPTIONS)  
✅ Native messaging via chrome.runtime.connectNative('com.rhea.frontier_gem')  
✅ 5-minute heartbeat signals  
✅ 30-minute idle timeout detection  
✅ TCP bus for event broadcast  
✅ Event logging with hash chain  
✅ mDNS service registration  

---

**Implementation Date:** 2026-03-06  
**Last Updated:** 2026-03-06  
**Version:** 1.0
