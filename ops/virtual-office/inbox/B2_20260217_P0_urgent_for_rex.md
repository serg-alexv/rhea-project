# P0 URGENT — FROM HUMAN VIA B2
## To: Rex (LEAD)
## Date: 2026-02-17T08:05:00Z
## Priority: P0 — IMMEDIATE

### 1. Anthropic 400 errors = QUOTA CAP, not bugs
- Error: "400 exceeded daily token limit until 2026-02-18 00:00 UTC"
- **STOP all retry loops.** Retries burn remaining budget.
- Implement provider fallback: OpenAI → Gemini → local
- Hard token budget: `max_tokens <= 512`, `k <= 3`
- Disable ICE and all high-effort consensus until quota resets

### 2. SECRETS DETECTED IN LOGS — P0 SECURITY
- `GEMINI_API_KEY` and `ANTHROPIC_AUTH_TOKEN` found in output
- Add redaction filter in ALL logging (bridge_calls.jsonl, tribunal_api_calls.jsonl, Firebase writes)
- Ensure NO secrets are EVER written to Firestore
- Firestore security rules currently **OPEN** — tighten immediately
- Pattern: any string matching `AIza*`, `sk-ant-*`, `sk-*` must be redacted before logging

### 3. Firestore rules fix needed
Current rules allow any authenticated read/write. Restrict to:
- Only service account can write
- Read: only authenticated agents with matching desk ID
- No public access
