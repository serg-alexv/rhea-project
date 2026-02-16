# Community

## How to contribute

Rhea is built in the open. Contributions welcome in four areas:

### 1. Science validation
We make claims grounded in published research. If you find an error, a missing citation, or a stronger source — open an issue. This is the highest-value contribution.

**What helps:**
- Point to specific claims in `architecture.md` or `VISION.md`
- Link the relevant paper (DOI preferred)
- State whether the claim is wrong, incomplete, or could be stronger

### 2. Cultural research
Rhea maps daily rituals across 16+ civilizations to biological mechanisms. If you have expertise in a culture's daily structure — especially non-Western, indigenous, or historical patterns — we want to hear from you.

**What helps:**
- Documented daily rhythm patterns from specific communities
- Primary sources (ethnographic studies, historical records)
- Connections between cultural practices and circadian/autonomic biology

### 3. iOS development
The app is SwiftUI + HealthKit + SwiftData, offline-first. See `ARCHITECTURE_FREEZE.md` for the frozen folder structure and constraints.

**What helps:**
- HealthKit integration experience (HRV, sleep stages, activity)
- CoreML model packaging for on-device inference
- SwiftUI accessibility patterns for ADHD-optimized UX

### 4. Multi-model bridge
`src/rhea_bridge.py` routes across 6 providers. New provider adapters, better error handling, and cost optimization are always useful.

**What helps:**
- New provider integrations (follow the `ProviderConfig` pattern)
- Token cost tracking improvements
- Reliability patterns for multi-provider failover

## How we work

- `ops/BACKLOG.md` is the canonical task list
- `ops/virtual-office/TODAY_CAPSULE.md` shows current priorities
- `docs/decisions.md` explains why we made each architectural choice
- Git push every 30 minutes. If it's not committed, it didn't happen.

## Code of conduct

Be direct. Be specific. Cite sources. No overclaims. If you're unsure, say so — that's more useful than confidence without evidence.
