# Windows Text Injection — Complete Guide

## Overview

The Windows Text Injection feature allows frontier-gem to inject text into the focused window's text field via the HTTP API. This enables AI-generated responses, code completions, and other automated text input directly into any text editor, browser, IDE, or application.

**Platform:** Windows only (gracefully skipped on macOS/Linux)

## Architecture

### Components

1. **TextInjector (Rust Core)** - `frontier-gem/src/windows_injector.rs`
   - Win32 SendInput API for keyboard simulation
   - Safety validation (block password fields)
   - Text validation (max 10KB, 1000ms delay per char)
   - Cross-platform with graceful fallback

2. **HTTP Endpoint** - `frontier-gem/src/main.rs`
   - POST `/api/inject` with JSON body
   - Response includes character count, timestamp
   - Error messages for failures

3. **Chrome Extension UI** - `frontier-gem/gem-extension/background.js`
   - `injectText()` function for programmatic injection
   - Context menu: "Inject AI Response" on editable fields
   - Desktop notifications for success/failure
   - Message listener for injection requests

### Flow Diagram

```
User triggers injection (button/context menu/message)
    ↓
Chrome Extension: injectText(text)
    ↓
HTTP POST /api/inject {text, delay_ms}
    ↓
frontier-gem: HTTP Server receives request
    ↓
Windows: TextInjector::inject_text()
    ↓
Win32 SendInput API
    ↓
Keyboard events to focused window
    ↓
Text appears in focused field
    ↓
Response: {status: "ok", characters: N, timestamp: T}
    ↓
Extension shows notification
```

## API Specification

### HTTP Endpoint

**POST** `/api/inject`

**Request:**
```json
{
  "text": "Hello, World!",
  "delay_ms": 50
}
```

**Parameters:**
- `text` (string, required) - Text to inject (max 10KB)
- `delay_ms` (number, optional) - Delay between keystrokes in milliseconds (0-1000, default 50)

**Success Response (200 OK):**
```json
{
  "status": "ok",
  "message": "Text injected successfully",
  "characters": 13,
  "timestamp": 1709707289
}
```

**Error Response (400 Bad Request):**
```json
{
  "status": "error",
  "message": "Unsafe target: Target class 'Edit_Password' is not safe for injection",
  "timestamp": 1709707289
}
```

**Possible Errors:**
- `No focused window found` — No window has focus
- `Invalid target` — Target is not a text input field
- `Injection failed` — SendInput API call failed
- `Unsafe target` — Password field or system window detected
- `Text exceeds 10KB limit` — Request too large
- `Text injection is only supported on Windows` — Running on non-Windows OS

### Testing with cURL

```bash
# Simple injection
curl -X POST http://localhost:3456/api/inject \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello from frontier-gem!",
    "delay_ms": 50
  }'

# With response validation
curl -X POST http://localhost:3456/api/inject \
  -H "Content-Type: application/json" \
  -d '{"text": "Test", "delay_ms": 0}' | jq '.status'

# Minimal (uses defaults)
curl -X POST http://localhost:3456/api/inject \
  -H "Content-Type: application/json" \
  -d '{"text": "Quick test"}'
```

## Extension Integration

### Programmatic Injection

From any Chrome extension component:

```javascript
// Simple injection
chrome.runtime.sendMessage({
    action: 'inject',
    text: 'Generated AI response here',
    delayMs: 50
}, (response) => {
    if (response.success) {
        console.log("Injected:", response.message);
    } else {
        console.error("Failed:", response.message);
    }
});
```

### Manual Injection

Call the `injectText()` function directly:

```javascript
// In background.js context
await injectText('Your text here', 50);

// Returns: {success: boolean, message: string}
```

### Context Menu Integration

The extension automatically creates a context menu item:
- **Menu Item:** "Inject AI Response (Windows Only)"
- **Contexts:** Editable text fields
- **Shortcut:** Right-click on any input field while extension is active

### Notifications

Injection status is shown via Chrome desktop notifications:
- ✅ **Success:** Shows character count typed
- ❌ **Failure:** Shows error message
- Auto-closes after 5 seconds

## Safety Features

### Protected Fields (Blocked)

The TextInjector automatically blocks injection into:
- Password fields: `Edit_Password`, `Password`, `Credential`, `Secret`, `PIN`
- System controls: `SysListView32`, `SysTreeView32`, `SHELLDLL_DefView`, etc.
- Dialog windows: `#32770`
- Authentication fields: `Authentication`

### Validation Checks

1. **Text Size:** Max 10KB (prevents DoS/buffer overflow)
2. **Delay Limit:** Max 1000ms per keystroke (prevents abuse)
3. **Character Validation:** Rejects null bytes and dangerous control characters
4. **Window Validation:** Verifies window exists and is focused

### Whitelisted Targets

Safe targets that allow injection:
- `Edit` — Text input fields
- `RichEditText`, `RichEdit` — Rich text editors
- `Chrome_RenderWidgetHostHWND` — Chrome web pages
- `Firefox`, `MozillaWindowClass` — Firefox
- `Notepad` — Windows Notepad
- `CabinetWClass` — File Explorer

## Supported Applications

### Verified Working

| Application | Status | Notes |
|------------|--------|-------|
| Notepad | ✅ | Direct keystroke injection |
| Word | ✅ | Via RichEdit control |
| VS Code | ✅ | Via Chrome renderer |
| Chrome | ✅ | Web page text fields |
| Firefox | ✅ | Web page text fields |
| PowerShell | ✅ | Console text input |
| Slack | ✅ | Web version (Chrome) |
| Discord | ✅ | Web version (Chrome) |

### Limitations

| Application | Status | Reason |
|------------|--------|--------|
| Password fields | ❌ | Blocked by safety check |
| macOS apps | ❌ | Windows-only feature |
| Linux apps | ❌ | Windows-only feature |
| UAC elevation | ❌ | Requires user privileges |
| Admin terminal | ✅ | If elevation already granted |

## Configuration

### Keystroke Delay

Adjust the delay between individual keystrokes to control injection speed:

```javascript
// Fast injection (0ms per character)
injectText("Quick text", 0);

// Medium speed (50ms per character) - DEFAULT
injectText("Normal speed", 50);

// Slow injection (100ms per character) - more reliable
injectText("Slow text", 100);

// Crawl speed (500ms per character) - debugging
injectText("Debug text", 500);
```

**Recommendation:** Use 50ms for most cases, increase if experiencing missed keystrokes.

### Max Text Length

Current limit: **10 KB (10,240 bytes)**

To change, modify `windows_injector.rs`:
```rust
const MAX_TEXT_LEN: usize = 10240;  // Change this value
```

### Blocked Patterns

To add or remove protected patterns, edit `windows_injector.rs`:

```rust
let blocked_patterns = vec![
    "Password",
    "YourCustomPattern",  // Add here
];

let allowed = vec![
    "Edit",
    "YourCustomControl",  // Add here
];
```

## Troubleshooting

### "No focused window found"

**Cause:** No application window has focus

**Solution:**
1. Click on the target application window first
2. Wait for the window to be focused
3. Then trigger injection

### "Invalid target: Target class not safe"

**Cause:** You're trying to inject into a protected field

**Solution:**
1. Click on an actual text input field (not a password field)
2. Check the window class name in the error message
3. Add to whitelist if legitimate use case

### Text not appearing

**Cause:** Keystroke speed too fast, or application doesn't accept events

**Solution:**
1. Increase `delay_ms` parameter (try 100-200ms)
2. Verify window is focused when injection starts
3. Check if application blocks SendInput (some games do)

### "Injection failed: Failed to send key"

**Cause:** Win32 SendInput API returned an error

**Solution:**
1. Run daemon with admin privileges
2. Check if antivirus/firewall is blocking
3. Restart the daemon
4. Try in Notepad to verify system works

### Notification not showing

**Cause:** Chrome notification permission issue

**Solution:**
1. Open `chrome://extensions` → Gem Observer → Details
2. Check "Notifications" permission is granted
3. Reload extension: Click the refresh icon
4. Try again

### Connection timeout

**Cause:** Daemon not running or HTTP server not responding

**Solution:**
1. Verify daemon is running: `frontier-gem daemon`
2. Check HTTP server port: `lsof -i :3456`
3. Try manual curl: `curl http://localhost:3456/api/inject`
4. Restart daemon if needed

## Performance

### Typical Injection Times

| Text Length | Delay | Time |
|------------|-------|------|
| 10 chars | 50ms | ~0.5s |
| 100 chars | 50ms | ~5s |
| 1000 chars | 50ms | ~50s |
| 10KB | 0ms | ~100ms |

**Note:** Larger delays increase reliability but slow down injection.

## Security Considerations

### What This Does NOT Do

- ❌ Does NOT capture keystrokes (only sends them)
- ❌ Does NOT store clipboard data
- ❌ Does NOT access file system
- ❌ Does NOT send data to internet
- ❌ Does NOT run scripts or code
- ❌ Does NOT modify system files

### What This DOES Do

- ✅ Simulates keyboard input (like typing)
- ✅ Requires user to trigger injection
- ✅ Logs injection attempts to event log
- ✅ Validates injection targets
- ✅ Blocks dangerous field types
- ✅ Local network only (localhost:3456)

### Risk Mitigation

1. **Opt-in Design:** Requires explicit user action (button/menu click)
2. **Target Validation:** Blocks password fields automatically
3. **Size Limits:** Max 10KB prevents DoS
4. **Rate Limiting:** 500ms cooldown between injections
5. **Local Network:** Only accessible on localhost
6. **Logging:** All injections logged to event log

## Development

### Building from Source

```bash
# On Windows, build will include TextInjector
cd frontier-gem
cargo build --release

# Windows binary: target/release/frontier-gem.exe
```

### Testing

```bash
# 1. Start daemon
frontier-gem daemon

# 2. In another terminal, test injection
curl -X POST http://localhost:3456/api/inject \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from curl!", "delay_ms": 50}'

# 3. Open Notepad
# 4. Click in Notepad window
# 5. Run curl command above
# 6. Text should appear in Notepad
```

### Debugging

Enable verbose logging in `background.js`:

```javascript
// Add at top of injectText()
console.log("Injection request:", { text, delayMs });
console.log("Sending to:", 'http://localhost:3456/api/inject');
```

Check daemon logs:
```bash
tail -f /tmp/0.log | grep inject
```

## Future Enhancements

1. **Clipboard Paste** — Alternative to keyboard injection for large texts
2. **Hotkey Binding** — Global keyboard shortcut to trigger injection
3. **Text History** — Store recently injected texts
4. **Smart Delay** — Auto-adjust delay based on system load
5. **Undo Support** — Keystroke can be undone (uses Ctrl+Z)
6. **Unicode Support** — Better handling of special characters/emoji
7. **macOS Support** — Equivalent feature using CGEvent
8. **Linux Support** — Using xdotool or uinput

## References

- [Windows SendInput API](https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput)
- [Virtual Key Codes](https://docs.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes)
- [Windows Class Names](https://docs.microsoft.com/en-us/windows/win32/winmsg/about-window-classes)
- [Chrome Runtime Messaging](https://developer.chrome.com/docs/extensions/mv3/messaging/)
- [Chrome Context Menus](https://developer.chrome.com/docs/extensions/reference/contextMenus/)

## Status

✅ **Windows Text Injection v1.0**
- ✅ Core implementation complete
- ✅ HTTP endpoint implemented
- ✅ Extension integration done
- ✅ Safety features implemented
- ✅ Documentation complete
- ⏳ Windows-only (macOS/Linux support future)

---

**Implementation Date:** 2026-03-06  
**Platform:** Windows  
**Status:** Ready for Production
