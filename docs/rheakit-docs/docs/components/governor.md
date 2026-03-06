---
sidebar_position: 6
title: GovernorView
---

# GovernorView

A real-time budget and pace dashboard for monitoring AI agent resource consumption. Displays token burn charts, per-agent status cards, and operational mode indicators.

## Usage

```swift
import RheaKit

struct GovernorTab: View {
    var body: some View {
        GovernorView()
    }
}
```

## Features

- **Token burn chart** — Swift Charts line graph showing cumulative token usage over time (last 5 minutes)
- **Summary header** — Total tokens, total cost, alive/dead agent counts
- **Agent cards** — Per-agent status with pace, mode, tokens, cost, and floor gap
- **Auto-polling** — Refreshes from `/agents/status` every 5 seconds
- **Pop animations** — Agent cards enter with Pow `.pop` transitions
- **Pull to refresh** — Standard refresh gesture

## Agent Status (AgentDTO)

Each agent card displays data from the `AgentDTO`:

| Field | Type | Description |
|---|---|---|
| `name` | `String` | Agent identifier (rex, orion, hyperion, etc.) |
| `alive` | `Bool` | Whether the agent is currently responsive |
| `pace` | `String` | Budget pace: `"green"`, `"yellow"`, or `"red"` |
| `mode` | `String` | Operational mode: `"normal"`, `"compact"`, `"critical"`, `"hard_fail"` |
| `billing_mode` | `String?` | Current billing tier |
| `T_day` | `Int` | Tokens consumed today |
| `dollar_day` | `Double` | Dollar cost today |
| `floor_gap` | `Int` | Gap to minimum required floor |
| `forecast` | `String?` | Budget forecast text |
| `budget_cap` | `Double?` | Maximum daily budget |
| `budget_remaining` | `Double?` | Remaining budget |
| `hard_fail` | `Bool?` | Whether agent is in hard-fail mode |

## Token Burn Chart

The chart tracks `BurnPoint` samples:

```swift
public struct BurnPoint: Identifiable {
    public let id: UUID
    public let ts: Date      // sample timestamp
    public let tokens: Int   // cumulative tokens at this point
}
```

Up to 60 data points are retained (5 minutes at 5-second intervals). The chart is built with Swift Charts.

## Color Coding

Agent cards use `RheaTheme` semantic colors:

- **Pace**: green → `RheaTheme.green`, yellow → `RheaTheme.amber`, red → `RheaTheme.red`
- **Mode**: normal → green, compact → amber, critical → red, hard_fail → purple
- **Status**: alive → green border, dead → red border

## Notes

- Requires the `/agents/status` endpoint on the Rhea backend
- The view shows `ContentUnavailableView` when the Governor API is unreachable
- Governor counters reset to zero on backend restart — this is expected behavior
