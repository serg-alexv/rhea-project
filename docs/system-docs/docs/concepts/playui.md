---
sidebar_position: 3
---

# Play UI — AI-Driven Interface Generation

Play UI is Rhea's concept for AI-generated user interfaces: instead of static layouts, the system generates UI components dynamically based on context, user state, and conversation flow.

## Concept

Traditional apps have fixed screens. Play UI generates interface elements on-the-fly:
- A tribunal result might render as a comparison table, a confidence meter, or a debate visualization
- Clipboard entries might appear as cards, a timeline, or a spatial map
- Agent status might render as a network graph or a simple list — depending on what's happening

## Current Implementation

The Tribunal API serves a Play UI page at `GET /play-ui` that demonstrates the concept with the agent dashboard.

The system includes:
- **play-token-mapper** — maps AI output tokens to UI components
- **play-extraction** (in ios/) — extracts UI patterns from conversations
- **play_frame_00.png** — reference frame for Play UI rendering

## Architecture

```
Prompt / Context
       ↓
  AI Model (LLM)
       ↓
  Token Stream
       ↓
  Play Token Mapper
       ↓
  UI Component Tree
       ↓
  Renderer (SwiftUI / Web)
```

## Actuator System

The Play UI connects to a browser/app actuator for bidirectional control:

| Endpoint | Description |
|----------|-------------|
| `POST /actuator/sync` | Sync visual state from browser tab |
| `GET /actuator/health` | Check actuator connection |
| `POST /actuator/command` | Send command (CLICK, TYPE, SCROLL) to browser |
| `GET /actuator/command` | Poll for pending commands |
| `POST /actuator/receipt` | Report command execution result |

The actuator enables the AI to observe and interact with web pages — reading state and issuing actions.

**Status:** Conceptual framework implemented. Token-to-component mapping and real-time rendering are in active development.
