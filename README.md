# Rhea

Multi-model AI advisory system with verifiable consensus. Ships as an iOS app, macOS ops centre, web dashboard, Python API server, and Rust CLI.

**Production:** [rhea-tribunal.fly.dev](https://rhea-tribunal.fly.dev) | **TestFlight:** [Join Beta](https://testflight.apple.com/join/BNya22Jg) | **Release:** [v1.0.0](https://github.com/serg-alexv/rhea-project/releases/tag/v1.0.0)

---

## What it does

You submit a claim. Multiple AI models evaluate it independently. Rhea computes agreement scores, confidence intervals, and stores verifiable proofs. No single model gets the final word.

```
User: "Lipinski's Rule of Five predicts oral bioavailability"
         │
         ▼
┌─────────────────────────────────────────────┐
│  Tribunal (multi-model consensus engine)     │
│  ├─ Gemini 2.5 Flash  → agrees (0.82)      │
│  ├─ GPT-5.3           → agrees (0.76)      │
│  ├─ Claude Opus 4.6   → partially (0.54)   │
│  └─ Sceptic (red team) → challenge filed    │
├─────────────────────────────────────────────┤
│  Agreement: 71%  │  Confidence: 68%         │
│  Proof ID: ale_1709...  │  Stored in DB     │
└─────────────────────────────────────────────┘
```

## Products

| Product | Platform | Status | Description |
|:--------|:---------|:-------|:------------|
| **Rhea iOS** | iOS 17+ | TestFlight live | 9-tab app: Tribunal, Radio, Governor, Tasks, Atlas, Pulse, Bio, Relay, Settings |
| **Rhea Play** | macOS 13+ | DMG in GitHub Release | 12-pane ops centre for monitoring agent fleet |
| **Tribunal API** | Python/Fly.io | Production | 79 route handlers, JWT auth, multi-model consensus |
| **Atlas** | Next.js | localhost:3000 | 3D web dashboard with research panel |
| **Rust CLI** | macOS (arm64) | Installed | 1.5MB native binary at `/opt/homebrew/bin/rhea` |
| **rhea-memory** | Python package | pip-installable | 5-layer persistent memory for AI agents |
| **Keyboard** | iOS extension | Built | System-wide AI text input using Tribunal |
| **VPN/Mesh** | iOS extension | Built | DPI bypass (ZAPRET-style) + Tailscale mesh networking |

## Architecture

```
                    ┌──────────────────────────────┐
                    │      iOS / macOS App          │
                    │  (SwiftUI, RheaKit, 6K LOC)   │
                    └───────────┬──────────────────┘
                                │ HTTPS / JWT
                    ┌───────────▼──────────────────┐
                    │      Tribunal API (:8400)      │
                    │  src/tribunal_api.py (3.3K LOC) │
                    │  79 routes, 54+ endpoints      │
                    ├────────────────────────────────┤
                    │  Aletheia  │ Governor │ Office  │
                    │  (proofs)  │ (budget) │ (relay) │
                    └──────┬─────┬────┬─────────────┘
                           │     │    │
              ┌────────────▼─┐ ┌─▼────▼──────────────┐
              │ Rhea Bridge   │ │  Databases            │
              │ 10 providers  │ │  proof.db (Aletheia)  │
              │ 42 models     │ │  tasks.db             │
              │ 4 cost tiers  │ │  users.db (JWT auth)  │
              └───────────────┘ │  rhea.db              │
                                └───────────────────────┘
```

### Backend (`src/`)

| Module | LOC | Purpose |
|:-------|:----|:--------|
| `tribunal_api.py` | 3,284 | Main API server — consensus, dialog, sceptic, tasks, agents, feed |
| `rhea_bridge.py` | 1,663 | Multi-provider LLM bridge (Gemini, GitHub, OpenAI, Anthropic, Groq, DeepSeek, Cerebras, Azure, HuggingFace, OpenRouter) |
| `token_governor.py` | — | Dual-rail token budget: subscription vs API-billed, per-agent tracking |
| `aletheia_api.py` | — | Proof store: submit, verify, search, dedup, ontology |
| `office.py` | — | Inter-agent messaging with H2O Sonnet gate |
| `task_queue.py` | — | Persistent task pipeline: add, claim, complete, block |
| `auth_api.py` | — | JWT signup/login, bcrypt passwords, Keychain-compatible tokens |
| `memory_feed.py` | — | Compact memory generation with dedup |
| `rhea_bridge.py` tiers | — | `cheap` (Flash/Haiku) → `mid` (Sonnet/GPT-4o-mini) → `strong` (Opus/GPT-5) → `research` (o3/Deep Research) |

### iOS App (`packages/RheaKit/`)

18 Swift files, 6,071 LOC. Cross-platform (iOS + macOS via `#if os`).

| View | Description |
|:-----|:------------|
| `DialogView` | Tribunal query interface — submit claims, see multi-model responses |
| `TeamChatView` | Live radio feed — agent-to-agent messages, "ON AIR" banner, 3s polling |
| `GovernorView` | Token budget dashboard — per-agent spend, daily limits, provider status |
| `TasksView` | Task queue management — create, claim, complete |
| `AtlasWebView` | 3D knowledge graph via embedded WebView |
| `PulseMonitorView` | Agent heartbeat monitoring |
| `BioRendererView` | 3D molecular viewer (3Dmol.js bundled locally, RCSB PDB lookup) |
| `RelayPrivacyView` | 6-layer privacy stack: HTTPS, DoH, API relay, DPI bypass, mesh, VPN |
| `AuthView` | JWT login/signup with Keychain storage |
| `MeshManager` | Agent mesh networking via TailscaleKit + self-hosted Headscale |
| `TunnelManager` | VPN/DPI tunnel control |
| `DPIBypassEngine` | ZAPRET-style packet transforms: ClientHello split, Host case randomize, TLS record split |

### Networking & Privacy

| Layer | Technology | Server Required |
|:------|:-----------|:----------------|
| DNS-over-HTTPS | Cloudflare/Google/Quad9/Mullvad | No |
| API Relay | Encrypted proxy routing | No |
| DPI Bypass | ZAPRET tpws-style (ClientHello split, disorder, fake TTL) | No |
| Mesh Network | TailscaleKit → Headscale (self-hosted control plane) | timelabs.ru |
| Full VPN | WireGuard tunnel via PacketTunnelProvider | timelabs.ru |

DPI bypass operates without any server — it runs a local proxy in the Network Extension that transforms outbound TLS packets to defeat passive DPI.

### Self-Hosted Infrastructure (`deploy/timelabs/`)

```yaml
Services on timelabs.ru (31.177.76.32):
  Headscale:     port 443   — Tailscale-compatible coordination server
  DERP relay:    port 8443  — NAT traversal for firewalled clients
  WireGuard:     port 51820 — Direct tunnel endpoint
  Headscale UI:  port 9090  — Admin web panel
```

MagicDNS domain: `rhea.mesh` | IP range: `100.64.0.0/10`

### Aletheia (Proof Store)

11 proofs stored. Every tribunal consensus result can be submitted as a verifiable proof with hash chain.

```bash
# Submit a proof
curl -X POST localhost:8400/aletheia/submit \
  -H "Content-Type: application/json" \
  -d '{"claim":"...", "evidence":"...", "source":"tribunal"}'

# Search proofs
curl localhost:8400/aletheia/search?q=lipinski

# Verify a proof
curl localhost:8400/aletheia/verify/ale_1709...
```

## Quick Start

### Server (Python)

```bash
git clone https://github.com/serg-alexv/rhea-project.git
cd rhea-project
pip install -r requirements.txt
python3 src/tribunal_api.py
# Server on http://localhost:8400
```

### iOS App

```bash
cd ios/RheaApp
xcodegen generate
open RheaApp.xcodeproj
# Build to simulator or device (iOS 17+)
```

Or join the [TestFlight beta](https://testflight.apple.com/join/BNya22Jg).

### Atlas (Web Dashboard)

```bash
cd rhea-atlas
npm install
npm run dev
# http://localhost:3000
```

### Rust CLI

```bash
cd tools/rhea-health
cargo build --release
# Binary at target/release/rhea-health
```

### rhea-memory (Python Package)

```bash
pip install -e packages/rhea-memory
rhea-memory --help
```

## API Endpoints (selected)

| Method | Path | Description |
|:-------|:-----|:------------|
| `POST` | `/tribunal` | Submit claim for multi-model consensus |
| `POST` | `/dialog` | Interactive dialog with selected model |
| `POST` | `/sceptic` | Red-team challenge against a claim |
| `GET` | `/health` | Server health + provider status |
| `GET` | `/governor` | Token budget across all agents |
| `GET` | `/agents/status` | Unified agent roster (Governor + Office + Tasks + Radio) |
| `GET` | `/feed/stream` | SSE real-time event feed |
| `POST` | `/tasks` | Create task |
| `POST` | `/tasks/{id}/claim` | Claim a task |
| `POST` | `/auth/signup` | Create account (JWT) |
| `POST` | `/auth/login` | Get JWT token |
| `POST` | `/aletheia/submit` | Submit proof |
| `GET` | `/aletheia/search` | Search proof store |
| `POST` | `/aletheia/dedup` | Deduplicate claims |
| `GET` | `/bio/lookup` | PDB molecular data lookup |
| `POST` | `/keyboard/quick` | Quick AI text completion |

Full API: 79 route handlers across tribunal, dialog, sceptic, governor, tasks, agents, feed, auth, aletheia, bio, keyboard, relay.

## Model Bridge

10 providers, 42 models, 4 cost tiers. Routes queries based on budget and capability needs.

| Tier | Models | Cost | Use Case |
|:-----|:-------|:-----|:---------|
| `cheap` | Gemini Flash, Haiku, Cerebras | ~$0 | Routine queries, agent chatter |
| `mid` | GPT-4o-mini, Sonnet, Mistral | Low | Code review, structured analysis |
| `strong` | Opus, GPT-5, Gemini Pro | Medium | Tribunal consensus, complex reasoning |
| `research` | o3, Deep Research | High | Novel hypothesis evaluation |

## Agent Team

| Agent | Model | Role |
|:------|:------|:-----|
| Rex | Claude Opus 4.6 | Core coordinator, routing, quality gate |
| Orion | GPT-5.3 (Codex) | Frontend, strategy, Atlas development |
| Gemini | Gemini 2.5 Flash | Cheap tier operations, bulk processing |
| Hyperion | — | Infrastructure, monitoring |

Agents communicate via the Office relay system with persistent message chains, relay acknowledgments, and incident tracking.

## Decisions

16 Architecture Decision Records in [`docs/decisions.md`](docs/decisions.md):

- ADR-001: Agent consolidation 10 → 8
- ADR-002: Multi-model bridge over single provider
- ADR-003: ADHD-optimized design
- ADR-008: Tiered model routing with cheap-first default
- ADR-013: Commit via `scripts/rhea_commit.sh` (audit trail)
- ADR-014: Auto-commit strategy

## Numbers

| Metric | Value |
|:-------|:------|
| Python backend | 12,939 LOC |
| Swift (RheaKit + app) | 7,812 LOC |
| TypeScript (Atlas) | 5,510 LOC |
| Shell scripts | 5,304 LOC |
| Deploy configs | 2,500 LOC |
| Total commits | 543 |
| API route handlers | 79 |
| LLM providers | 10 |
| Models available | 42 |
| Proofs in Aletheia | 11 |
| Databases | 4 (proof.db, tasks.db, users.db, rhea.db) |
| iOS tabs | 9 |
| Privacy layers | 6 |

## Project Structure

```
rhea-project/
├── src/                    # Python backend (tribunal, bridge, governor, office, aletheia)
├── packages/
│   ├── RheaKit/            # Swift framework (18 views, shared iOS/macOS)
│   └── rhea-memory/        # Python package (5-layer agent memory)
├── ios/
│   ├── RheaApp/            # Xcode project (xcodegen)
│   ├── RheaPreview.swiftpm/# App entry point + ScreenPilot
│   ├── RheaTunnel/         # Network Extension (DPI + VPN)
│   ├── RheaKeyboard/       # Keyboard Extension (AI text input)
│   └── Frameworks/         # TailscaleKit.xcframework
├── rhea-atlas/             # Next.js web dashboard
├── tools/
│   ├── rhea-health/        # Rust CLI (health monitor)
│   └── rhea-cc/            # Rust CLI (command centre)
├── deploy/
│   └── timelabs/           # Docker Compose stack (Headscale + DERP + WireGuard)
├── data/                   # SQLite databases (proof.db, tasks.db, users.db, rhea.db)
├── scripts/                # Automation (commit, check, deploy, orchestrate)
├── docs/                   # ADRs, state, integration audit, guides
└── vendor/
    └── libtailscale/       # TailscaleKit source (BSD-3-Clause)
```

## Licenses

| Component | License |
|:----------|:--------|
| Rhea (this project) | Proprietary |
| TailscaleKit | BSD-3-Clause |
| WireGuard-Go | MIT |
| Headscale | BSD-3-Clause |
| 3Dmol.js | BSD-3-Clause |

## Links

- Production: [rhea-tribunal.fly.dev](https://rhea-tribunal.fly.dev)
- TestFlight: [testflight.apple.com/join/BNya22Jg](https://testflight.apple.com/join/BNya22Jg)
- Release: [v1.0.0](https://github.com/serg-alexv/rhea-project/releases/tag/v1.0.0)

---

> *Previous README preserved at [readme0.md](readme0.md)*
