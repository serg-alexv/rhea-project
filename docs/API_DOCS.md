# API Documentation — Rhea Stage 5

Generated: 2026-03-06

---

## Session Server (Port 3000)

### List Sessions
```http
GET /sessions
```
**Response:**
```json
[
  {
    "id": "uuid",
    "created_at": 1709701234,
    "message_count": 5,
    "lamport_clock": 5,
    "devices": 2
  }
]
```

### Create Session
```http
POST /sessions
Content-Type: application/json

{"character":"PROTOS"}
```
**Response:**
```json
{
  "id": "uuid",
  "created_at": 1709701234,
  "message_count": 0,
  "lamport_clock": 0,
  "devices": 0
}
```

### Get Session Detail
```http
GET /sessions/{id}
```
**Response:**
```json
{
  "session": {...},
  "messages": [
    {
      "id": "uuid",
      "created_at": 1709701234,
      "lamport_clock": 1,
      "content": "...",
      "device_id": "phone-1",
      "role": "USER"
    }
  ]
}
```

### Add Message
```http
POST /sessions/{id}/messages
Content-Type: application/json

{
  "role": "USER",
  "content": "message text",
  "device_id": "phone-1"
}
```
**Response:**
```json
{
  "id": "uuid",
  "created_at": 1709701234,
  "lamport_clock": 2,
  "content": "message text",
  "device_id": "phone-1"
}
```

---

## AI Auth (Port 3001)

### Create Challenge
```http
POST /auth/challenge
Content-Type: application/json

{"model_name":"gpt-4"}
```
**Response:**
```json
{
  "challenge_id": "uuid",
  "target_hash": "sha256hash",
  "template": "code template for solution"
}
```

### Submit Solution
```http
POST /auth/solve
Content-Type: application/json

{
  "challenge_id": "uuid",
  "solution": "code"
}
```
**Response:**
```json
{
  "valid": true,
  "token": "jwt-token"
}
```

---

## Angel Game (Port 3002)

### Evaluate Decision
```http
POST /eval/decision
Content-Type: application/json

{
  "decision_id": "uuid",
  "context": "...",
  "options": ["option1", "option2"],
  "chosen": "option1",
  "rationale": "..."
}
```
**Response:**
```json
{
  "eval_id": "uuid",
  "total_score": 8.25,
  "clarity": 9,
  "alignment": 8,
  "reversibility": 8,
  "evidence": 8
}
```

---

## BioRenderer (Port 3003)

### Copy to Clipboard
```http
POST /copy/{session_id}
Content-Type: application/json

{"figure":"base64-encoded"}
```
**Response:**
```json
{"ttl": 3600, "url": "/paste/session_id"}
```

### Paste from Clipboard
```http
GET /paste/{session_id}
```
**Response:**
```json
[
  {"figure": "base64", "created_at": 1709701234}
]
```

---

## Play Token Mapper (Port 3006)

### List Components
```http
GET /components
```
**Response:**
```json
[
  {"id": "gpt4", "name": "GPT-4", "priority": 10},
  {"id": "claude", "name": "Claude", "priority": 8}
]
```

### Create Component
```http
POST /components
Content-Type: application/json

{"id": "llama", "name": "Llama2", "priority": 6}
```

### Delete Component
```http
DELETE /components/{id}
```

### Allocate Tokens
```http
POST /allocate
Content-Type: application/json

{"budget": 1000}
```
**Response:**
```json
[
  {"id": "gpt4", "allocated": 435},
  {"id": "claude", "allocated": 348},
  {"id": "llama", "allocated": 217}
]
```

---

## Errors

All services return:
```json
{
  "error": "error message",
  "code": "ERROR_CODE"
}
```

Common status codes:
- **200**: Success
- **201**: Created
- **400**: Bad request
- **404**: Not found
- **500**: Server error

---

**For full integration examples, see:**
- `test_integration.sh` (curl examples for each service)
- `PLAY_PRODUCT_GUIDE.md` (Play Token Mapper detailed)
- `STAGE5_RELEASE.md` (Dashboard API usage)
