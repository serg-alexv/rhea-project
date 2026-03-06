---
sidebar_position: 3
title: Design System
---

# Design System

RheaKit's visual language is defined in `RheaTheme` — a single enum with static color constants, semantic color functions, and the `GlassCard` view modifier.

## Color Palette

All colors are defined as `Color` constants on `RheaTheme`:

| Token | Value | Usage |
|---|---|---|
| `bg` | `rgb(15, 15, 26)` | Primary background — dark navy |
| `card` | `rgb(26, 26, 41)` | Card/panel fill |
| `cardBorder` | `white @ 6%` | Subtle card outline |
| `accent` | `rgb(102, 217, 255)` | Cyan — primary interactive color |
| `green` | `rgb(77, 230, 128)` | Success, online, healthy |
| `amber` | `rgb(255, 199, 51)` | Warning, compact mode |
| `red` | `rgb(255, 89, 89)` | Error, critical, offline |
| `purple` | `rgb(179, 128, 255)` | Proof markers, hard-fail state |
| `muted` | `white @ 50%` | Secondary text |
| `text` | `white` | Primary text |

```swift
Text("Online")
    .foregroundStyle(RheaTheme.green)

Text("3 alerts")
    .foregroundStyle(RheaTheme.red)

Rectangle()
    .fill(RheaTheme.bg)
```

## Semantic Color Functions

RheaTheme provides context-aware color mappings:

### `modeColor(_ mode: String) -> Color`

Maps operational modes to colors:

| Mode | Color |
|---|---|
| `"normal"` | green |
| `"compact"` | amber |
| `"critical"` | red |
| `"hard_fail"` | purple |

### `paceColor(_ pace: String) -> Color`

Maps agent pace indicators:

| Pace | Color |
|---|---|
| `"green"` | green |
| `"yellow"` | amber |
| `"red"` | red |

### `priorityColor(_ priority: String) -> Color`

Maps task priorities:

| Priority | Color |
|---|---|
| `"P0"` | red |
| `"P1"` | amber |
| `"P2"` | accent (cyan) |

### `statusColor(_ status: String) -> Color`

Maps task/item status:

| Status | Color |
|---|---|
| `"open"` | secondary |
| `"claimed"` | accent (cyan) |
| `"done"` | green |
| `"blocked"` | red |

## GlassCard Modifier

The `.glassCard()` modifier applies the signature frosted-glass panel style used throughout RheaKit:

```swift
VStack {
    Text("Agent: Rex")
    Text("Tokens: 12K")
}
.glassCard()
```

This applies:
- **16pt padding** on all sides
- **Card fill** (`RheaTheme.card`) with 16pt corner radius
- **1px border** at `white @ 6%` opacity

### Implementation

```swift
public struct GlassCard: ViewModifier {
    public init() {}

    public func body(content: Content) -> some View {
        content
            .padding(16)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(RheaTheme.card)
                    .overlay(
                        RoundedRectangle(cornerRadius: 16)
                            .stroke(RheaTheme.cardBorder, lineWidth: 1)
                    )
            )
    }
}
```

## Typography Conventions

RheaKit doesn't define custom fonts but follows consistent patterns:

| Context | Font |
|---|---|
| Section headers | `.system(size: 10, weight: .bold, design: .monospaced)` |
| Body/content | `.system(size: 12, design: .monospaced)` |
| Badges/labels | `.system(size: 9, weight: .bold, design: .monospaced)` |
| Status indicators | `.system(size: 8–9, design: .monospaced)` |

The monospaced design is used consistently to give the UI a terminal/ops-console aesthetic.
