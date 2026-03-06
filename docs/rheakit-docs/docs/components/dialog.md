---
sidebar_position: 5
title: DialogView
---

# DialogView

A tribunal-powered chat interface for conversational AI queries. Sends prompts to the Rhea multi-model consensus engine and displays responses with agreement scores, model counts, and response times.

## Usage

```swift
import RheaKit

struct ChatTab: View {
    var body: some View {
        DialogView()
    }
}
```

## Features

- **Multi-model consensus** — Every query goes through the tribunal (multiple LLMs)
- **Markdown rendering** — AI responses rendered with `MarkdownUI`
- **Chat history** — Loads previous messages from `GET /cc/dialog`
- **Agreement score** — Displays inter-model agreement as a percentage
- **Response metadata** — Shows models responded count and elapsed time
- **Human/AI distinction** — Messages styled differently for human vs AI senders

## Data Models

### ChatMsg

```swift
public struct ChatMsg: Codable, Identifiable {
    public let id: String
    public let sender: String   // "human" or agent name
    public let text: String     // message content
    public let ts: String       // ISO 8601 timestamp

    public var isHuman: Bool    // true if sender == "human"
    public var displayTime: String  // "HH:mm" extracted from timestamp
}
```

### DialogResponse

The backend returns enriched responses:

```swift
public struct DialogResponse: Codable {
    public let reply: String?           // consensus response text
    public let agreement_score: Double? // 0.0–1.0 inter-model agreement
    public let models_responded: Int?   // how many models contributed
    public let elapsed_s: Double?       // total response time in seconds
    public let ts: String?             // timestamp
}
```

## Request Format

```swift
public struct DialogRequest: Codable {
    public let text: String    // user's prompt
    public let sender: String  // always "human"
}
```

## Notes

- History is loaded from the SQL-backed `/cc/dialog` endpoint (survives backend restarts)
- The view uses a standard `ScrollViewReader` for auto-scrolling to the latest message
- Markdown is rendered using the `MarkdownUI` package with dark theme styling
