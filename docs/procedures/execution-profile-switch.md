# Execution Profile Switch

Global model execution profile for Rhea Bridge.

## Profiles
- `safe_cheap` — economy-first, shorter outputs, cheap-effective tier mapping.
- `balanced` — quality/cost balance.
- `deep` — depth-first, higher spend.

## API
- `GET /api/settings/execution-profile`
- `POST /api/settings/execution-profile` with body `{ "profile": "safe_cheap|balanced|deep" }`

Example:
```bash
curl -s -X POST http://localhost:8000/api/settings/execution-profile \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: dev-bypass' \
  -d '{"profile":"balanced"}'
```

## CLI
```bash
python3 src/rhea_bridge.py profile
python3 src/rhea_bridge.py profile set safe_cheap
python3 src/rhea_bridge.py profile set balanced
python3 src/rhea_bridge.py profile set deep
```

## Persistence
Active profile is persisted in:
`opera/metrics/model_execution_profile.json`

All new `RheaBridge()` instances load this profile on boot.
