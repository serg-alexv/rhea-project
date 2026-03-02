<p align="center">
  <strong>R H E A</strong><br>
  <em>Multi-model consensus with verifiable proofs</em>
</p>

<p align="center">
  <a href="https://rhea-tribunal.fly.dev">Try it</a> · <a href="https://testflight.apple.com/join/BNya22Jg">iOS Beta</a> · <a href="https://github.com/timelabs/rhea-project/releases/tag/v1.0.0">v1.0.0</a> · <a href="https://rhea-tribunal-api-145767756165.europe-west1.run.app/health">EU Mirror</a>
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

## Install

### Server (one command)

```bash
curl -sL https://raw.githubusercontent.com/timelabs/rhea-project/main/deploy/setup.sh | bash
```

Works on macOS, Ubuntu, Debian, Alpine, Amazon Linux, Arch. Auto-detects your OS, installs Python 3.10+ if needed, creates a virtualenv, generates `.env`, starts the server on `:8400`.

### Server (manual)

```bash
git clone https://github.com/timelabs/rhea-project.git
cd rhea-project
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — add at minimum GEMINI_API_KEY (free: https://aistudio.google.com)
python3 src/tribunal_api.py
# http://localhost:8400
```

<details>
<summary>Windows</summary>

```powershell
git clone https://github.com/timelabs/rhea-project.git
cd rhea-project
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env — add GEMINI_API_KEY
python src\tribunal_api.py
```
</details>

### Memory package (standalone)

```bash
pip install rhea-memory
```

Zero-dependency persistent memory for AI agents. [Package docs →](packages/rhea-memory/README.md)

## Use it

### Submit a claim for consensus

```bash
curl -X POST http://localhost:8400/tribunal \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{"prompt": "Aspirin inhibits COX-2 selectively"}'
```

Returns agreement score, confidence interval, individual model votes, and a proof ID.

### Red-team a claim

```bash
curl -X POST http://localhost:8400/sceptic \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{"prompt": "CRISPR has no off-target effects"}'
```

The sceptic actively tries to disprove the claim.

### Store a proof

```bash
curl -X POST http://localhost:8400/aletheia/submit \
  -H "Content-Type: application/json" \
  -d '{"claim": "...", "evidence": "...", "source": "tribunal"}'
```

Every consensus result gets a hash-chained proof you can verify later.

### Create an account

```bash
curl -X POST http://localhost:8400/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "your-password"}'
```

Returns a JWT token for authenticated API access.

## What's in the box

| Component | What it does |
|:----------|:-------------|
| **Tribunal API** | Python server — multi-model consensus, red-team sceptic, proof store, JWT auth |
| **rhea-memory** | `pip install rhea-memory` — persistent memory for AI agents (MIT, zero deps) |
| **iOS app** | SwiftUI — 9 tabs: tribunal, radio, governor, tasks, atlas, pulse, bio, relay, settings |
| **Command Centre** | macOS — 3-column ops centre with menu bar widget |
| **Atlas** | Next.js — 3D web dashboard |
| **Model bridge** | 10 providers, 42 models, 4 cost tiers (cheap → research) |

## API at a glance

| Method | Path | What it does |
|:-------|:-----|:-------------|
| `POST` | `/tribunal` | Multi-model consensus |
| `POST` | `/sceptic` | Red-team challenge |
| `POST` | `/dialog` | Interactive dialog |
| `POST` | `/auth/signup` | Create account |
| `POST` | `/auth/login` | Get JWT token |
| `GET` | `/health` | Server status |
| `GET` | `/governor` | Token budget |
| `GET` | `/agents/status` | Agent roster |
| `GET` | `/feed/stream` | SSE real-time feed |
| `POST` | `/aletheia/submit` | Submit proof |
| `GET` | `/aletheia/search` | Search proofs |

Full API: 79 route handlers. See [`docs/`](docs/) for architecture, decisions, and guides.

## Architecture decisions

16 ADRs document every major choice. Here are the ones that matter most:

| # | Decision | Why |
|:--|:---------|:----|
| 002 | Multi-model bridge over single provider | No vendor lock-in, consensus requires diversity |
| 003 | ADHD-optimized design | Real users have real constraints — UI must respect attention |
| 008 | Cheap-first model routing | Default to $0.001/query, escalate only when needed |
| 009 | Cost-aware agents | Every agent tracks its own spend |
| 010 | Memory budget + discomfort metric | Agents self-improve when context gets expensive |

Full list: [`docs/decisions.md`](docs/decisions.md)

## Project structure

```
rhea-project/
├── src/                    # Python backend (tribunal, bridge, governor, auth)
├── packages/
│   ├── RheaKit/            # Swift framework (iOS + macOS views)
│   └── rhea-memory/        # pip-installable memory layer (MIT)
├── ios/                    # Xcode project, extensions (tunnel, keyboard)
├── rhea-atlas/             # Next.js dashboard
├── tools/                  # Rust CLI
├── deploy/                 # setup.sh, Docker Compose, infra
├── docs/                   # ADRs, architecture, guides
└── scripts/                # Automation
```

## Contributing

```bash
git clone https://github.com/timelabs/rhea-project.git
cd rhea-project
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 src/tribunal_api.py
# Server on :8400 — make changes, test, submit PR
```

## License

MIT. See [LICENSE](LICENSE).

All third-party dependencies carry compatible licenses (MIT, BSD-3-Clause, Apache-2.0). See [`docs/licenses.md`](docs/) for the full dependency table.

---

<p align="center">
  <sub>
    <em>"Logic is Fluid. Evidence is Durable. The Manifold is Smooth."</em><br>
    ∇ > 0 ∨ ⊥
  </sub>
</p>

<p align="center">
  <sub>
    <a href="https://github.com/timelabs/rhea-project">github.com/timelabs/rhea-project</a><br>
    <a href="readme0.md">genesis</a> · <a href="docs/decisions.md">decisions</a> · <a href="docs/AI_COMPACT_LANG.md">protocol</a>
  </sub>
</p>

<p align="center">
  <sub><em>timelabs npo</em></sub>
</p>
