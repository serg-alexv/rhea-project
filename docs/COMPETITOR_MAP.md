# Rhea Competitor Map — AI Coding Tools Landscape (March 2026)

> Reference doc for competitive positioning. Updated 2026-03-03.

---

## 1. Product Matrix

| Product | Type | Stars/Users | Models | Pricing | Open Source |
|---------|------|-------------|--------|---------|-------------|
| **Rhea** | MCP server + CLI + iOS + macOS + Web | — | 31 (6 providers, 4 tiers) | Free (self-hosted) | Private |
| **Claude Code** | CLI agent | — | Opus 4.6, Sonnet 4.6, Haiku 4.5 | $20-200/mo (subscription) | Closed |
| **Cursor** | VSCode fork | — | GPT-4, Claude, custom | $20/mo Pro, $40/mo Business | Closed |
| **Kilo Code** | VSCode fork + CLI + Cloud | 16.2K | 500+ (gateway) | Free tier, $15/team, $49 KiloClaw | Open Source |
| **Continue** | VSCode/JetBrains ext | 31.6K | Any (BYOK) | Free (open source) | Apache 2.0 |
| **Verdent** | Desktop + VSCode ext | — | Multi-model | Credits system | Closed |
| **Augment Code** | VSCode ext + CLI | — | Proprietary | Enterprise | Closed |
| **Amazon Q** | IDE plugins + Kiro CLI | — | Amazon models | Free (50 agentic/mo) | Closed |
| **Windsurf** | VSCode fork | — | GPT-4, Claude | $10/mo Pro | Closed |
| **GitHub Copilot** | VSCode/JetBrains ext | — | GPT-4o, Claude | $10/mo, $39/mo Business | Closed |
| **Hyper** | Electron terminal | 44.7K | — (terminal, not AI) | Free | MIT |

---

## 2. Unique Capabilities Comparison

### 2.1 Multi-Model Consensus

| Feature | Rhea | Kilo | Continue | Cursor | Claude Code | Copilot |
|---------|------|------|----------|--------|-------------|---------|
| Query k models simultaneously | **YES (k=2-10)** | No (one at a time) | No | No | No | No |
| Agreement score | **YES (0-1 float)** | — | — | — | — | — |
| Disagreement = red flag | **YES** | — | — | — | — | — |
| Sceptic/adversarial mode | **YES** | — | — | — | — | — |
| ICE iterative critique | **YES (multi-round)** | — | — | — | — | — |
| Chairman synthesis | **YES (L2 mode)** | — | — | — | — | — |
| Ontology lenses | **YES (6 domains)** | — | — | — | — | — |

### 2.2 IDE Integration

| Feature | Rhea | Kilo | Continue | Cursor | Claude Code | Copilot |
|---------|------|------|----------|--------|-------------|---------|
| VSCode extension | No (MCP) | Fork | Extension | Fork | No (CLI) | Extension |
| JetBrains | No (MCP) | Extension | Extension | No | No | Extension |
| **Xcode 26.3 MCP** | **YES** | No | No | No | YES | No |
| CLI | YES (`rhea_code.py`) | YES | No | No | YES | No |
| iOS app | **YES (TestFlight)** | Mobile (planned) | No | No | No | No |
| macOS app | **YES (Play)** | No | No | No | No | No |
| Web dashboard | **YES (Atlas :3000)** | Web UI | No | No | No | No |
| Slack | No | YES | No | No | No | No |

### 2.3 Cloud / Remote

| Feature | Rhea | Kilo | Continue | Cursor | Claude Code |
|---------|------|------|----------|--------|-------------|
| Cloud agents | Fly.io (API) | **YES (containers)** | No | No | No |
| Auto-commit every message | No (30min push) | **YES** | No | No | No |
| Cross-device sessions | No | **YES** | No | No | No |
| Webhook triggers | No | **YES (HTTP→session)** | No | No | No |
| Isolated containers | Docker (Fly) | **YES (per-user Linux)** | No | No | No |
| Env profiles | No | **YES** | No | No | No |

### 2.4 Code Review

| Feature | Rhea | Kilo | Continue | Cursor | Claude Code | Copilot |
|---------|------|------|----------|--------|-------------|---------|
| PR review | **YES (k-model tribunal)** | YES (single model) | **YES (.continue/checks/)** | No | No | YES |
| CI integration | Planned | Webhooks | **GitHub Actions** | No | No | GitHub native |
| Multi-model review | **YES** | No | No | No | No | No |
| Disagreement detection | **YES** | No | No | No | No | No |
| Source-controlled checks | Planned | No | **YES (.continue/checks/*.md)** | No | No | No |

### 2.5 Model Routing

| Feature | Rhea | Kilo | Continue | Cursor | Claude Code |
|---------|------|------|----------|--------|-------------|
| Models available | 31 | 500+ | Any (BYOK) | ~10 | 3 (Opus/Sonnet/Haiku) |
| Tier-based routing | **YES (4 tiers)** | Auto Model | No | No | No |
| Cost optimization | **YES (cheap default)** | YES | BYOK | No | No |
| Provider fallback | YES | YES | No | No | No |
| Custom providers | YES | YES (gateway) | YES | No | No |

### 2.6 Knowledge & Memory

| Feature | Rhea | Kilo | Continue | Claude Code | Copilot |
|---------|------|------|----------|-------------|---------|
| Persistent memory | **YES (rhea-memory, proof.db)** | Context persistence | No | **YES (/memories)** | No |
| Proof chains | **YES (Aletheia)** | No | No | No | No |
| Codebase indexing | No | **YES (managed)** | YES | No | YES |
| MCP marketplace | Planned | **YES (Context7)** | No | No | No |
| Skills system | **YES (.claude/agents/)** | **YES (.kilocode/skills/)** | No | **YES (skills API)** | No |

---

## 3. Architecture Comparison

### 3.1 Rhea Architecture

```
┌─────────────────────────────────────────────────────┐
│                    CLIENTS                           │
│  iOS App ─ macOS Play ─ Atlas Web ─ CLI ─ MCP       │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              tribunal_api.py :8400                    │
│  54+ endpoints ─ JWT auth ─ /swagger ─ /redoc        │
│                                                      │
│  /tribunal ─ /tribunal/ice ─ /tribunal/sceptic       │
│  /v1/chat/completions (OpenAI compat)                │
│  /mcp (Streamable HTTP for remote MCP)               │
│  /aletheia/* ─ /office/* ─ /salon/* ─ /feed/*        │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              rhea_bridge.py                           │
│  6 providers ─ 31 models ─ 4 tiers                   │
│  Anthropic ─ OpenAI ─ Google ─ xAI ─ Mistral ─ etc  │
└─────────────────────────────────────────────────────┘
```

### 3.2 Kilo Architecture

```
┌───────────────────────────────────────────┐
│  VSCode Fork ─ JetBrains ─ CLI ─ Web     │
│  Mobile ─ Slack ─ App Builder             │
└─────────────────┬─────────────────────────┘
                  │
┌─────────────────▼─────────────────────────┐
│           Kilo Gateway                     │
│  500+ models ─ Auto Model routing          │
│  MCP marketplace ─ Code Reviewer           │
└─────────────────┬─────────────────────────┘
                  │
┌─────────────────▼─────────────────────────┐
│        Cloud Agents (Linux containers)     │
│  Auto-branch ─ Auto-commit ─ Env profiles  │
│  Webhook triggers ─ Cross-device sessions  │
└───────────────────────────────────────────┘
```

### 3.3 Continue Architecture

```
┌───────────────────────────────────┐
│  VSCode/JetBrains Extension       │
└─────────────────┬─────────────────┘
                  │
┌─────────────────▼─────────────────┐
│  .continue/config.json            │
│  BYOK (any provider)              │
│  .continue/checks/*.md            │
│  → GitHub Actions status checks   │
└───────────────────────────────────┘
```

---

## 4. Xcode Integration Landscape

| Product | Xcode Support | How |
|---------|---------------|-----|
| **Rhea** | **YES** | MCP server (stdio via xcrun mcpbridge) + Custom provider (/v1/chat/completions) |
| **Claude Agent** | **Built-in** | Native in Xcode 26.3 Intelligence settings |
| **OpenAI Codex** | **Built-in** | Native in Xcode 26.3 Intelligence settings |
| **Kilo Code** | No | — |
| **Continue** | No | — |
| **Cursor** | No (VSCode only) | — |
| **Copilot** | Xcode extension (limited) | Basic completions only |

### Xcode MCP Details

```bash
# Connect Claude Code to Xcode tools
claude mcp add --transport stdio xcode -- xcrun mcpbridge

# Connect Rhea MCP server to Claude Code
claude mcp add --transport stdio rhea -- python3 src/rhea_mcp_server.py

# Xcode custom provider (Rhea)
# Add in Xcode > Settings > Intelligence > Add a Provider
# URL: http://localhost:8400 (or https://rhea-tribunal.fly.dev)
# Endpoints: /v1/models, /v1/chat/completions

# Claude Agent config location
~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/
```

---

## 5. Anthropic Platform Ecosystem

| Feature | What It Is | Rhea Integration |
|---------|-----------|------------------|
| **Agent SDK** | Claude Code as a library (Python/TypeScript) | Could replace custom agent loop in rhea_code.py |
| **Memory Tool** | Client-side persistent /memories dir | Rhea already has rhea-memory — map to API format |
| **Web Search** | Dynamic filtering (11% boost, 24% fewer tokens) | Available in bridge queries via Claude |
| **Enterprise Skills** | Governed, audited skill deployment (max 8/request) | Tribunal checks could be a Claude Skill |
| **Remote MCP Servers** | HTTPS MCP servers in Claude API (mcp_connector) | Rhea at fly.dev/mcp — register as remote server |
| **MCP Connector** | `mcp_servers` param in Messages API | Pass rhea-tribunal.fly.dev/mcp as server URL |
| **Adaptive Thinking** | `thinking.type: "adaptive"` + effort param | Use in bridge for Opus/Sonnet 4.6 queries |
| **Vertex AI** | Claude on GCP (FedRAMP High) | Bridge already has GCP provider path |
| **Usage/Cost API** | Track API usage and costs | Wire into governor token tracking |
| **Prompt Library** | 30+ pre-made prompt templates | Integrate into salon characters |
| **Programmatic Tool Calling** | Force/disable specific tools per request | Use for controlled tribunal queries |

---

## 6. Distribution Channels

| Channel | Rhea | Kilo | Continue | Cursor |
|---------|------|------|----------|--------|
| npm/pip | `rhea-memory` (pip) | `@anthropic-ai/claude-agent-sdk` | npm | — |
| Mac App Store | Planned (Xcode Extension) | No | No | No |
| VS Code Marketplace | No | Extension | Extension | Fork |
| JetBrains Marketplace | No | Extension | Extension | No |
| TestFlight | **YES** | No | No | No |
| Homebrew | No | CLI | No | No |
| Docker/Fly.io | **YES (fly.dev)** | Cloud Agents | No | No |
| GitHub Release | **YES (v1.0.0)** | YES | YES | No |
| Remote MCP Registry | Planned | No | No | No |

---

## 7. What to Build Next (Priority Order)

### P0 — Immediate (This Week)
1. **Deploy new code to Fly.io** — /v1/chat/completions + /mcp + /swagger working
2. **Register Rhea MCP with Claude Code** — `claude mcp add --transport stdio rhea -- python3 src/rhea_mcp_server.py`
3. **Connect to Xcode MCP** — `claude mcp add --transport stdio xcode -- xcrun mcpbridge`
4. **Fix iOS app** — simulator runtime download, auth flow

### P1 — This Sprint
5. **Tribunal PR checks** — GitHub Action that runs `tribunal_pr_review` on PR diffs
6. **Register as Remote MCP** — HTTPS endpoint at fly.dev/mcp for Claude API mcp_connector
7. **Xcode custom provider** — Test /v1/chat/completions from Xcode Intelligence settings
8. **Documentation site** — External-facing docs (we have 0 pages, Play has 198)

### P2 — Next Sprint
9. **Cloud Agent** — Kilo-style isolated containers, auto-commit, webhook triggers
10. **Codebase indexing** — Managed code indexing for better context
11. **Agent SDK integration** — Replace rhea_code.py agent loop with Claude Agent SDK
12. **Skills as Claude Skills** — Register tribunal checks as Enterprise Skills

---

## 8. Moat Analysis

### What ONLY Rhea Can Do (Unique Differentiators)

1. **k-model consensus** — No competitor queries multiple models and synthesizes. Period.
2. **Disagreement detection** — When models disagree, it's a red flag. Single-model systems are blind to this.
3. **Adversarial review (Sceptic)** — Devil's advocate mode where models actively critique consensus.
4. **ICE iterative critique** — Multi-round refinement. Models improve each other's answers.
5. **Ontology lenses** — Domain-specific analysis (pharmacology, biochemistry, logic, topology, systems_biology).
6. **Aletheia proof chains** — Verified claims with evidence trails. Knowledge that accumulates.
7. **Salon multi-character** — Multiple AI personalities discussing a topic (not just Q&A).
8. **Triple-client** — iOS + macOS + Web + CLI + MCP. No competitor ships all five.

### What Competitors Do Better (Gaps to Close)

1. **Cloud agents** — Kilo's auto-commit + isolated containers + webhook triggers
2. **Distribution** — Kilo has VSCode + JetBrains + Slack + CLI + Mobile
3. **Documentation** — Play has 198 pages, we have /swagger + /redoc
4. **Codebase indexing** — Kilo + Copilot do managed indexing, we don't
5. **Model count** — Kilo has 500+ models, we have 31
6. **Community** — Kilo 16.2K stars, Continue 31.6K, we have 0
7. **CI integration** — Continue has .continue/checks/ → GitHub Actions
8. **Cross-device** — Kilo: start local → continue cloud, seamlessly

---

## 9. Reference Architectures

### 9.1 Hyper Terminal (Vercel)

| Attribute | Detail |
|-----------|--------|
| **Stars** | 44.7K |
| **License** | MIT |
| **Language** | TypeScript (98.1%) |
| **Stack** | Electron + React + Redux + xterm.js |
| **Contributors** | 268 |
| **Version** | v3.4.1 |
| **Last active commit** | 2024 (somewhat dormant) |

**Extension architecture (reference pattern for Rhea plugins):**
- Extensions = Node.js modules published to npm (`hyper` keyword)
- Config: `~/.config/Hyper/.hyper.js` — JS object with `config`, `plugins[]`, `keymaps{}`
- Plugin install dir: `~/.config/Hyper/.hyper_plugins/`
- **Composition model:** Decorate React components + Redux middleware/reducers
  - `decorateHyper`, `decorateTerm`, `decorateTab`, etc. — HOC wrappers
  - `middleware` — intercept any Redux action
  - `reduceUI`, `reduceSessions`, `reduceTermGroups` — custom reducers
  - `mapHyperState`, `mapHyperDispatch` — container mappers
- Hot reload: Cmd+R prunes require.cache, re-invokes `on*` methods
- Electron hooks: `onApp`, `onWindow`, `onUnload`, `decorateMenu`, `decorateBrowserOptions`
- **No session persistence** — needs tmux for session management
- Built-in: tabs, split panes, but no multiplexer features

**Relevant for Rhea:** The decorator/composition pattern is elegant for a plugin system. Instead of a custom API for everything, Hyper lets plugins intercept and compose existing React + Redux internals. Rhea could adopt a similar pattern for tribunal result decoration, UI component extension, or model routing overrides.

### 9.2 Agent Supervision Patterns

| Tool/Framework | Type | Key Pattern |
|---------------|------|-------------|
| **Flowstate** (Stevo Ledbetter) | Sprint framework | Markdown-based skills → wave execution → structured retros with diffs → metrics pipeline. 97% cache hit rate, 10 sprints/day. Skills > checklists for agent compliance. |
| **Clawdbot** | Self-hosted agent | Always-on Mac mini agent. Slack/WhatsApp/Telegram/Discord/iMessage. Scheduled tasks, monitoring, browsing. Permission model: access/deny/approve/autonomous. |
| **GSD (Get Shit Done)** | Claude Code framework | Planning → execution → verification. Inspired Flowstate. |
| **Gastown** (Steve Yegge) | Claude Code framework | Management tool for AI coding agents. |
| **Claude Code Tasks** | Built-in | TodoWrite → dispatch subagents → checkpoint review. |
| **Kilo Agent Manager** | VSCode panel | CLI process supervisor. Parallel Mode (git worktrees). Session resume. Cloud sync. Approval UI. |

**Key learnings for Rhea "nanny" layer:**
1. **Skills (principles) > Checklists (procedures)** — agents follow principles, skip checklists
2. **Quality gates are the review** — tests/types/lint/coverage after each wave, not manual review
3. **Structured retros with diffs** — not prose, actual file edits to approve/reject
4. **Wave-based parallelism** — haiku for mechanical, sonnet for reasoning, parallel within waves
5. **Metrics pipeline** — tokens/line, cache hit rate, gate pass rate, skill compliance score
6. **Permission model** — what agent can access, what needs approval, what's autonomous

---

*This document is a living reference. Update when researching new competitors or shipping new features.*
