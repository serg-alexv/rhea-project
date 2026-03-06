---
sidebar_position: 7
title: TasksView
---

# TasksView

A kanban-style task management view for tracking work across the multi-agent system. Supports filtering by status, agent, and priority, with the ability to create new tasks.

## Usage

```swift
import RheaKit

struct TasksTab: View {
    var body: some View {
        TasksView()
    }
}
```

## Features

- **Status filters** — All, open, claimed, done, blocked
- **Agent filter** — Filter tasks by the claiming agent
- **Priority filter** — Filter by P0, P1, P2
- **Lens mode** — Combine multiple filters for focused views
- **Create tasks** — New task sheet with title, priority, and agent assignment
- **Auto-polling** — Refreshes from the backend periodically
- **Animated transitions** — Pow `.pop` transitions for task cards

## Data Model

```swift
public struct TaskItem: Codable, Identifiable {
    public let id: String
    public let title: String
    public let priority: String     // "P0", "P1", "P2"
    public let status: String       // "open", "claimed", "done", "blocked"
    public let agent: String        // originating agent
    public let claimed_by: String   // agent that claimed the task
    public let tags: [String]       // category tags
}
```

## Color Coding

Tasks use `RheaTheme` semantic colors:

| Priority | Color |
|---|---|
| P0 | `RheaTheme.red` |
| P1 | `RheaTheme.amber` |
| P2 | `RheaTheme.accent` |

| Status | Color |
|---|---|
| open | secondary |
| claimed | `RheaTheme.accent` |
| done | `RheaTheme.green` |
| blocked | `RheaTheme.red` |

## New Task Creation

The creation sheet sends a POST request with:

```swift
{
    "title": "<task title>",
    "priority": "P0" | "P1" | "P2",
    "agent": "<agent name>"
}
```

## Notes

- Tasks are fetched from and created via the Rhea backend API
- The view detects unique agents and priorities from the task list for dynamic filter chips
- Empty state shows a message when no tasks match current filters
