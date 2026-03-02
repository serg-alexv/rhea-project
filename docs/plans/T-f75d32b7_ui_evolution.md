# Task T-f75d32b7 — UI Evolution (P0)

Status: done
Owner lane: ORION
Umbrella: Rhea+UI ([docs/plans/RHEA_PLUS_UI_UMBRELLA.md](RHEA_PLUS_UI_UMBRELLA.md))

## Goal
Reduce perceived complexity while preserving full system power via intent-first flow.

## Deliverables
1. Primary route map (`Quick Ask`, `Research`, `Operator`, `Investor`, `Share Ingress`).
2. Progressive disclosure rules (`L0 ask`, `L1 result`, `L2 controls`, `L3 expert`).
3. iOS entry refactor: no cockpit before first query.
4. 2-3 UI slices in Atlas/iOS with measurable impact.

## Definition of Done
- First useful action <= 2 steps on quick path.
- Advanced controls available without blocking novice flow.
- Before/after evidence + rationale documented.

## Delivered (2026-02-28)
1. Intent-first entry shell implemented:
   - `ios/RheaPreview.swiftpm/Sources/RheaPreviewApp.swift`
   - User must submit base query before cockpit tabs unlock.
2. Progressive disclosure wired into app shell:
   - `ios/RheaPreview.swiftpm/Sources/RheaPreviewApp.swift`
   - `L1`: Dialog+Team+Settings
   - `L2`: +Governor+Tasks
   - `L3`: +Atlas+Pulse
3. Runtime control in settings:
   - `ios/RheaPreview.swiftpm/Sources/SettingsView.swift`
   - Reveal-level picker and intent-gate reset.

Outcome: cockpit-first entry removed for first-contact flow.
