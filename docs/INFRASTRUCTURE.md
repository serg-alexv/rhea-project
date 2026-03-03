# Rhea Infrastructure Map

> Single source of truth. Updated by Rex. Read by everyone.
> Last updated: 2026-03-03

## Cloud Services

| Service | Address | Platform | Status |
|---------|---------|----------|--------|
| Tribunal API | `rhea-tribunal.fly.dev` | Fly.io (ams, 512MB, vol: rhea_data) | LIVE |
| OpenShift AI | `rhea-openshift-one-mrfeynman-dev.apps.rm3.7wse.p1.openshiftapps.com` | Red Hat OpenShift (GCP EU) | LIVE |
| Oracle VM | `???` — need IP | Oracle Cloud Free Tier | UNKNOWN |
| RHEL Basement | `???` — need IP | Physical server | PLANNED |
| Cloud Run (legacy) | `rhea-api-<hash>-ue.a.run.app` | GCP us-east | UNKNOWN |
| Atlas Frontend | via `VERCEL_URL` | Vercel | UNKNOWN |
| Railway | port 8400 | Railway.app | DORMANT |

## Databases

| DB | Type | Location | Stores | Status |
|----|------|----------|--------|--------|
| proof.db | SQLite WAL | local + Fly volume | Aletheia proofs | LIVE |
| tasks.db | SQLite WAL | local | Task queue | LIVE |
| users.db | SQLite | local + Fly volume | Auth, billing, API keys | LIVE |
| rhea.db | SQLite WAL | local + Fly volume | Sessions, radio, office | LIVE |
| CockroachDB | Distributed SQL | GCP EU-West3 (`rhea-flow`) | Workflows, billing | LIVE |
| MongoDB Atlas | Document | Atlas (`rhea` v8.0.19) | Documents, change streams | LIVE |
| Firestore | NoSQL | GCP (`rhea-office-sync`) | Proof sync | LIVE |
| Redis | In-memory | `REDIS_URL` env | Cache, SSE pub/sub | CONDITIONAL |

## LLM Providers (11)

| Provider | Tier | Status |
|----------|------|--------|
| Anthropic (Claude) | expensive, science | ACTIVE |
| OpenAI (GPT-5, o3, o4) | all tiers | FLAGGED — cybersecurity ban pending |
| Google Gemini | all tiers | ACTIVE |
| DeepSeek | cheap, reasoning | ACTIVE |
| OpenRouter | all tiers (aggregator) | ACTIVE |
| HuggingFace | free | ACTIVE |
| Azure OpenAI | all tiers | KEY NEEDED |
| Cerebras | cheap, balanced | KEY NEEDED |
| Groq | cheap, balanced | KEY NEEDED |
| GitHub Models | cheap | ACTIVE (auto-token) |
| OpenShift AI (OpenVINO) | self-hosted | LIVE |

## Network Layers

| Layer | Purpose | Status |
|-------|---------|--------|
| Tailscale | Mesh between Fly.io, Oracle, local | LIVE (DERP-14 Amsterdam) |
| Caddy | TLS reverse proxy | CONFIG READY |
| Fly.io HTTPS | Edge TLS | LIVE |
| Reticulum | Dark forest mesh | PLANNED |
| Tor + I2P | Anonymous transport | PLANNED |

## Auth & Payments

| Service | Purpose | Status |
|---------|---------|--------|
| JWT (local) | Signup/login | LIVE |
| Google OAuth | Social login | WIRED |
| Microsoft OAuth | Social login | WIRED |
| Apple Sign In | Social login | WIRED |
| Stripe | Subscriptions ($29/$99) | WIRED |
| BTCPay | BTC payments | WIRED |

## Products

| Product | Stack | Distribution | Status |
|---------|-------|-------------|--------|
| iOS (RheaPreview) | Swift, build 26, 13 tabs | TestFlight | LIVE |
| macOS (RheaPlay) | Swift, 12 panes | DMG (GitHub Release v1.0.0) | SHIPPED |
| Atlas (Web) | Next.js 14, Three.js, 11 pages | localhost:3000 / Vercel | IN PROGRESS (Orion) |
| Rust TUI | Rust | binary | DORMANT |
| rhea-memory | Python package | pip | SHIPPED (v0.1.0) |
| Landing Page | static | Fly.io `/app` | LIVE |

## Revenue Model

| Stream | Status | Notes |
|--------|--------|-------|
| Subscriptions (Stripe) | WIRED, NOT TESTED | Pro $29/mo, Enterprise $99/mo |
| BTC (BTCPay) | WIRED, NOT TESTED | Invoice webhook ready |
| Consulting | FIRST CONTACT | Daniel/Acolite, YC Spring 2025, call March 9 |
| API Keys | WIRED | 100 free credits on signup |

## SSH Access

| Server | Command | Key |
|--------|---------|-----|
| Fly.io | `fly ssh console -a rhea-tribunal` | Fly.io auth (no SSH key) |
| OpenShift | `oc login ...` then `oc rsh <pod>` | oc token |
| Oracle VM | `ssh opc@???` | `~/.ssh/id_ed25519` (uploaded) |
| RHEL Basement | `ssh ???` | `~/.ssh/id_ed25519` (uploaded) |

## Missing (fill in when available)

- [ ] Oracle VM public IP
- [ ] RHEL basement IP/hostname
- [ ] Vercel project URL
- [ ] Cloud Run final URL
- [ ] Redis host (production)
