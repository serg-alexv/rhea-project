<p align="center">
  <strong>R H E A</strong><br>
  <em>Multi-model consensus with verifiable proofs</em>
</p>

<p align="center">
  <a href="https://rhea-tribunal.fly.dev">Production</a> · <a href="https://testflight.apple.com/join/BNya22Jg">TestFlight</a> · <a href="https://github.com/serg-alexv/rhea-project/releases/tag/v1.0.0">v1.0.0</a> · <a href="https://rhea-tribunal-api-145767756165.europe-west1.run.app/health">EU Mirror</a>
</p>

---

You submit a claim. Multiple AI models evaluate it independently. Rhea computes agreement scores, confidence intervals, and stores verifiable proofs. No single model gets the final word.

```
"Lipinski's Rule of Five predicts oral bioavailability"
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

## Quick Start

### Unix / macOS (one command)

```bash
curl -sL https://raw.githubusercontent.com/serg-alexv/rhea-project/main/deploy/setup.sh | bash
```

Auto-detects your OS, installs Python 3.10+ if needed, creates a virtualenv, generates `.env`, initializes databases, starts the server on `:8400`. Works on Ubuntu, Debian, macOS, Alpine, Amazon Linux, Arch.

### Windows

```powershell
# 1. Install Python 3.10+ from https://python.org (check "Add to PATH")
# 2. Clone and run:
git clone https://github.com/serg-alexv/rhea-project.git
cd rhea-project
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env — add at minimum GEMINI_API_KEY (free tier: https://aistudio.google.com)
python src\tribunal_api.py
# Server on http://localhost:8400
```

### Manual (any platform)

```bash
git clone https://github.com/serg-alexv/rhea-project.git
cd rhea-project
pip install -r requirements.txt
python3 src/tribunal_api.py
# http://localhost:8400
```

### iOS

```bash
cd ios/RheaApp && xcodegen generate && open RheaApp.xcodeproj
# Build to simulator or device (iOS 17+)
```

Or join [TestFlight](https://testflight.apple.com/join/BNya22Jg).

### Atlas (Web Dashboard)

```bash
cd rhea-atlas && npm install && npm run dev
# http://localhost:3000
```

## Products

| Product | Platform | Status |
|:--------|:---------|:-------|
| **Rhea iOS** | iOS 17+ | TestFlight live — 9 tabs: Tribunal, Radio, Governor, Tasks, Atlas, Pulse, Bio, Relay, Settings |
| **Rhea Play** | macOS 13+ | [DMG in GitHub Release](https://github.com/serg-alexv/rhea-project/releases/tag/v1.0.0) — 12-pane ops centre for monitoring the agent fleet |
| **Tribunal API** | Python / Fly.io | Production — 79 route handlers, JWT auth, multi-model consensus |
| **Atlas** | Next.js | 3D web dashboard with research panel |
| **Rust CLI** | macOS arm64 | 1.5 MB native binary — health monitor + command centre |
| **rhea-memory** | Python package | pip-installable — 5-layer persistent memory for AI agents |
| **Keyboard** | iOS extension | System-wide AI text input powered by Tribunal |
| **VPN / Mesh** | iOS extension | DPI bypass (ZAPRET-style) + Tailscale mesh networking |

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
                    │  79 routes · 54+ endpoints     │
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

### Backend

| Module | Purpose |
|:-------|:--------|
| `tribunal_api.py` | Main server — consensus, dialog, sceptic, tasks, agents, feed |
| `rhea_bridge.py` | Multi-provider LLM bridge — Gemini, GitHub, OpenAI, Anthropic, Groq, DeepSeek, Cerebras, Azure, HuggingFace, OpenRouter |
| `token_governor.py` | Dual-rail token budget: subscription vs API-billed, per-agent tracking |
| `aletheia_api.py` | Proof store: submit, verify, search, dedup, ontology |
| `office.py` | Inter-agent messaging with H2O Sonnet gate |
| `task_queue.py` | Persistent task pipeline: add, claim, complete, block |
| `auth_api.py` | JWT signup/login, bcrypt passwords, Keychain-compatible tokens |

### iOS App — RheaKit

18 Swift files, cross-platform (iOS + macOS via `#if os`).

| View | What it does |
|:-----|:-------------|
| `DialogView` | Submit claims, see multi-model responses with agreement scores |
| `TeamChatView` | Live radio feed — agent-to-agent messages, ON AIR banner, 3s polling |
| `GovernorView` | Token budget dashboard — per-agent spend, daily limits, provider status |
| `TasksView` | Task queue — create, claim, complete |
| `AtlasWebView` | 3D knowledge graph via embedded WebView |
| `PulseMonitorView` | Agent heartbeat monitoring |
| `BioRendererView` | 3D molecular viewer — 3Dmol.js bundled locally, PDB + SMILES, AI molecule analysis |
| `RelayPrivacyView` | 6-layer privacy stack: HTTPS, DoH, API relay, DPI bypass, mesh, VPN |
| `DPIBypassEngine` | ZAPRET-style packet transforms — ClientHello split, Host randomize, TLS record split, fake RST, segment disorder |
| `MeshManager` | Agent mesh via TailscaleKit + self-hosted Headscale |
| `TunnelManager` | WireGuard VPN / DPI bypass tunnel control |

### Networking & Privacy

| Layer | Technology | Server Required |
|:------|:-----------|:----------------|
| DNS-over-HTTPS | Cloudflare / Google / Quad9 / Mullvad | No |
| API Relay | Encrypted proxy routing | No |
| DPI Bypass | ZAPRET tpws-style (ClientHello split, disorder, fake TTL) | No |
| Mesh Network | TailscaleKit → Headscale (self-hosted) | timelabs.ru |
| Full VPN | WireGuard via PacketTunnelProvider | timelabs.ru |

DPI bypass runs entirely in userspace — no jailbreak, no server. A local proxy in the Network Extension transforms outbound TLS packets to defeat passive DPI.

### Self-Hosted Infrastructure

```yaml
Services on timelabs.ru:
  Headscale:     port 443   — Tailscale-compatible coordination server
  DERP relay:    port 8443  — NAT traversal for firewalled clients
  WireGuard:     port 51820 — Direct tunnel endpoint
  Headscale UI:  port 9090  — Admin web panel
```

MagicDNS: `rhea.mesh` · IP range: `100.64.0.0/10`

## Model Bridge

10 providers, 42 models, 4 cost tiers. Routes queries by budget and capability.

| Tier | Models | Use Case |
|:-----|:-------|:---------|
| `cheap` | Gemini Flash, Haiku, Cerebras | Routine queries, agent chatter |
| `mid` | GPT-4o-mini, Sonnet, Mistral | Code review, structured analysis |
| `strong` | Opus, GPT-5, Gemini Pro | Tribunal consensus, complex reasoning |
| `research` | o3, Deep Research | Novel hypothesis evaluation |

## Agent Team

| Agent | Model | Role |
|:------|:------|:-----|
| Rex | Claude Opus 4.6 | Core coordinator, routing, quality gate |
| Orion | GPT-5.3 (Codex) | Frontend, strategy, Atlas development |
| Gemini | Gemini 2.5 Flash | Cheap tier operations, bulk processing |
| Hyperion | — | Infrastructure, monitoring |

Agents communicate via the Office relay system — persistent message chains, relay acknowledgments, incident tracking.

## Aletheia — Proof Store

Every consensus result can be submitted as a verifiable proof with hash chain.

```bash
# Submit
curl -X POST localhost:8400/aletheia/submit \
  -H "Content-Type: application/json" \
  -d '{"claim":"...", "evidence":"...", "source":"tribunal"}'

# Search
curl localhost:8400/aletheia/search?q=lipinski

# Verify
curl localhost:8400/aletheia/verify/ale_1709...
```

## API (selected)

| Method | Path | Description |
|:-------|:-----|:------------|
| `POST` | `/tribunal` | Multi-model consensus |
| `POST` | `/dialog` | Interactive dialog |
| `POST` | `/sceptic` | Red-team challenge |
| `GET` | `/health` | Server health + providers |
| `GET` | `/governor` | Token budget |
| `GET` | `/agents/status` | Unified agent roster |
| `GET` | `/feed/stream` | SSE real-time feed |
| `POST` | `/tasks` | Create task |
| `POST` | `/auth/signup` | Create account (JWT) |
| `POST` | `/aletheia/submit` | Submit proof |
| `GET` | `/aletheia/search` | Search proofs |
| `POST` | `/aletheia/dedup` | Deduplicate claims |
| `GET` | `/bio/lookup` | PDB molecular data |
| `POST` | `/keyboard/quick` | AI text completion |
| `POST` | `/billing/checkout` | Stripe checkout |
| `POST` | `/billing/btcpay` | BTC invoice |

79 route handlers across tribunal, dialog, sceptic, governor, tasks, agents, feed, auth, aletheia, bio, keyboard, relay, billing.

## Pricing

| Plan | Queries/mo | Models | Price |
|:-----|:-----------|:-------|:------|
| Free | 100 | 1 | $0 |
| Pro | 10,000 | 5 (consensus) | $29/mo |
| Enterprise | Unlimited | All + custom | $99/mo |

Payment: Stripe (card) or BTC (BTCPay Server).

## Decisions

16 Architecture Decision Records in [`docs/decisions.md`](docs/decisions.md) — agent consolidation, multi-model bridge, ADHD-optimized design, tiered routing, audit-trail commits.

## Project Structure

```
rhea-project/
├── src/                    # Python backend
├── packages/
│   ├── RheaKit/            # Swift framework (18 views, iOS + macOS)
│   └── rhea-memory/        # Python package (5-layer agent memory)
├── ios/
│   ├── RheaApp/            # Xcode project (xcodegen)
│   ├── RheaPreview.swiftpm/# App entry point
│   ├── RheaTunnel/         # Network Extension (DPI + VPN)
│   ├── RheaKeyboard/       # Keyboard Extension (AI text input)
│   └── Frameworks/         # TailscaleKit.xcframework
├── rhea-atlas/             # Next.js web dashboard
├── tools/                  # Rust CLIs (health monitor, command centre)
├── deploy/
│   ├── setup.sh            # Universal one-liner setup
│   └── timelabs/           # Docker Compose (Headscale + DERP + WireGuard)
├── data/                   # SQLite databases
├── scripts/                # Automation (commit, check, deploy)
├── docs/                   # ADRs, state, guides
└── vendor/
    └── libtailscale/       # TailscaleKit source (BSD-3-Clause)
```

## Numbers

| | |
|:--|:--|
| Python backend | 12,939 LOC |
| Swift (RheaKit + app) | 7,812 LOC |
| TypeScript (Atlas) | 5,510 LOC |
| Shell scripts | 5,304 LOC |
| API route handlers | 79 |
| LLM providers | 10 |
| Models available | 42 |
| Proofs in Aletheia | 11 |
| Databases | 4 |
| iOS tabs | 9 |
| Privacy layers | 6 |

## Deployments

| Surface | URL | Provider |
|:--------|:----|:---------|
| Tribunal API | [rhea-tribunal.fly.dev](https://rhea-tribunal.fly.dev) | Fly.io |
| Tribunal API (EU) | [europe-west1.run.app](https://rhea-tribunal-api-145767756165.europe-west1.run.app/health) | GCP Cloud Run |
| iOS Beta | [TestFlight](https://testflight.apple.com/join/BNya22Jg) | Apple |
| Release v1.0.0 | [GitHub](https://github.com/serg-alexv/rhea-project/releases/tag/v1.0.0) | GitHub |
| Mesh Control | headscale.timelabs.ru | timelabs.ru |

## Support

BTC: `your-btc-address-here`

All donations go toward server costs and development.

## Licenses

| Component | License | Source |
|:----------|:--------|:-------|
| Rhea | Proprietary | this repo |
| TailscaleKit / libtailscale | BSD-3-Clause | [tailscale/libtailscale](https://github.com/tailscale/libtailscale) |
| WireGuard-Go | MIT | [WireGuard/wireguard-go](https://github.com/WireGuard/wireguard-go) |
| Headscale | BSD-3-Clause | [juanfont/headscale](https://github.com/juanfont/headscale) |
| 3Dmol.js | BSD-3-Clause | [3dmol/3Dmol.js](https://github.com/3dmol/3Dmol.js) |
| GRDB.swift | MIT | [groue/GRDB.swift](https://github.com/groue/GRDB.swift) |
| KeychainAccess | MIT | [kishikawakatsumi/KeychainAccess](https://github.com/kishikawakatsumi/KeychainAccess) |
| swift-markdown-ui | MIT | [gonzalezreal/swift-markdown-ui](https://github.com/gonzalezreal/swift-markdown-ui) |
| Starscream | Apache-2.0 | [daltoniam/Starscream](https://github.com/daltoniam/Starscream) |
| swift-collections | Apache-2.0 | [apple/swift-collections](https://github.com/apple/swift-collections) |
| Pow | MIT | [EmergeTools/Pow](https://github.com/EmergeTools/Pow) |
| Ruliad Explorer | Internal | `friends/ruliad/explorer/` — Wolfram-inspired ontology engine |
| Aletheia | Internal | `friends/aletheia/` — proof store, community hypotheses |

---

<p align="center">
  <sub>
    <em>"Logic is Fluid. Evidence is Durable. The Manifold is Smooth."</em><br>
    ∇ > 0 ∨ ⊥
  </sub>
</p>

<p align="center">
  <sub>
    <a href="https://github.com/serg-alexv/rhea-project">github.com/serg-alexv/rhea-project</a><br>
    <a href="readme0.md">genesis</a> · <a href="docs/decisions.md">decisions</a> · <a href="docs/AI_COMPACT_LANG.md">protocol</a>
  </sub>
</p>

<p align="center">
  <sub><em>TimeLabs NPO</em></sub>
</p>
