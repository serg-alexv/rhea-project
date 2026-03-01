# Rhea Competitive Landscape Report — March 2026

Research date: 2026-03-01. Focus: iOS App Store competitors across Rhea's functional surface area.

---

## 1. OpenClaw Ecosystem (Open-Source AI Assistant)

OpenClaw (formerly Clawdbot/Moltbot) is Rhea's most direct structural competitor: open-source, multi-model, agent-based, local-first memory (Markdown files), autonomous scheduling via heartbeat daemon. Launched late January 2026, 100K+ GitHub stars in under a week. MIT license.

**Core product**: Free software. Costs = your API keys + hosting ($0-13/mo personal, $25-50/mo business).

**iOS companion apps** (third-party, not official):

| App | Developer | Price | Rating | Model |
|-----|-----------|-------|--------|-------|
| GoClaw | Apphive Io | Free + IAP ($10-90 plans, credit packs $3-40) | 3.6/5 (17 ratings) | Freemium + credits |
| Majordomo | Toggle Media | Free trial 7d, then $39.99/mo | No ratings yet | SaaS subscription |
| OpenClaw Messenger | DeepWork Technologies | Free (companion for OCLauncher) | N/A | Companion app |

**Key OpenClaw features**: 50+ integrations (WhatsApp, Telegram, Slack, Discord, iMessage, Signal), 100+ AgentSkills, shell commands, browser automation, file management, calendar, email. Model-agnostic (bring your own keys or run local).

**Gap for Rhea**: OpenClaw has no tribunal/consensus pattern. It routes to ONE model at a time. No chronobiology layer. No cost-tier routing. No built-in verification pipeline. The companion apps are thin wrappers — Majordomo at $40/mo for hosted OpenClaw is pure margin on commodity infra.

---

## 2. AI Keyboard Extensions

The "AI in every text field" market. Relevant because Rhea's advisory surface could manifest as a keyboard extension.

| App | Rating | Reviews | Pricing | Key Differentiator |
|-----|--------|---------|---------|-------------------|
| TypeAI | 4.7/5 | 19,592 | Free + $4.99-7.99/mo, $69.99 lifetime | Chatbot + keyboard combo, 7 languages |
| CleverType | 4.0/5 | 78 | Free + $4.99-59.99 tiers | 30+ AI tools, 40+ languages, tone control |
| Grammarly Keyboard | ~4.5/5 | 100K+ | Free basic, $12.99/mo premium | Brand recognition, enterprise trust |
| Gboard | ~4.5/5 | massive | Free (data-harvested) | Google ecosystem, zero cost, data mining |
| Fleksy | ~4.2/5 | moderate | $4.99/mo or $29.99/yr | Accessibility focus, extreme customization |
| SwiftKey | ~4.5/5 | massive | Free (Microsoft ecosystem) | Predictive text, cloud sync |

**Market pattern**: Free tier with crippled AI + subscription $5-13/mo for "unlimited." TypeAI's $70 lifetime is the outlier — clever for user acquisition but unsustainable at scale.

**Gap for Rhea**: None of these keyboards consult multiple models. None have domain-specific expertise (chronobiology, control theory). None offer a tribunal/verification layer. A Rhea keyboard extension that routes through the bridge (cheap tier for autocorrect, escalate to consensus for important messages) would be unique. The "AI keyboard that actually fact-checks itself" positioning is unoccupied.

---

## 3. Bio/Molecular Viewer Apps

Relevant because Rhea's chronobiology domain intersects molecular visualization (circadian protein structures, receptor binding).

| App | Rating | Reviews | Price | Status |
|-----|--------|---------|-------|--------|
| Molecules | 3.6/5 | 164 | Free | Open source (BSD), Swift+Metal rewrite, RCSB/PubChem integration |
| BioViewer | 1.0/5 | 1 (3 reviews) | Free | Open source, Metal renderer, but MIRROR IMAGE BUG (structures render backwards) |
| iMolview | ~3.5/5 | moderate | Free (Lite) / Paid (full) | PDB/DrugBank/PubChem, rich representations |
| 3D Molecules View&Edit | ~4.0/5 | low | Free (Lite) | Builder + viewer, SDF/PDB support |
| Mol* (web) | N/A | N/A | Free | RCSB's official viewer, browser-based, no native iOS app |
| Molecular Constructor | ~4.0/5 | low | Free | 3D builder with geometry optimization |

**Market pattern**: Almost everything is free or open-source. Academic niche with no monetization. BioViewer has a critical accuracy bug that a biology professor flagged (mirror-image rendering). Mol* is web-only — no native iOS presence despite being RCSB's official tool.

**Gap for Rhea**: Zero apps combine molecular visualization with AI advisory. "Show me the circadian clock protein PER2 and explain how light affects its conformation" — no app does this. A Rhea module that wraps Mol*/PDB data with LLM-powered explanation + chronobiology context would be a category creator, not a competitor.

---

## 4. AI-Powered VPN / Privacy Tools

Relevant because Rhea's architecture is privacy-first (local memory, own API keys) and the user mentioned Bebra VPN specifically.

| App | Rating | Reviews | Pricing | AI Features |
|-----|--------|---------|---------|-------------|
| Bebra VPN | 4.7/5 | 1,004 | 3-day trial, then $9.99/mo / $39.99/6mo / $59.99/yr | Shadowsocks-based, "AI" in domain name (bebra.ai) but minimal AI features |
| NordVPN | ~4.7/5 | 500K+ | $3.39-5/mo (annual/2yr) | Threat Protection Pro (ML-driven malware/phishing blocking), adaptive encryption |
| Proton VPN | ~4.6/5 | 100K+ | Free tier, $4.99/mo paid | Open source, Swiss jurisdiction, no AI claims |
| Apple Private Relay | built-in | N/A | Included in iCloud+ ($0.99/mo+) | Dual-hop relay, limited to Safari |

**Market pattern**: VPN is a race to the bottom on price. "AI-powered" is mostly marketing — NordVPN's threat detection is the only substantive AI feature. Bebra is a small Russian-origin VPN (KONDAKOV&GORIN LLC) using Shadowsocks with AI branding but no visible AI functionality beyond the domain name.

**Gap for Rhea**: Rhea is not a VPN and should not become one. However, the privacy-first architecture (local memory, BYOK, no cloud dependency) is a genuine differentiator against cloud-dependent AI apps. "Your AI advisor that never phones home" is a positioning statement that none of the multi-model aggregators can honestly make.

---

## 5. Multi-Model AI Advisor / Consensus Apps

Rhea's primary competitive category. Apps that query multiple LLMs and synthesize answers.

| Platform | iOS App | Pricing | Models | Consensus Method |
|----------|---------|---------|--------|-----------------|
| Poe (Quora) | Yes, 4.7/5, 53.7K ratings | Free + $5/mo (basic) or $19.99/mo / $199.99/yr | GPT, Claude, Gemini, Mistral, + 1M custom bots | Side-by-side comparison, no formal consensus |
| Council AI | Web only | Unknown (likely freemium) | 30+ models (GPT, Claude, Gemini, Mistral, DeepSeek, Qwen, Grok) | Consensus scoring across all models |
| AISCouncil | Web only | Free to start (free models via OpenRouter + Gemini) | Claude, GPT, Grok, Gemini, 300+ via OpenRouter | 7 modes: Council, Compare, Debate, Mixture of Agents, Smart Router, Consensus Vote, Arena |
| Aymo AI | Web (possibly mobile) | Free + from $4/mo | 45+ models | Aggregation, no formal tribunal |
| TypingMind | Web (PWA only) | One-time $39-79 (no subscription) | Any via API keys | BYOK, no consensus — single model per chat |
| LLM Council (Karpathy) | GitHub only | Free (open source) | Any | 3-stage: Individual Response, Peer Review, Chairman synthesis |
| Perplexity Model Council | In Perplexity app | $20/mo Pro | Multiple (internal routing) | Internal model council for answer verification |

**Market pattern**: The consensus/tribunal concept is emerging but fragmented. Council AI and AISCouncil are web-only with no native iOS presence. Poe dominates mobile (53K ratings, 4.7 stars) but has NO consensus mechanism — it's a model switcher, not a tribunal. Karpathy's LLM Council proved the concept but is a CLI tool, not a product. Perplexity's Model Council is the closest to Rhea's tribunal but is a black box inside their product, not user-configurable.

**Gap for Rhea**: MASSIVE. No iOS app combines:
1. Multi-model tribunal with configurable consensus thresholds
2. Cost-tier routing (cheap for simple queries, escalate for critical ones)
3. Domain expertise (chronobiology, control theory)
4. Local-first privacy (no cloud dependency for memory)
5. Agent orchestration visible to the user (not a black box)

---

## Strategic Summary: Where Rhea Fits

### The Landscape in One Sentence
OpenClaw owns "free open-source AI assistant," Poe owns "all models in one app," and everyone else is fighting over keyboard extensions and VPN subscriptions — but NOBODY owns "AI tribunal that verifies its own answers."

### Free/Open-Source vs Paid SaaS

| Category | Free/OSS Leaders | Paid SaaS Leaders |
|----------|-----------------|-------------------|
| AI Assistant | OpenClaw (MIT), LLM Council (OSS) | Majordomo ($40/mo), Poe ($20/mo) |
| AI Keyboard | Gboard, SwiftKey | Grammarly ($13/mo), TypeAI ($5-8/mo) |
| Molecular Viewer | Molecules (BSD), BioViewer (OSS), Mol* (OSS) | iMolview (paid tier) |
| VPN/Privacy | Proton VPN (free tier) | NordVPN ($3-5/mo), Bebra ($10/mo) |
| Multi-Model Consensus | AISCouncil (free start), Karpathy LLM Council | Council AI, Perplexity Pro ($20/mo) |

### Subscription Traps to Avoid
1. **Credit-based pricing** (GoClaw's $3-40 credit packs): opaque, unpredictable costs. Users hate it.
2. **$40/mo for hosted commodity** (Majordomo): pure infrastructure margin, easily undercut.
3. **Free-to-crippled** (most AI keyboards): free tier is deliberately broken to force upgrade. Breeds resentment.
4. **Annual lock-in** (Bebra $60/yr, Poe $200/yr): discount bait that reduces churn through sunk cost, not value.

### Gaps Rhea Can Exploit

1. **Tribunal-as-a-Feature**: No iOS app lets the user SEE multiple models disagree and reach consensus. Rhea's Governor/Pulse/Radio views already visualize this. Ship it.

2. **Cost-Transparent Multi-Model**: Every aggregator hides costs behind subscriptions. Rhea's 4-tier bridge with visible per-query cost would be the first "honest AI billing" on iOS.

3. **Domain-Expert AI on Mobile**: Zero apps combine molecular/biological domain knowledge with LLM advisory. "Chronobiology AI advisor" is an empty category.

4. **Privacy-First Positioning**: OpenClaw is local-first but requires self-hosting. Poe/Council AI are cloud-only. Rhea's hybrid (local memory + selective cloud queries) is the middle ground nobody occupies on iOS.

5. **Agent Transparency**: Poe has 1M bots but they're black boxes. Rhea's agent roster (Rex, Orion, Gemini, Hyperion) with visible status, heartbeats, and inter-agent communication is unprecedented in a consumer app.

6. **One-Time Purchase**: TypingMind proved one-time pricing works ($39-79, BYOK). Apply this to a tribunal app: pay once, bring your own API keys, no subscription. The anti-Poe positioning.

### Recommended Positioning
**"The AI app that argues with itself before answering you."**
- Not another chatbot. Not another model aggregator. A visible deliberation process.
- Free tier: 2 models, basic consensus. Paid: full tribunal, all tiers, agent transparency.
- BYOK option for power users (TypingMind proved this market exists).
- Chronobiology domain pack as premium differentiator (no competition whatsoever).

---

*Sources: App Store listings, web research, product pages. All pricing and ratings current as of March 2026.*
