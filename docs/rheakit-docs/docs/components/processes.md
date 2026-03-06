---
sidebar_position: 9
title: ProcessesView
---

# ProcessesView

A supervisor session manager for spawning, monitoring, and controlling agent processes. Provides real-time output viewing and interactive input for running sessions.

## Usage

```swift
import RheaKit

struct ProcessesTab: View {
    var body: some View {
        ProcessesView()
    }
}
```

## Features

- **Session list** — View all supervisor sessions with status badges (running, stopped, idle)
- **Spawn agents** — Launch new agent sessions with optional prompt
- **Kill sessions** — Terminate running sessions with confirmation
- **Live output** — View the last N lines of output from any session
- **Send input** — Type and send text input to interactive sessions
- **Status badges** — Running count and total count in toolbar

## Data Model

```swift
public struct SupervisorSession: Codable, Identifiable {
    public let id: String
    public let agent: String?       // agent name (rex, orion, etc.)
    public let status: String?      // "running", "active", "stopped", "killed", "idle"
    public let started_at: String?  // ISO 8601 start time
    public let pid: Int?            // OS process ID

    public var isAlive: Bool        // true if status is "running" or "active"
    public var stateColor: String   // "green", "red", "amber", or "secondary"
}
```

## API Endpoints

| Action | Method | Endpoint |
|---|---|---|
| List sessions | `GET` | `/supervisor/sessions` |
| Spawn agent | `POST` | `/supervisor/spawn` |
| Kill session | `POST` | `/supervisor/kill/:id` |
| Get output | `GET` | `/supervisor/output/:id?lines=50` |
| Send input | `POST` | `/supervisor/input/:id` |

## Known Agents

The spawn dialog offers these pre-configured agent names: `rex`, `orion`, `gemini`, `hyperion`, `shared`, `b2`.

## Notes

- Uses `RheaStore.shared` for shared agent state observation
- Session output is fetched on-demand (not polled) when a session is selected
- The spawn payload includes `agent` name and optional `prompt` text
- Kill requires `confirm: true` in the request body as a safety guard
