# Cloud Operation Guide

This note captures the operational steps that keep Rhea running as a cloud-managed, scalable, revenue-ready platform.

## 1. Infrastructure inventory
- **Compute**: Fly.io hosts the Next.js frontend (`rhea-atlas`) and the `tribunal_api.py` runtime. Deploys via `deploy/vercel/deploy.sh` (frontend) and `deploy/cloudrun/deploy.sh` (backend) per the relay noted in `REX_TO_ORION_20260226_REMAINING_ITEMS.md`.
- **Persistence**: Redis (connected via `redis_url` env) stores fast state and pub/sub notifications; `data/tasks.db` (SQLite WAL) and `opera/ops/virtual-office/*` keep the durable audit trail.
- **Broadcast/Media**: NDI bridge (`.rhea/ndi`) streams desktop content; queue guard and radio logs ensure no buffer overflow. Cloud relay (firehose) can replay the same feed from Fly/Google.
- **AI agents**: Gemini, Orion (Claude), Rex (Claude Opus), Shared (common) run through `scripts/rhea.sh` commands (`flow`, `continuity`, `continuity-smoke`, `ndi`, `queue`). `bridge_calls.jsonl` tracks token spend.
- **Billing**: Fly.io + Apple Developer balances are funded; `Governor` UI surfaces daily budgets (`docs/governor_ui.md` in progress).

## 2. Control/Scaling playbook
1. **Startup**: Run `./scripts/rhea.sh flow` to start the coordinated multi-agent process, then `flow-guard` to validate invariants. Use `axiom check`/`check-fleet` to verify A0 gate before sending production pushes.
2. **Monitoring**: `scripts/rhea.sh queue status` plus `queue_guard` ensures WAL sizes remain reasonable; `radio` and `ndi` scripts keep notifications and screen capture loops healthy. Use the Governor panel to watch token burn vs budget (Gemini $2/day, Orion $5/day, shared $1/day, etc.).
3. **Autoscaling**: Offload heavy agents to Google Cloud/Oracle by pointing their `RHEA_API_URL` to the cloud relay endpoint; embed the `continuity-smoke` mirror for reliability testing.
4. **Failure handling**: If agents hit the `PAUSE` sentinel or the radio log shows `risk=critical`, run `./scripts/rhea.sh pause`, inspect `opera/ops/virtual-office/shared/LEARNING_FEED.md`, then `resume` once races are cleared.
5. **Onboarding new agents**: Create entries in `docs/agent_profiles.md` (planned) listing responsibilities; ensure the agent is declared in `AXIOM_A0_CONTROLLED_SENDERS` before linking to the `office` bus.

## 3. Revenue & commercialization hints
- **TestFlight**: keep build 1.0(5) assigned to Internal Testing; confirm invites (e.g., `blidetfh@yandex.ru`) and gather logs/screenshots for investor proof.
- **Governor dashboard**: highlight token budgets, broadcast costs, and uptime in the `Governor` UI with `on track`/`risk` statuses for sale pitches.
- **Documentation**: Spread the above playbook into `README.md` (quick start, selling points) and `docs/upgrade_plan_suggestions.md` (Go-to-market steps). Provide copy describing “cloud-managed, multi-agent orchestration with NDI broadcast + SQL WAL continuity” for marketing materials.
- **Metrics**: log token spend per build, radio/NDI uptime, and invite completions in `logs/patrol_A.log` / `patrol_B.log` so sales can show reliability stats.

## 4. Next backlog items
- Finish `docs/agent_profiles.md` and fold into the onboarding script. (Tied to question about five background agents.)
- Automate `TestFlight` invite confirmation and screenshot capture; log to `opera/ops/virtual-office/outbox/ORION_*_STATUS.md` for investor proof.
- Launch `Governor`/`Atlas` view for Apple News/AI news; include cloud feed summary in the `Radio` channel.
