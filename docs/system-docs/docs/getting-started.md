---
sidebar_position: 2
---

# Getting Started

## Prerequisites

- **Python 3.11+** with pip
- **Rust toolchain** (for frontier-gem, session-server, rhea-dash)
- **Node.js 18+** (for frontend tooling)
- At least one LLM API key (Gemini, OpenAI, Anthropic, Groq, DeepSeek, or HuggingFace)

## Quick Setup

### 1. Clone and install Python dependencies

```bash
cd rh.1
pip install -r requirements.txt
```

Key Python packages: `fastapi`, `uvicorn`, `litellm`, `pydantic`, `requests`.

### 2. Configure API keys

Create a `.env` file in the project root with at least one provider:

```bash
# Required: at least one provider
GEMINI_API_KEY=your-key-here

# Optional providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
DEEPSEEK_API_KEY=dsk-...
HF_TOKEN=hf_...

# Auth & billing (optional for local dev)
JWT_SECRET=your-jwt-secret
TRIBUNAL_API_KEYS=dev-bypass
```

### 3. Check bridge status

```bash
python3 src/rhea_bridge.py status
```

This shows which providers have valid keys and which models are available.

### 4. Start the Tribunal API

```bash
uvicorn src.tribunal_api:app --host 0.0.0.0 --port 8400
```

The API serves Swagger docs at `http://localhost:8400/swagger`.

In local dev mode (no `FLY_APP_NAME` env var), the API key `dev-bypass` is accepted automatically.

### 5. Test a tribunal query

```bash
curl -X POST http://localhost:8400/tribunal \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-bypass" \
  -d '{"prompt": "Is coffee good for you?", "k": 3}'
```

### 6. Build Rust components (optional)

```bash
# Session server
cd rhea-session-server && cargo build --release

# Frontier gem daemon
cd frontier-gem && cargo build --release

# Dashboard
cd rhea-dash && cargo build --release
```

## Project Structure

```
rh.1/
├── src/                    # Python source
│   ├── tribunal_api.py     # FastAPI main app (~6000 lines)
│   ├── rhea_bridge.py      # Multi-provider LLM bridge
│   ├── rhea_db.py          # SQLite persistence
│   ├── consensus_analyzer.py
│   ├── auth_api.py         # JWT auth + signup/login
│   └── billing.py          # Stripe/BTCPay billing
├── frontier-gem/           # Rust daemon (0.log, mDNS, clipboard)
├── rhea-session-server/    # Rust Axum session server
├── rhea-dash/              # Rust egui+wgpu dashboard
├── scripts/
│   ├── rhea_orchestrate.py # 8-agent orchestration
│   └── rhea_commit.sh      # Git commit wrapper (ADR-013)
├── ios/                    # Swift iOS app
├── config/
│   └── docker/             # Dockerfiles
├── fly.toml                # Fly.io deployment
├── docker-compose.yml      # Local/production compose
└── data/                   # SQLite databases (runtime)
```

## Next Steps

- [Architecture → Services](/docs/architecture/services) — Understand the 7-service topology
- [API → Tribunal](/docs/api/tribunal) — The core consensus endpoint
- [Components → Rhea Bridge](/docs/components/rhea-bridge) — How multi-model routing works
- [Deployment → Docker](/docs/deployment/docker) — Run the full stack locally
