---
sidebar_position: 1
---

# Tribunal API

The Tribunal is Rhea's core feature: multi-model consensus as a service. Send a prompt, get structured agreement analysis across 2–10 AI models.

## Authentication

All mutating endpoints require authentication via one of:
- `X-API-Key` header — static admin key or billing API key (`rk_...`)
- `Authorization: Bearer <JWT>` — from `/auth/signup` + `/auth/login`
- In local dev mode (no `FLY_APP_NAME`), `dev-bypass` is accepted as an API key

## Rate Limits

- **Per minute:** 30 requests (configurable via `TRIBUNAL_RATE_LIMIT` env var)
- **Per day:** 1000 requests (configurable via `TRIBUNAL_DAILY_LIMIT` env var)
- Rate limiting is per-user (JWT) or per-key

---

## POST /tribunal

Level 1 (local analysis) or Level 2 (chairman synthesis) multi-model consensus.

### Request

```json
{
  "prompt": "Is intermittent fasting beneficial for ADHD?",
  "k": 5,
  "tier": "cheap",
  "mode": "local",
  "system": ""
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `prompt` | string | *required* | The question (1–10000 chars) |
| `k` | int | 5 | Number of models to query (2–10) |
| `tier` | string | `"cheap"` | Cost tier: `cheap`, `balanced`, `expensive`, `reasoning`, `science` |
| `mode` | string | `"local"` | `local` (L1, free analysis) or `chairman` (L2, +1 API call for synthesis) |
| `system` | string | `""` | Optional system prompt (max 2000 chars) |

### Response

```json
{
  "prompt": "Is intermittent fasting beneficial for ADHD?",
  "k": 5,
  "mode": "local",
  "elapsed_s": 3.42,
  "consensus": "Intermittent fasting may offer cognitive benefits...",
  "agreement_score": 0.78,
  "confidence": 0.66,
  "models_responded": 4,
  "models_queried": 5,
  "analysis_method": "local_statistical",
  "agreement_points": ["Cognitive benefits during fasting windows", "Blood sugar stabilization"],
  "divergence_points": ["Impact on medication absorption", "Long-term sustainability"],
  "stance_summary": {
    "positive": 3,
    "negative": 0,
    "neutral": 1,
    "mixed": 1
  },
  "responses": [
    {
      "model": "gemini-2.5-flash",
      "provider": "gemini",
      "text": "Research suggests...",
      "latency_s": 1.23,
      "tokens_used": 245,
      "error": null
    }
  ],
  "math_verification": {},
  "meta": {}
}
```

### curl Example

```bash
curl -X POST http://localhost:8400/tribunal \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-bypass" \
  -d '{
    "prompt": "What is the relationship between HRV and sleep quality?",
    "k": 3,
    "tier": "cheap",
    "mode": "chairman"
  }'
```

---

## POST /tribunal/ice

**ICE (Iterative Critique and Elaboration)** — Level 3 consensus with multiple critique rounds. Models challenge each other's answers and refine toward convergence.

### Request

```json
{
  "prompt": "Does polyvagal theory have empirical support?",
  "k": 4,
  "rounds": 2,
  "tier": "cheap",
  "chairman_tier": "balanced"
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `prompt` | string | *required* | The question (1–10000 chars) |
| `k` | int | 5 | Number of models (2–7, ICE is expensive) |
| `rounds` | int | 2 | Max critique rounds (1–5, optimal: 2–3) |
| `tier` | string | `"cheap"` | Cost tier for queries + critiques |
| `chairman_tier` | string | `"balanced"` | Cost tier for final chairman synthesis |

### Response

```json
{
  "prompt": "Does polyvagal theory have empirical support?",
  "k": 4,
  "rounds_completed": 2,
  "convergence_achieved": true,
  "elapsed_s": 12.7,
  "consensus": "Polyvagal theory has mixed empirical support...",
  "agreement_score": 0.82,
  "confidence": 0.70,
  "chairman_model": "gpt-4o",
  "analysis_method": "ice_iterative",
  "round_history": [
    {"round": 1, "agreement_score": 0.65, "critiques": 3},
    {"round": 2, "agreement_score": 0.82, "critiques": 1}
  ],
  "agreement_points": [],
  "divergence_points": [],
  "stance_summary": {},
  "math_verification": {},
  "meta": {}
}
```

### curl Example

```bash
curl -X POST http://localhost:8400/tribunal/ice \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-bypass" \
  -d '{
    "prompt": "Is melatonin supplementation safe long-term?",
    "k": 4,
    "rounds": 2
  }'
```

---

## POST /tribunal/math-verify

Verify a mathematical or scientific hypothesis using the Ruliad ontology engine and tribunal consensus.

### Request

```json
{
  "hypothesis": "The Fourier transform of a Gaussian is a Gaussian",
  "domain": "general",
  "skip_tribunal": false
}
```

### curl Example

```bash
curl -X POST http://localhost:8400/tribunal/math-verify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-bypass" \
  -d '{"hypothesis": "e^(iπ) + 1 = 0", "domain": "general"}'
```

---

## POST /dialog (Session Server)

The Rust session server provides a simpler tribunal endpoint with deterministic heuristic scoring (no real LLM calls):

### Request

```json
{
  "text": "Is coffee good for you?",
  "sender": "user"
}
```

### Response

```json
{
  "reply": "Tribunal consensus on \"Is coffee good for you?\": 74% agreement across 4 models.",
  "agreement_score": 0.74,
  "models_responded": 4,
  "elapsed_s": 0.001,
  "adversarial_note": "Moderate agreement (74%). The claim \"Is coffee good for you?\" warrants further evidence before full endorsement.",
  "confidence_adjusted": 0.629
}
```

The session server's `/dialog` endpoint uses word-count heuristics for scoring (≤3 words → 92%, 4–12 → 74%, 13+ → 45%) and includes an **adversarial layer** with a 15% skepticism discount.

---

## GET /health

Health check endpoint (no auth required).

```bash
curl http://localhost:8400/health
```

## GET /models

List available models and providers (no auth required).

```bash
curl http://localhost:8400/models
```
