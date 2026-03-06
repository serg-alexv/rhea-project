---
sidebar_position: 1
---

# Fly.io Deployment

The Tribunal API is deployed to [Fly.io](https://fly.io) as `rhea-tribunal` in the Amsterdam (AMS) region.

## fly.toml Configuration

```toml
app = "rhea-tribunal"
primary_region = "ams"

[build]
  dockerfile = "config/docker/Dockerfile.platform"

[env]
  PORT = "8400"
  PYTHONUNBUFFERED = "1"

[http_service]
  internal_port = 8400
  force_https = true
  auto_stop_machines = "suspend"
  auto_start_machines = true
  min_machines_running = 0

  [http_service.concurrency]
    type = "requests"
    hard_limit = 100
    soft_limit = 80

[[vm]]
  size = "shared-cpu-1x"
  memory = "512mb"

[mounts]
  source = "rhea_data"
  destination = "/app/data"
```

### Key Settings

| Setting | Value | Purpose |
|---------|-------|---------|
| `auto_stop_machines` | `suspend` | Suspends idle machines to save cost |
| `auto_start_machines` | `true` | Wakes on incoming request |
| `min_machines_running` | `0` | Allows full scale-to-zero |
| `force_https` | `true` | All traffic over TLS |
| `hard_limit` | 100 | Max concurrent requests per machine |
| `memory` | 512MB | Sufficient for Python + SQLite |

### Persistent Volume

The `rhea_data` volume is mounted at `/app/data` — this is where SQLite databases (`rhea.db`, `proof.db`, `auth.db`) are stored. Data survives deploys.

## Deployment Steps

### Prerequisites

```bash
# Install Fly CLI
brew install flyctl

# Authenticate
fly auth login
```

### Deploy

```bash
# From project root
fly deploy

# Or with specific config
fly deploy --config fly.toml
```

### Set Secrets

```bash
# Required
fly secrets set GEMINI_API_KEY=your-key

# Optional providers
fly secrets set OPENAI_API_KEY=sk-...
fly secrets set ANTHROPIC_API_KEY=sk-ant-...

# Auth & billing
fly secrets set JWT_SECRET=your-production-secret
fly secrets set TRIBUNAL_API_KEYS=key1,key2
fly secrets set STRIPE_SECRET_KEY=sk_live_...
fly secrets set STRIPE_WEBHOOK_SECRET=whsec_...
```

### Monitoring

```bash
# View logs
fly logs

# SSH into machine
fly ssh console

# Check status
fly status

# Scale
fly scale count 2  # run 2 machines
```

## Production URL

```
https://rhea-tribunal.fly.dev
```

Health check: `GET https://rhea-tribunal.fly.dev/health`

## Docker Entrypoint

The entrypoint script (`scripts/docker-entrypoint.sh`) handles:
1. Seeding `proof.db` from `/tmp/seed_proof.db` if the volume is empty
2. Starting uvicorn on port 8400

```bash
# Entrypoint command
uvicorn src.tribunal_api:app --host 0.0.0.0 --port 8400
```
