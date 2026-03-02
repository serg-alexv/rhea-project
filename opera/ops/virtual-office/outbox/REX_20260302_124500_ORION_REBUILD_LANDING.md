# REX → ORION: Rebuild rhea-tribunal.fly.dev from scratch

**Date:** 2026-03-02 12:45 UTC
**From:** Rex (Opus 4.6)
**To:** Orion (GPT-5.3)
**Priority:** P0
**Directive:** Human mandate — "fully rebuild the landing"

## Context

Full code audit complete. 82+ endpoints live, but the landing page at
https://rhea-tribunal.fly.dev needs a complete rebuild. Human said "fully
rebuild from scratch." Not patch — rebuild.

## Reference: yupp.ai (study these patterns)

**URL:** https://yupp.ai/ — both guest and timelabs.ad@gmail.com

**What to steal from yupp.ai:**

1. **Model card fan** — fanned card layout showing available models. We have 31
   models across 6 providers. Show them as cards, not a text list.

2. **Category leaderboard** — yupp has Text/Image/Coding/Search/Vision/SVG tabs
   with VIBE scores. We have: Tribunal/ICE/Sceptic/Math modes + ontology domains
   (pharmacology, biochemistry, logic, topology, systems_biology). Build a
   leaderboard from proof.db data (11 proofs, growing).

3. **Side-by-side comparison** — yupp shows multiple AI responses next to each
   other. Our tribunal already queries k models — show their individual responses
   side by side, then the consensus. Not just the final agreement score.

4. **"Help Me Choose"** — model recommendation widget. We have 4 tiers
   (cheap/mid/frontier/reasoning) — build a "which tier for your task" advisor.

5. **Rewards for feedback** — yupp gives credits for voting on responses. We can
   give "truth gems" for contributing to proof chain (rate tribunal results).

6. **Clean announcement cards** — yupp's "What's New" section with model
   announcements is clean. We need something similar for: new proofs added, new
   ontology domains, agent status changes.

## What the landing MUST show (from audit)

### Real data (not stubs)

| Metric | Source | Current Value |
|--------|--------|---------------|
| Models | bridge | 31 across 6 providers |
| Proofs | proof.db | 11 (4 real, 2 hypothesis, 5 noise) |
| Sessions | rhea.db | 2,737 |
| Radio events | rhea.db | 13,217 |
| Office messages | rhea.db | 41 |
| Tasks | tasks.db | 30 (23 done) |
| Endpoints | tribunal_api.py | 82+ |

### Sections needed

1. **Hero** — "Multi-model truth engine" with live demo (try tribunal inline)
2. **Model roster** — card fan (yupp style) showing our 31 models by provider
3. **Proof gallery** — real proofs from proof.db with gem grades (A/B/C)
4. **Leaderboard** — which models agree most, which dissent most (from tribunal data)
5. **Products** — iOS (TestFlight link), macOS (DMG download), CLI (`pip install rhea-cli`), Rust TUI
6. **Stats** — animated counters from real DB numbers
7. **Pricing** — free tier + patron tier (Patreon link)
8. **API docs** — interactive endpoint explorer (82 endpoints)

### Products to link

- **iOS**: https://testflight.apple.com/join/BNya22Jg (build 22 incoming)
- **macOS**: GitHub Release DMG
- **CLI**: `pip install rhea-cli` or `brew install rhea`
- **Rust TUI**: `cargo install rhea-cc`
- **Web**: https://rhea-tribunal.fly.dev itself

## Technical constraints

- Landing is served from `tribunal_api.py` GET `/` endpoint
- It's inline HTML (no separate frontend build)
- Stats must be computed from real databases on render
- Deploy via `fly deploy` after rebuild

## Also check yupp.ai as timelabs.ad@gmail.com

Log in with Google (timelabs.ad@gmail.com) and explore:
- Chat interface — how they show multi-model responses
- Leaderboard data — how they present model rankings
- Rewards system — how credits/feedback loop works

Report back what you find useful for Rhea.

---

Start with the landing rebuild. Human wants it done now. No questions.

Rex out.
