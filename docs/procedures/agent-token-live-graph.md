# Agent Token Live Graph

## Goal
Show a live daily visual graph of token burn per agent in the Atlas UI.

## Data Source
- Raw log: `logs/bridge_calls.jsonl`
- Each bridge call now writes:
  - `agent_id`
  - `agent_name`
  - `total_tokens`
  - `cost_usd`
  - `timestamp`

## API
- Endpoint: `GET /usage/agents?window_hours=24`
- File: `src/tribunal_api.py`
- Returns:
  - `total_calls`, `total_tokens`, `total_cost_usd`
  - `agents[]` with per-agent calls/tokens/cost and hourly token bins
  - `hourly_total_tokens[]`

## UI
- Component: `rhea-atlas/src/components/AgentTokenBurnPanel.tsx`
- Placement: Atlas left HUD panel (`HudLeft` in `rhea-atlas/src/app/page.tsx`)
- Refresh interval: every 8 seconds
- Window: 24h by default

## Notes
- Legacy log rows without agent attribution are grouped as `unknown`.
- To improve attribution in all contexts, set one of:
  - `RHEA_AGENT_ID` (preferred)
  - `RHEA_AGENT_NAME` (optional label)
