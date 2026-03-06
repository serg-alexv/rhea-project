# 🌟 Rhea CLI — Cross-Device Chat Terminal

Responsive, alive terminal UI for Rhea sessions. Type fast, see instantly.

## Quick Start

**Terminal 1: Start the server**
```bash
cd /Users/sa/rh.1/rhea-session-server
cargo run --bin server --release
# Or: ./target/release/server
```

**Terminal 2: Run the CLI**
```bash
cd /Users/sa/rh.1/rhea-cli
cargo run
# Or: ./target/debug/rhea-cli
```

## Features

- **🎨 Character Selection** — Pick Protos/Zerg/Terran/Aeon (each with unique color + emoji)
- **⚡ Live Feedback** — Input changes color as you type (gray → green)
- **📊 Session Info** — Live message count, device ID, character name
- **🔄 Cross-Device Sync** — Messages sync via Lamport clocks (deterministic order)
- **💾 Local SQLite** — Each device has its own truth (immutable append-only log)

## Commands

| Key | Action |
|-----|--------|
| `1-4` | Select character (1=Protos, 2=Zerg, 3=Terran, 4=Aeon) |
| `Type text` | Compose message |
| `Enter` | Send message |
| `Esc` | Back to character select / Quit |
| `Ctrl+C` | Force quit |
| `--help` | Show help |

## Architecture

```
Your Terminal (CLI)
    ↓ (raw mode, crossterm)
ratatui UI engine
    ↓ (events: keypresses)
RheaClient (async/await)
    ↓ (HTTP requests)
Server (http://127.0.0.1:3000)
    ↓ (assign Lamport clocks)
Local SQLite (:memory:)
    ↓ (append-only, immutable)
Message order = Causality (via LC), not wall-clock time
```

## Design Philosophy

**Alive ≠ Fast**
- Causality > wall-clock time (deterministic across devices)
- Append-only immutable log (CRDT convergence guaranteed)
- Sub-100ms UI feedback (every keystroke echoed instantly)
- No layers between you & terminal (raw mode, direct control)

**Control**
- You control YOUR terminal's flow
- Server controls message ordering (via Lamport clocks)
- Each device is a sovereign peer (local SQLite is your truth)

## Troubleshooting

**"Failed to connect to server"**
- Make sure server is running: `./target/release/server`
- Check port: `curl http://127.0.0.1:3000/sessions`
- Custom server: `RHEA_SERVER=http://example.com:8080 rhea-cli`

**"Message didn't appear"**
- Check server logs (should show lamport_clock assignment)
- Verify local SQLite: `sqlite3 :memory: "SELECT * FROM messages;"`
- Messages sync on next poll (100ms event loop)

**"Terminal looks broken"**
- Make sure your terminal supports ratatui (Kitty, iTerm2, or Alacritty recommended)
- Disable other TUI apps that might interfere

## Testing

```bash
# Test server + CLI together
bash ../test_cli.sh
```

## Performance

- **Startup**: ~50ms (initialization)
- **Keystroke → Echo**: <20ms (ratatui render)
- **Message Send**: ~500ms (HTTP + Lamport clock assign)
- **UI Refresh**: 100ms (event loop) = snappy feel
