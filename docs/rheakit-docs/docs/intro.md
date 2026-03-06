---
slug: /
sidebar_position: 1
title: Introduction
---

# RheaKit

**RheaKit** is a SwiftUI component library for building AI-driven control interfaces. It provides a complete set of views for monitoring multi-agent systems, visualizing molecular structures, managing tasks, and interacting with tribunal-based consensus engines.

## What's Inside

RheaKit ships as a single Swift Package containing **40+ SwiftUI views** and supporting infrastructure:

| Layer | What it provides |
|---|---|
| **RheaTheme** | Dark-first design system — colors, glass-card modifier, mode/status palettes |
| **RheaAPI** | Singleton HTTP client with JWT/API-key auth, typed endpoints, error handling |
| **RheaStore** | `@Observable` shared state — polling loop, GRDB-backed local cache, staleness tracking |
| **Views** | Full-screen panes: TeamChat, BioRenderer, NodeEditor, Governor, Tasks, Aletheia, Processes, and more |

## Requirements

| Requirement | Version |
|---|---|
| Swift | 5.9+ |
| iOS | 17.0+ |
| macOS | 14.0+ |
| Xcode | 15.0+ |

## Installation

Add RheaKit via Swift Package Manager:

```swift
// Package.swift
dependencies: [
    .package(path: "../packages/RheaKit"),
]
```

Or add the repository URL in Xcode:
1. **File → Add Package Dependencies…**
2. Enter the repository URL
3. Select version or branch

## Dependencies

RheaKit builds on these packages (resolved automatically via SPM):

| Package | Purpose |
|---|---|
| [GRDB.swift](https://github.com/groue/GRDB.swift) | Local SQLite cache for offline access |
| [swift-collections](https://github.com/apple/swift-collections) | `OrderedDictionary` for agent maps |
| [KeychainAccess](https://github.com/kishikawakatsumi/KeychainAccess) | Secure JWT/API-key storage |
| [swift-markdown-ui](https://github.com/gonzalezreal/swift-markdown-ui) | Markdown rendering in chat views |
| [Starscream](https://github.com/daltoniam/Starscream) | WebSocket streaming for live feeds |
| [Pow](https://github.com/serg-alexv/Pow) | Transition animations (pop, glow) |

## Architecture at a Glance

```
┌──────────────────────────────────────────┐
│  SwiftUI Views (TeamChat, Governor, …)   │
├──────────────────────────────────────────┤
│  RheaStore (shared @Observable state)    │
├──────────────────────────────────────────┤
│  RheaAPI (HTTP client, typed endpoints)  │
├──────────────────────────────────────────┤
│  AuthManager (JWT + Keychain)            │
├──────────────────────────────────────────┤
│  Rhea Backend (Fly.io / localhost:8400)  │
└──────────────────────────────────────────┘
```

Every view reads from `RheaStore.shared` or calls `RheaAPI.shared` directly. No duplicate fetchers — one polling loop, one source of truth.
