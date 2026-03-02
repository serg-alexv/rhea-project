# Commercial Positioning — Rhea Continuity Cloud

**Value proposition**
- Unified multi-agent orchestration (Gemini, Orion, Rex, Shared) that runs across **cloud compute (Fly.io/Google Cloud)** and **desktop capture (NDI + queue guard)**, delivering live command/alert visibility in a single Governor dashboard.
- **Cloud-managed token budgets** (Gemini $2/day, Orion $5/day) tied to an executable `A0` gate and SQL-backed `tasks.db`/`office.jsonl` ledger, so customers only pay for purposeful pushes while maintaining compliance-friendly audit trails.
- Real-time **NDI/Radio sync + TestFlight distribution** ensures investors/customers watch the same terminal + agent state on mobile devices; no local manual syncing required.

**Operational snapshot**
1. **Deployable**: `deploy/vercel/deploy.sh` (frontend), `deploy/cloudrun/deploy.sh` (backend) triggered in the CICD pipeline documented in `REX_TO_ORION_20260226_REMAINING_ITEMS.md`. Fly.io runs the node apps, Redis/SQL persist the queue, and Oracle on-demand handles periodic spikes.
2. **Monitoring**: `Governor` panel shows token burn, agent health, and radio/NDI risk; `logs/bridge_calls.jsonl` records spend. Continuous `queue guard`, `flow-up`, and `continuity-smoke` scripts keep the cloud mirror in sync.
3. **Monetization hooks**: internal TestFlight (1.0(5)) ready for early-access, `apps` marketed through Apple News+ storytelling, and `Governor` dashboards can be packaged as a SaaS “Continuity Commander” offering.

**Call to action**
- Promote the dedicated cloud service (Fly.io + NDI relay + SQL audit + A0 safety) as a premium tier. Add a near-term milestone to describe the service bundle (`docs/upgrade_plan_suggestions.md`: add bullet referencing `docs/commercial_pitch.md`).
- Demonstrate continuity by deploying an App Store build (TestFlight internal testers) and using `Governor` to show tokens/resources per minute; capture this in investor updates.
