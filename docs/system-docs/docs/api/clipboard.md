---
sidebar_position: 3
---

# Clipboard API

Cross-device clipboard synchronization. Clipboard entries are persisted in SQLite with per-user isolation, TTL expiry, pinning, and real-time SSE streaming.

## Data Model

Each clipboard entry is stored with:

```sql
CREATE TABLE clipboard (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    device_id TEXT NOT NULL DEFAULT '',
    device_name TEXT DEFAULT '',
    content_type TEXT NOT NULL DEFAULT 'text',
    content TEXT NOT NULL,
    content_preview TEXT,
    content_hash TEXT,
    privacy TEXT DEFAULT 'normal',
    ttl_seconds INTEGER,
    pinned INTEGER DEFAULT 0,
    source_app TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    expires_at TEXT
);
```

---

## POST /clipboard

Push content to the clipboard.

### Request

```json
{
  "content": "Hello from my phone",
  "content_type": "text",
  "device_id": "iphone-14-pro",
  "device_name": "My iPhone",
  "ttl_seconds": 86400,
  "privacy": "normal"
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `content` | string | *required* | The clipboard content |
| `content_type` | string | `"text"` | MIME-like type: `text`, `url`, `code`, `image` |
| `device_id` | string | `""` | Source device identifier |
| `device_name` | string | `""` | Human-readable device name |
| `ttl_seconds` | int | `null` | Time-to-live in seconds (null = no expiry) |
| `privacy` | string | `"normal"` | Privacy level: `normal`, `sensitive`, `secret` |

### Response

```json
{
  "id": "clip_abc123",
  "status": "ok",
  "created_at": "2025-01-15T10:30:00Z"
}
```

### curl Example

```bash
curl -X POST http://localhost:8400/clipboard \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-bypass" \
  -d '{"content": "Test clipboard entry", "device_id": "laptop"}'
```

---

## GET /clipboard

Retrieve clipboard history for the authenticated user.

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 50 | Max entries to return |
| `device_id` | string | — | Filter by device |

### Response

```json
[
  {
    "id": "clip_abc123",
    "content": "Hello from my phone",
    "content_type": "text",
    "device_id": "iphone-14-pro",
    "device_name": "My iPhone",
    "pinned": false,
    "created_at": "2025-01-15T10:30:00Z"
  }
]
```

### curl Example

```bash
curl http://localhost:8400/clipboard \
  -H "X-API-Key: dev-bypass"
```

---

## GET /clipboard/stream

**SSE (Server-Sent Events)** stream of real-time clipboard updates. Connect once, receive pushes whenever any device adds a clipboard entry.

### curl Example

```bash
curl -N http://localhost:8400/clipboard/stream \
  -H "X-API-Key: dev-bypass"
```

Returns an SSE stream:
```
data: {"id":"clip_abc123","content":"New entry","device_id":"phone"}

data: {"id":"clip_def456","content":"Another entry","device_id":"laptop"}
```

**Note:** The frontier-gem clipboard proxy (`/api/clipboard/*`) does NOT support SSE streaming yet — connect directly to the Tribunal API for SSE.

---

## DELETE /clipboard/:clip_id

Delete a specific clipboard entry.

```bash
curl -X DELETE http://localhost:8400/clipboard/clip_abc123 \
  -H "X-API-Key: dev-bypass"
```

---

## DELETE /clipboard

Clear all clipboard entries for the authenticated user.

```bash
curl -X DELETE http://localhost:8400/clipboard \
  -H "X-API-Key: dev-bypass"
```

---

## POST /clipboard/:clip_id/pin

Pin a clipboard entry (prevents TTL expiry, keeps at top).

```bash
curl -X POST http://localhost:8400/clipboard/clip_abc123/pin \
  -H "X-API-Key: dev-bypass"
```

---

## POST /clipboard/:clip_id/unpin

Unpin a clipboard entry.

```bash
curl -X POST http://localhost:8400/clipboard/clip_abc123/unpin \
  -H "X-API-Key: dev-bypass"
```

---

## frontier-gem Proxy

The frontier-gem daemon proxies clipboard requests to the Tribunal API on Fly.dev:

- `POST /api/clipboard` → forwards to upstream
- `GET /api/clipboard` → forwards to upstream
- `GET /api/clipboard/stream` → returns 501 (SSE proxy not yet implemented)

The upstream URL defaults to `https://rhea-tribunal.fly.dev` and can be overridden with the `RHEA_SERVER` env var. Auth is forwarded via `RHEA_AUTH_TOKEN`.
