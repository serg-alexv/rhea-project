# DIRECTIVE: TODO Crisis Panel — Required in Orion UI
**From:** Rex (Core Coordinator) | **Date:** 2026-02-26
**Priority:** P0 — User mandate

## Requirement
The live metrics controller (`scripts/live_metrics.py`) now tracks `todo_load` as a first-class metric.
When TODO load > 70% (currently 31%, threshold 210/300), it fires a `todo_crisis` wake-up trigger.

**Orion MUST expose this in the UI panel:**
1. Live TODO count with visual indicator (green/yellow/red)
2. TODO load factor as percentage bar (current/max_sustainable)
3. List of top TODOs by file, sortable and actionable
4. Ability to mark TODOs as resolved directly from UI
5. Historical trend graph (TODO count over time)

## Data Source
- `opera/metrics/live_dashboard.json` — updated by `scripts/live_metrics.py`
- `todo_load` field: `{"value": 0.31, "open_todos": 93, "max_sustainable": 300}`
- Threshold config in `scripts/live_metrics.py` HYSTERESIS dict

## Why
Human explicitly requested: "we should clearly see and control over this via the Orion's UI panel"
TODOs are the #1 contributor to D-metric overload. Visual control = faster triage.
