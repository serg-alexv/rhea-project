---
sidebar_position: 2
---

# Docker

Run the full Rhea stack locally with Docker Compose: the API server + Caddy reverse proxy with auto-TLS.

## Quick Start

```bash
# Create .env with at minimum one provider
cat > .env << 'EOF'
GEMINI_API_KEY=your-key-here
JWT_SECRET=local-dev-secret-change-in-prod
DOMAIN=localhost
EOF

# Start the stack
docker compose up -d

# Check health
curl http://localhost:80/health
```

## docker-compose.yml

The compose file defines two services:

### API Service

```yaml
services:
  api:
    build:
      context: .
      dockerfile: config/docker/Dockerfile.platform
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY:-}
      - STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET:-}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - TRIBUNAL_API_KEYS=${TRIBUNAL_API_KEYS:-}
      - FLY_APP_NAME=docker
    volumes:
      - rhea-data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8400/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
```

Setting `FLY_APP_NAME=docker` disables the `dev-bypass` API key — production behavior even locally.

### Caddy Service

```yaml
  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/Caddyfile:/etc/caddy/Caddyfile
      - caddy-data:/data
      - caddy-config:/config
    environment:
      - DOMAIN=${DOMAIN:-localhost}
    depends_on:
      api:
        condition: service_healthy
    restart: unless-stopped
```

Caddy provides automatic HTTPS certificates when `DOMAIN` is set to a real domain.

## Dockerfile

The production Dockerfile (`config/docker/Dockerfile.platform`):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System deps + Tailscale for mesh networking
RUN apt-get update && apt-get install -y --no-install-recommends \
        libzmq3-dev curl iptables \
    && curl -fsSL https://tailscale.com/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application source
COPY src/ ./src/
COPY opera/ ./opera/
COPY prompts/ ./prompts/
COPY friends/ ./friends/

ENV PYTHONPATH="/app/src:/app/friends/ruliad/explorer:/app"

RUN mkdir -p /app/logs /app/data

# Seed proof.db
COPY data/proof.db /tmp/seed_proof.db
COPY scripts/docker-entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8400
CMD ["/app/entrypoint.sh"]
```

### Notable Details

- **Tailscale** is included for mesh networking between Fly.io machines
- **PYTHONPATH** includes both `src/` and the Ruliad math engine
- **proof.db** is seeded from a static copy if the data volume is empty
- Layer caching: `requirements.txt` is copied and installed before source code

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes (at least one provider) | Google Gemini API key |
| `JWT_SECRET` | For auth | JWT signing secret |
| `STRIPE_SECRET_KEY` | For billing | Stripe API key |
| `STRIPE_WEBHOOK_SECRET` | For billing | Stripe webhook verification |
| `STRIPE_PRO_PRICE_ID` | For billing | Stripe Price ID for Pro plan |
| `STRIPE_ENTERPRISE_PRICE_ID` | For billing | Stripe Price ID for Enterprise plan |
| `BTCPAY_WEBHOOK_SECRET` | For crypto billing | BTCPay Server HMAC key |
| `ANTHROPIC_API_KEY` | Optional | Anthropic Claude API key |
| `OPENAI_API_KEY` | Optional | OpenAI API key |
| `TRIBUNAL_API_KEYS` | Recommended | Comma-separated admin API keys |
| `DOMAIN` | For TLS | Domain for Caddy auto-TLS |
| `MONGODB_URL` | Optional | MongoDB connection for change streams |
| `REDIS_URL` | Optional | Redis for LiteLLM response caching |

## Volumes

```yaml
volumes:
  rhea-data:      # SQLite databases (rhea.db, auth.db, proof.db)
  caddy-data:     # TLS certificates
  caddy-config:   # Caddy configuration
```

## Building Manually

```bash
# Build the API image
docker build -f config/docker/Dockerfile.platform -t rhea-api .

# Run standalone (no Caddy)
docker run -p 8400:8400 \
  -e GEMINI_API_KEY=your-key \
  -e JWT_SECRET=dev-secret \
  -v rhea-data:/app/data \
  rhea-api
```
