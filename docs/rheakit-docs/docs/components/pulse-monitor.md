---
sidebar_position: 10
title: PulseMonitorView
---

# PulseMonitorView

A system-level monitoring dashboard showing agent pulse status, task queue health, and lease states. Designed for ops-console oversight of the multi-agent system.

## Usage

```swift
import RheaKit

struct PulseTab: View {
    var body: some View {
        PulseMonitorView()
    }
}
```

## Features

- **Queue summary** — Total tasks, counts by status, active by priority, stale count
- **Agent pulse cards** — Per-agent status with lease token, lease expiry, office status
- **Auto-polling** — Refreshes on a timer for near-real-time monitoring
- **Agent table filtering** — Reads the same `@AppStorage` agent preferences as TeamChatView

## Data Models

### PulseQueueSummary

```swift
public struct PulseQueueSummary: Codable {
    public let total: Int                       // total items in queue
    public let counts: [String: Int]            // count by status
    public let active_by_priority: [String: Int] // count by priority
    public let stale_count: Int                 // items past deadline
    public let _updated: String?                // last update timestamp
}
```

### Agent Data

Pulse uses the same `AgentDTO` as GovernorView, with additional lease fields:

| Field | Type | Description |
|---|---|---|
| `lease_token` | `Int?` | Current lease token count |
| `lease_expired` | `Bool?` | Whether the agent's lease has expired |
| `lease_expires_at` | `String?` | ISO 8601 lease expiry time |
| `office_status` | `String?` | Agent's office status |
| `pending_msgs` | `Int?` | Unread message count |
| `tasks_open` | `Int?` | Open tasks assigned to agent |
| `tasks_claimed` | `Int?` | Tasks claimed by agent |

## Notes

- Shares agent table preferences with TeamChatView (`table_rex`, `table_orion`, etc.)
- The pulse endpoint returns a unified response with all agents and queue summary
- Lease tracking helps identify agents that need token renewal
