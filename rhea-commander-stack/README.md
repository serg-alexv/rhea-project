# Rhea Commander Stack

Multi-model AI gateway for the Chronos Protocol. Three services, one deploy command, working URLs.

## Architecture

```
You (browser)
  │
  ├─► LobeChat        http://localhost:3210    ← chat UI
  │     │
  │     ▼
  ├─► LiteLLM Proxy   http://localhost:4000    ← unified API gateway
  │     │
  │     ├─► Anthropic  (Claude Opus/Sonnet/Haiku)
  │     ├─► Google     (Gemini Flash/Pro)
  │     ├─► OpenAI     (GPT-4o, o3-mini)
  │     ├─► DeepSeek   (Chat, Reasoner)
  │     ├─► OpenRouter (200+ models)
  │     ├─► HuggingFace (Llama, etc.)
  │     └─► Azure      (Jais 30B — when deployed)
  │
  └─► ComfyUI          http://localhost:8188    ← image generation (optional)
```

## Prerequisites

- Docker Engine 20.10+ with Compose V2
- At least ONE API key from any supported provider
- 2GB RAM minimum (lite), 8GB+ for ComfyUI

Verify Docker is ready:
```bash
docker compose version
```

## Quick Start (3 commands)

```bash
# 1. Configure API keys
./deploy.sh env

# 2. Start the stack
./deploy.sh up --lite    # LiteLLM + LobeChat (recommended first time)
./deploy.sh up           # Full stack including ComfyUI

# 3. Verify everything works
./deploy.sh test
```

## Step-by-Step Setup

### Step 1: Clone and enter directory

```bash
cd rhea-commander-stack
```

### Step 2: Run the env wizard

```bash
./deploy.sh env
```

The wizard will prompt for each API key. Press Enter to skip providers you don't have. You need at least ONE key. The cheapest option to start:

| Provider | Free tier | Key source |
|----------|-----------|------------|
| Gemini | 1500 req/day free | [aistudio.google.com](https://aistudio.google.com/apikey) |
| DeepSeek | $5 free credits | [platform.deepseek.com](https://platform.deepseek.com/api_keys) |
| HuggingFace | Free inference | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |

### Step 3: Start the stack

```bash
# Recommended: lite mode (no ComfyUI, faster startup)
./deploy.sh up --lite
```

Docker will pull images (~1.5GB for lite, ~6GB for full) and start services. First run takes 2-5 minutes depending on connection.

### Step 4: Verify

```bash
./deploy.sh test
```

This runs 5 checks:
1. LiteLLM health endpoint
2. Model list retrieval
3. LobeChat UI reachable
4. ComfyUI reachable (skipped in lite mode)
5. Live inference test via gemini-flash

### Step 5: Open in browser

After `test` passes, your working URLs:

| Service | URL | Purpose |
|---------|-----|---------|
| **LobeChat** | [http://localhost:3210](http://localhost:3210) | Chat UI — talk to any model |
| **LiteLLM API** | [http://localhost:4000](http://localhost:4000) | OpenAI-compatible API endpoint |
| **LiteLLM Dashboard** | [http://localhost:4000/ui](http://localhost:4000/ui) | Proxy admin, usage stats |
| **ComfyUI** | [http://localhost:8188](http://localhost:8188) | Image generation workflows |

Use LobeChat to chat with any configured model through a clean UI. All requests route through LiteLLM, which handles key management, fallback routing, and cost tracking.

## Using the API directly

LiteLLM exposes an OpenAI-compatible API. Use it from any tool that speaks OpenAI format:

```bash
# Chat completion
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-rhea-dev-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-flash",
    "messages": [{"role": "user", "content": "Hello from Rhea Commander"}]
  }'
```

```bash
# List available models
curl http://localhost:4000/v1/models \
  -H "Authorization: Bearer sk-rhea-dev-key"
```

```python
# Python (OpenAI SDK)
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="sk-rhea-dev-key"
)

response = client.chat.completions.create(
    model="claude-sonnet",
    messages=[{"role": "user", "content": "Rhea Commander online?"}]
)
print(response.choices[0].message.content)
```

## Available Models

| Alias | Provider | Model | Use case |
|-------|----------|-------|----------|
| `claude-opus` | Anthropic | claude-opus-4-5 | Deep reasoning, architecture |
| `claude-sonnet` | Anthropic | claude-sonnet-4-5 | Core agent tasks |
| `claude-haiku` | Anthropic | claude-haiku-4-5 | Fast, cheap tasks |
| `gemini-flash` | Google | gemini-2.0-flash | Fast delegation, free tier |
| `gemini-pro` | Google | gemini-2.5-pro | Complex analysis |
| `gpt-4o` | OpenAI | gpt-4o | Paper generation |
| `o3-mini` | OpenAI | o3-mini | Reasoning tasks |
| `deepseek-chat` | DeepSeek | deepseek-chat | Cultural perspective |
| `deepseek-reasoner` | DeepSeek | deepseek-reasoner | Chain-of-thought |
| `openrouter-auto` | OpenRouter | auto-route | Cost arbitrage |
| `hf-inference` | HuggingFace | Llama-3.1-8B | Specialized tasks |

## All deploy.sh commands

```
./deploy.sh env           Set up API keys (interactive wizard)
./deploy.sh up            Start full stack (LiteLLM + LobeChat + ComfyUI)
./deploy.sh up --lite     Start lite (LiteLLM + LobeChat only)
./deploy.sh down          Stop all services
./deploy.sh status        Show container status
./deploy.sh logs [svc]    Tail logs (optional: litellm, lobechat, comfyui)
./deploy.sh test          Run 5-point verification + show URLs
./deploy.sh nuke          Remove everything (requires 'yes' confirmation)
./deploy.sh help          Show help
```

## Troubleshooting

**ComfyUI image not found:**
The `ai-dock/comfyui` image tag may have changed. Use `--lite` to skip it, or update the image in `docker-compose.yaml` to `ghcr.io/ai-dock/comfyui:latest`.

**Port already in use:**
Edit `.env` to change ports:
```
LITELLM_PORT=4001
LOBECHAT_PORT=3211
```

**LiteLLM not starting:**
Check logs: `./deploy.sh logs litellm`
Common issue: invalid API key format in `.env`.

**LobeChat shows no models:**
LobeChat connects to LiteLLM via internal Docker network. Ensure LiteLLM is healthy first: `curl http://localhost:4000/health`

## Network & Security

- All services communicate on an isolated Docker bridge network (`rhea-net`)
- Only ports 3210, 4000, 8188 are exposed to localhost
- LiteLLM master key protects the API — change `sk-rhea-dev-key` in production
- API keys are stored in `.env` (gitignored) — never committed
- Config mounted read-only (`:ro`)

## Future: Jais Integration

Azure Marketplace listing for Jais 30B Chat (Core42) is active. Once deployed:

1. Get endpoint URL and API key from Azure AI Foundry
2. Add to `.env`:
   ```
   AZURE_API_KEY=your-key
   AZURE_API_BASE=https://your-endpoint.swedencentral.inference.ai.azure.com
   ```
3. Uncomment `jais-30b` section in `litellm_config.yaml`
4. Restart: `./deploy.sh down && ./deploy.sh up --lite`

## Final Check

After setup, these URLs should all be live:

- **http://localhost:3210** — LobeChat (your command interface)
- **http://localhost:4000** — LiteLLM API (your unified gateway)
- **http://localhost:4000/ui** — LiteLLM dashboard (admin view)
