---
sidebar_position: 4
title: ClipboardView
---

# ClipboardView

A cross-device clipboard manager. Sync text, URLs, and code snippets between devices via the Rhea backend with support for pinning, expiry, and privacy levels.

## Usage

```swift
import RheaKit

struct ClipboardTab: View {
    var body: some View {
        ClipboardView()
    }
}
```

## Features

- **Push to cloud** — Send local clipboard contents to `POST /clipboard`
- **Pull to device** — Tap any clip to copy it to the local pasteboard
- **Auto-polling** — Refreshes every 5 seconds for near-real-time sync
- **Pin/unpin** — Keep important clips from being cleared
- **Privacy levels** — Normal, sensitive (🔒), and secret (🔐) clips
- **Content types** — Text, URL, code, and image with distinct icons
- **Expiry** — Clips can have expiration timestamps
- **Swipe to delete** — Standard iOS swipe-to-delete gesture
- **Pull to refresh** — Standard refresh gesture

## Data Model

```swift
struct ClipEntry: Identifiable, Codable {
    let id: String
    let content: String
    let contentType: String        // "text", "url", "code", "image"
    let contentPreview: String?    // preview for secret clips
    let deviceName: String         // originating device
    let privacy: String            // "normal", "sensitive", "secret"
    let pinned: Bool
    let createdAt: String          // ISO 8601
    let expiresAt: String?         // optional expiry
}
```

## Privacy Levels

| Level | Badge | Behavior |
|---|---|---|
| `normal` | — | Full content visible and copyable |
| `sensitive` | 🔒 | Content visible but marked |
| `secret` | 🔐 | Only `contentPreview` shown; tap-to-copy disabled |

## API Endpoints

| Action | Method | Endpoint |
|---|---|---|
| List clips | `GET` | `/clipboard` |
| Push clip | `POST` | `/clipboard` |
| Delete clip | `DELETE` | `/clipboard/:id` |
| Pin clip | `POST` | `/clipboard/:id/pin` |
| Unpin clip | `POST` | `/clipboard/:id/unpin` |
| Clear all | `DELETE` | `/clipboard` |

## Status Bar

The top status bar shows connection state (green/red dot with CONNECTED/OFFLINE label) and the current device name.

## Notes

- The device name is auto-detected: `UIDevice.current.name` on iOS, `Host.current().localizedName` on macOS
- Authentication uses `AuthManager.shared.token` (JWT Bearer) with fallback to `dev-bypass` API key
- URL content is auto-detected by checking if the text starts with `http`
