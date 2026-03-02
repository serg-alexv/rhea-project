# Rhea iOS UI Simplify Protocols

## Objective
Reduce cognitive load in Rhea iOS by enforcing progressive disclosure through:
1. Intent-first entry
2. Adaptive reveal of complexity
3. Maximum 3 user actions per step

## Scope
- Platform: Rhea iOS app
- Surfaces: launch flow, primary task flows, analysis/detail views
- Out of scope: backend API contract changes, non-iOS platforms

## Protocol v1.0

### 1) Intent-First Screen (required)
Every major flow must start with an intent selector screen before exposing controls.

Rules:
1. Show 3-5 intent cards max.
2. Each card must contain:
- Verb-led label (example: "Review Signals", "Run Analysis", "Share Findings")
- One-line consequence ("Takes about 2 min", "Uses latest synced data")
3. No advanced settings on this screen.
4. If a user has a recent repeated intent, pin one "Continue last task" option at top.
5. First tap must transition into a guided step flow in <= 300 ms local UI response.

### 2) Step Contract: Max 3 Actions
Each step in a flow can expose at most 3 direct actions.

Definitions:
- Step: one visible state where user chooses before progressing.
- Action: any tappable control that changes state or navigates.

Rules:
1. Per step, allow:
- 1 primary action
- Up to 2 secondary actions
2. Additional controls go behind a single "More options" disclosure.
3. Never show more than 3 actionable controls above the fold.
4. Gesture-only hidden actions do not bypass this rule.
5. Disable rather than hide primary action when prerequisites are missing; show inline reason.

Enforcement:
- Design QA checklist must include action count audit per step.
- UI test snapshot audit must fail if `visible_action_count > 3`.

### 3) Adaptive Reveal Model
Complexity is revealed in three levels and only when needed.

Levels:
1. L1 Essential: minimum fields and one clear next action.
2. L2 Contextual: helper data, alternatives, and safe customization.
3. L3 Expert: advanced settings, diagnostics, and overrides.

Reveal triggers:
1. Explicit user request:
- Tap "More options"
- Tap "Show details"
2. Friction trigger:
- User dwell > 8 seconds on current step without action
- User performs 2 consecutive validation errors on same step
3. Experience trigger:
- User completes same flow successfully 3+ times in past 14 days

Reveal rules:
1. Default to L1 for new users and first run of each flow version.
2. Escalate only one level at a time (L1 -> L2 -> L3).
3. Persist user-selected level per flow for 30 days.
4. Provide "Simplify this screen" control whenever level is above L1.
5. Never auto-escalate to L3 solely from dwell time.

### 4) Content and Layout Guardrails
1. One goal per screen title. No compound titles.
2. Max 2 lines of explanatory copy before first action.
3. Group supporting information under collapsible sections.
4. Keep destructive actions out of primary slot unless flow is explicitly destructive.
5. Use progressive labels:
- L1: plain language
- L2: plain language + context
- L3: technical terminology allowed

### 5) Instrumentation (mandatory)
Emit these events for every covered flow:
1. `intent_screen_viewed`
2. `intent_selected`
3. `step_viewed` (with `step_id`, `reveal_level`, `visible_action_count`)
4. `step_action_tapped`
5. `step_validation_error`
6. `reveal_level_changed` (source: explicit, friction, experience)
7. `flow_completed`
8. `flow_abandoned`

Required event fields:
- `user_id_hash`
- `flow_id`
- `step_id`
- `reveal_level`
- `visible_action_count`
- `time_since_step_view_ms`

## Acceptance Criteria (Pass/Fail)

### A. Structural Compliance
1. 100% of audited flows start with an intent-first screen.
2. 100% of audited steps have `visible_action_count <= 3`.
3. 100% of audited flows implement L1/L2/L3 reveal levels.

Measurement:
- Audit sample: top 8 iOS flows by traffic
- Method: UI test snapshots + manual design QA checklist

### B. Cognitive Load Outcome Metrics
Baseline window:
- 14 days pre-rollout median for each metric.

Targets after rollout (7-day trailing window):
1. Time to first meaningful action: improve by >= 25%.
2. Flow abandonment rate: reduce by >= 20%.
3. Backtrack rate (back navigation per completed flow): reduce by >= 20%.
4. Validation error rate per session: reduce by >= 15%.
5. Completion rate of top 5 flows: improve by >= 10%.

Guardrail metrics:
1. Crash-free sessions must not drop below baseline - 0.2%.
2. P95 step transition latency must remain <= 400 ms.

Pass condition:
- All Structural Compliance criteria pass.
- At least 4 of 5 Cognitive Load Outcome targets pass.
- Both guardrails pass.

## 7-Day Rollout Plan

### Day 1 - Baseline and Audit
1. Instrument missing telemetry events.
2. Capture 14-day baseline for target metrics.
3. Audit top 8 flows for action counts and intent-entry presence.
Deliverable:
- Baseline dashboard and flow audit sheet.

### Day 2 - Intent-First IA and Step Mapping
1. Define intent taxonomy for top 8 flows.
2. Map each flow into explicit steps and count actions per step.
3. Mark overflow controls for "More options".
Deliverable:
- Approved flow map with step-action budgets.

### Day 3 - Build Intent-First Screens
1. Implement intent-first screens for top 5 flows behind feature flag `ui_simplify_v1`.
2. Add "Continue last task" for repeated intents.
3. Wire analytics events for intent selection and step entry.
Deliverable:
- Working flagged build with telemetry.

### Day 4 - Build Adaptive Reveal
1. Implement L1/L2/L3 components and one-level-at-a-time escalation.
2. Add triggers for explicit, friction, and experience-based reveal.
3. Persist reveal preference for 30 days.
Deliverable:
- Adaptive reveal active in flagged flows.

### Day 5 - Enforce Max-3 and QA
1. Add automated assertion for `visible_action_count <= 3`.
2. Run snapshot/UI tests for top 8 flows.
3. Fix violations and regression bugs.
Deliverable:
- Green test report and zero known max-3 violations.

### Day 6 - Limited Release
1. Enable `ui_simplify_v1` for 20% of iOS users.
2. Monitor outcome and guardrail metrics every 4 hours.
3. Roll back flag immediately if guardrail breached.
Deliverable:
- Interim metric readout and incident log (if any).

### Day 7 - Decision Gate and Expansion
1. Evaluate pass/fail criteria.
2. If passed, expand to 100% of iOS users.
3. If failed, keep at 20%, open remediation tickets, and schedule 3-day fix loop.
Deliverable:
- Rollout decision memo with metric table and next actions.

## Governance
1. Any new iOS flow must include an intent-first entry and step-action audit before release.
2. Any exception to max-3 requires documented waiver with rationale and expiry date.
3. Re-run compliance audit bi-weekly for top traffic flows.
