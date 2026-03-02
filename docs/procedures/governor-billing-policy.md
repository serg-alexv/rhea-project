# Governor Billing Policy

Date: 2026-02-28
Owner: ORION
Status: ACTIVE

## Purpose
Define which agents are treated as `subscription` vs `api` in token governor.

## Policy File
- `opera/metrics/governor_billing_policy.json`

## Modes
- `subscription`: upper budget rail disabled, floor trajectory only.
- `api`: dual-rail enabled (budget cap + floor trajectory).

## Current Principal Override
- `rex`: subscription
- `orion`: subscription
- `gemini`: subscription
- `shared`: subscription

## Validation
```bash
python3 src/token_governor.py all
```
Check fields:
- `billing_mode`
- `upper_rail_enabled`
