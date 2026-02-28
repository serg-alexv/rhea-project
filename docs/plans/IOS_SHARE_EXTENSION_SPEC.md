# iOS Share Extension Implementation Spec
Date: 2026-02-28  
Owner: ORION (UI lane)  
Status: Ready for implementation

## 1. Objective

Add a native iOS Share Extension so `Rhea` appears in the iOS Share Sheet and can send compact screenshot/text payloads to Rhea relay endpoints.

Primary outcome:
1. Share from Photos/Safari/Notes/Files -> choose `Rhea` -> select receiver (`shared` or specific agent) -> payload reaches Office relay and appears in feed/history.

## 2. Scope

In scope:
1. New iOS Share Extension target in `ios/RheaApp`.
2. Share Sheet ingestion for image and text.
3. Payload compaction and upload to relay endpoints.
4. Shared config (API base URL, API key, defaults) between app and extension.
5. Security hardening requirements for transport, auth, and local data handling.
6. Failure handling + retry/outbox behavior.
7. Test matrix for unit/integration/manual validation.

Out of scope:
1. Replacing Office backend message model.
2. Multi-image album upload in V1.
3. Video/audio share in V1.

## 3. Existing Backend Contract (Current State)

Current relay endpoints in `src/tribunal_api.py`:
1. `POST /office/send_shot` for image+note payload.
2. `POST /office/send` for text-only payload.
3. `POST /office/broadcast` exists but is not required for V1 because `/office/send_shot` already supports broadcast via receiver.

Important current behavior:
1. `/office/send_shot` rejects decoded image payloads > `2_500_000` bytes (413).
2. `/office/send_shot` supports direct mode and broadcast mode (`receiver` in `ALL|BROADCAST|*`).
3. `/office/send_shot` stores media under `opera/media/shots/YYYY-MM-DD/...`.
4. `/office/send_shot` returns `shot_id`, `sha1`, `media_path`, and mode-specific fields.
5. `X-API-Key` auth exists globally but is not currently attached to these two Office routes.

## 4. Required Architecture

### 4.1 Targets

Add new target:
1. `RheaShareExtension` (Share Extension, extension point `com.apple.share-services`).

Existing target:
1. `RheaApp` remains host app.

### 4.2 Proposed file map

Under `ios/RheaApp`:
1. `ShareExtension/ShareViewController.swift`
2. `ShareExtension/ShareView.swift` (SwiftUI UI embedded in controller)
3. `ShareExtension/ShareUploadClient.swift`
4. `ShareExtension/SharePayloadBuilder.swift`
5. `ShareExtension/ShareModels.swift`
6. `ShareExtension/Info.plist`
7. `ShareExtension/RheaShareExtension.entitlements`
8. `RheaApp/RheaApp.entitlements` (or existing app entitlements file, if already present)

Project config:
1. Update `ios/RheaApp/project.yml` to declare extension target, embed it, and configure entitlements.

Shared settings (host app + extension):
1. Add a shared config helper in SwiftPM sources (or shared source folder) for App Group defaults access.

## 5. Data Flow

### 5.1 Image or Screenshot Share Path

1. User shares an image from any app and selects `Rhea`.
2. Extension reads `NSExtensionContext` attachments (`UTType.image`).
3. Extension normalizes image to JPEG:
1. Strip metadata (EXIF/GPS).
2. Resize long edge to max `1600px`.
3. Quality-compress to target <= `1.8MB` (hard cap `2.3MB` before base64).
4. Extension collects optional text from shared item and/or user note.
5. Extension builds request for `POST {apiBaseURL}/office/send_shot`:
1. `sender = "human"` (or configured alias).
2. `receiver = selected receiver` (`shared`, `rex`, `orion`, `hyperion`, `gemini`, `all`).
3. `note = compact text`.
4. `image_b64 = base64(jpeg data)`.
5. `mime = "image/jpeg"`.
6. `filename = source-derived or "share.jpg"`.
6. Upload via `URLSession` with timeout 12s.
7. On 2xx:
1. Parse `shot_id`, `mode`, `office_id?`, `media_path`, `sha1`.
2. Show success state and close extension.
8. On failure:
1. Map to explicit error state.
2. Offer retry.
3. Optionally persist pending payload to shared outbox for host-app retry.

### 5.2 Text-only Share Path

1. User shares text/URL without image.
2. Extension extracts plain text and normalizes whitespace.
3. Extension sends `POST {apiBaseURL}/office/send`:
1. `sender`
2. `receiver`
3. `text` (prefixed with `[SHARE]` marker in V1 for feed visibility)
4. Handle response success/failure as above.

### 5.3 Optional Shared Outbox Path (recommended)

If upload fails due to network/timeout:
1. Serialize pending share JSON to App Group container (`pending-shares/`).
2. Host app drains queue on launch/foreground.
3. Drainer retries with exponential backoff and deletes on success.

## 6. Entitlements and iOS Configuration

### 6.1 App Group (required)

Enable for both host app and extension:
1. `com.apple.security.application-groups`
2. Group identifier example: `group.com.rhea.preview.shared`

Use App Group for:
1. Shared defaults (`apiBaseURL`, receiver defaults, sender alias).
2. Optional outbox queue.

### 6.2 Keychain Sharing (required for production key handling)

Enable for both targets:
1. `keychain-access-groups`

Store API key in shared keychain, not in source or plist.

### 6.3 Extension Info.plist (required)

Set:
1. `NSExtensionPointIdentifier = com.apple.share-services`
2. Activation rules for:
1. `NSExtensionActivationSupportsImageWithMaxCount = 1`
2. `NSExtensionActivationSupportsText = true`
3. Optional URL support for Safari shares

### 6.4 ATS / networking

1. Debug may allow local-network HTTP for localhost/LAN testing.
2. Release must require HTTPS endpoints.
3. Certificate validation must remain enabled (no trust bypass).

## 7. Security Specification

### 7.1 Transport + auth

1. All extension requests send `X-API-Key`.
2. Add client headers:
1. `X-Rhea-Client: ios-share-extension/1.0`
2. `X-Rhea-Request-Id: <uuid>`
3. Backend requirement: attach auth/rate-limit dependencies to:
1. `POST /office/send`
2. `POST /office/send_shot`

### 7.2 Secret handling

1. No hardcoded production API key in app or extension code.
2. `dev-bypass` allowed only for local debug profile.
3. Key reads must come from shared keychain accessor.

### 7.3 Payload privacy

1. Strip image metadata before upload.
2. Do not persist raw image unless queued for retry.
3. If queued, encrypt-at-rest in App Group container (or use protected file mode + short TTL).
4. Redact API key and base64 payload from logs.

### 7.4 Receiver validation

Client-side receiver allowlist:
1. `shared`
2. `rex`
3. `orion`
4. `hyperion`
5. `gemini`
6. `all`

Reject unknown receiver values locally before request.

## 8. API Contract (V1)

Base URL:
1. `apiBaseURL` from shared settings (`http://localhost:8400` simulator default, LAN URL on device in debug).

Headers:
1. `Content-Type: application/json`
2. `X-API-Key: <key>`
3. `X-Rhea-Client: ios-share-extension/1.0`
4. `X-Rhea-Request-Id: <uuid>`

### 8.1 `POST /office/send_shot`

Request JSON:
```json
{
  "sender": "human",
  "receiver": "shared",
  "note": "optional compact note",
  "image_b64": "<base64-or-data-url>",
  "mime": "image/jpeg",
  "filename": "share.jpg"
}
```

Success (direct):
```json
{
  "status": "ok",
  "mode": "direct",
  "office_id": "msg-...",
  "shot_id": "shot-...",
  "receiver": "orion",
  "media_path": "opera/media/shots/2026-02-28/shot-....jpg",
  "size_bytes": 183204,
  "mime": "image/jpeg",
  "sha1": "abc123...",
  "ts": "2026-02-28T20:00:00Z"
}
```

Success (broadcast):
```json
{
  "status": "ok",
  "mode": "broadcast",
  "shot_id": "shot-...",
  "media_path": "opera/media/shots/2026-02-28/shot-....jpg",
  "size_bytes": 183204,
  "mime": "image/jpeg",
  "sha1": "abc123...",
  "sent": 4
}
```

Errors to handle:
1. `400` invalid base64 / data URL.
2. `400` empty image payload.
3. `401` invalid/missing API key (after backend hardening).
4. `413` image too large.
5. `429` rate limit.
6. `5xx` backend error.

### 8.2 `POST /office/send`

Request JSON:
```json
{
  "sender": "human",
  "receiver": "shared",
  "text": "[SHARE] compact text payload"
}
```

Success JSON (current backend shape):
1. Includes `id`, `sender`, `receiver`, `compressed`, `response`, token/cost fields, and `ts`.

Errors to handle:
1. `401` invalid/missing API key (after hardening).
2. `429` rate limit.
3. `5xx` backend error.

## 9. Failure States and UX Behavior

### 9.1 Extension-level failures

1. Attachment parse fails:
1. Show `Unsupported share item`.
2. Allow cancel.
2. Image compression fails:
1. Show `Could not prepare image`.
2. Suggest sharing smaller image.
3. Payload still >2.5MB after compression:
1. Show `Image too large after compression`.
2. Offer text-only fallback send.

### 9.2 Network/API failures

1. Timeout/offline:
1. Show `Network unavailable`.
2. Offer `Retry` and `Save for app retry`.
2. `401`:
1. Show `Authentication required`.
2. Deep-link to app settings to refresh API key.
3. `413`:
1. Show `Payload too large`.
2. Retry once with lower quality before surfacing failure.
4. `429`:
1. Show `Rate limited`.
2. Auto-retry with backoff (2s, 4s, max 2 retries).
5. `5xx`:
1. Show `Relay temporarily unavailable`.
2. Queue for later retry if user accepts.

### 9.3 Extension lifecycle constraints

1. Sending state must complete within extension execution limits.
2. If extension is dismissed mid-send, use queued outbox path to avoid silent loss.
3. Keep peak memory bounded by downsampling before decoding full-size images.

## 10. Test Matrix

### 10.1 Unit tests (Share extension target)

1. Image compactor:
1. PNG/JPEG/HEIC input -> JPEG output.
2. EXIF removed.
3. Size under threshold.
2. Payload builder:
1. `send_shot` JSON schema.
2. `send` JSON schema.
3. Receiver validation rejects unknown values.
3. Error mapper:
1. HTTP status -> user-visible failure reason.

### 10.2 Integration tests

1. Local backend (`src/tribunal_api.py`) with valid key:
1. Image share direct -> returns `mode=direct`.
2. Image share broadcast -> returns `mode=broadcast`.
3. Text share -> relay message accepted.
2. Negative paths:
1. Bad key -> 401.
2. Oversized image -> 413.
3. Forced 429 and 500 handling.

### 10.3 Manual QA matrix

| Case | Input | Receiver | Network | Expected |
|---|---|---|---|---|
| M1 | Photo (JPEG) | `orion` | good | 2xx direct, success UI |
| M2 | Screenshot (PNG) | `shared` | good | compressed + 2xx direct |
| M3 | Text from Notes | `shared` | good | `/office/send` success |
| M4 | URL from Safari + note | `rex` | good | text payload sent |
| M5 | Image near limit | `gemini` | good | retry compress then success |
| M6 | Oversized image | `shared` | good | fail with size message |
| M7 | Any payload | `all` | good | broadcast response with `sent` |
| M8 | Any payload | `orion` | offline | retry or queued outbox |
| M9 | Any payload | `orion` | good + bad key | auth error UX |
| M10 | Any payload | `orion` | good + 429 | backoff then final status |

Device/OS coverage:
1. iOS 17.x and 18.x.
2. iPhone (small + large screen).
3. iPad share sheet presentation.

## 11. Implementation Sequence

1. Backend hardening (required first):
1. Add auth/rate-limit dependencies to `/office/send` and `/office/send_shot`.
2. Confirm `X-API-Key` required in non-dev.
2. iOS project wiring:
1. Add extension target and plist/entitlements in `project.yml`.
2. Regenerate Xcode project.
3. Shared config:
1. App Group defaults + shared keychain helper.
2. Settings screen writes shared values for extension.
4. Extension core:
1. Attachment parsing.
2. Compaction pipeline.
3. Upload client and response handling.
5. Outbox retry (recommended):
1. Queue pending shares on failure.
2. Host app drainer.
6. QA + test matrix execution.

## 12. Definition of Done

1. `Rhea` appears in iOS Share Sheet for image and text sources.
2. Image shares reach `/office/send_shot` and return `shot_id`.
3. Text-only shares reach `/office/send`.
4. Auth is enforced on relay endpoints.
5. No API keys committed in repo.
6. Failure states map to explicit user-visible outcomes.
7. Test matrix passes for all P0 cases (`M1` to `M8` minimum).
