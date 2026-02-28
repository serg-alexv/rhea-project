# Rhea+UI Umbrella (2026-02-28)

Status: active  
Owner: ORION (UI lane), Rex-first execution alignment  
Scope: iOS app + Atlas surfaces + relay/radio visibility

## Why this umbrella exists

Rhea is already powerful, but first-contact UX still exposes too much system complexity before user intent is clear.
The new umbrella makes one rule explicit:

`No cockpit before intent.`

User gives a base query first, then UI reveals only the next useful layer.

## Product constraints (non-negotiable)

1. First screen asks for intent, not system controls.
2. Advanced controls are available, but progressively revealed.
3. Every reveal step must reduce cognitive load, not add conceptual debt.
4. Every critical action has observable evidence (`seq/ack/status`) in UI.
5. Complexity must be discoverable on demand, never forced upfront.

## Primary routes (unique value protocols)

1. `Quick Ask` (guest/new user):
   Input query -> one useful answer -> optional "expand controls".
2. `Research Protocol` (scientist):
   Query -> hypothesis frame -> evidence sources -> deep tools.
3. `Operator Control` (team lead):
   Query -> live state -> queue/radio/actions.
4. `Investor Visibility`:
   Query -> progress proof (`task`, `ack`, `eta`) -> escalation controls.
5. `Share Ingress` (mobile OS):
   Share screenshot -> choose agent/broadcast -> compact evidence in feed.

## Workstreams

W1. Intent-first adaptive shell (P0)  
- Replace cockpit-first entry with query-first gate.
- Reveal panels only after first meaningful input.

W2. Progressive disclosure engine (P0)  
- Define reveal levels: `L0 ask`, `L1 result`, `L2 controls`, `L3 expert`.
- Add deterministic rules for when each level appears.

W3. Native iOS Share Sheet ingress (P0)  
- `Rhea` appears in iOS share list.
- Share image/text directly to selected agent or broadcast.

W4. Verifiable execution HUD (P1)  
- Show `seq`, `ack`, and last delivery status in UI for sent messages.
- Separate "delivered" from "human reply" to avoid ambiguity.

W5. Role presets (P1)  
- Presets: `biochemist`, `operator`, `investor`.
- Preset controls visibility defaults; user can still override.

W6. Use-case playbook (P0/P1)  
- Real scenarios: intent -> minimal steps -> expected value -> evidence check.

## 72h execution slice

1. Ship intent-first entry state in iOS (`L0/L1`) and keep existing tabs behind reveal.
2. Ship native Share Sheet path to `/office/send_shot`.
3. Add visible delivery proof (`seq/ack`) for outgoing messages.
4. Publish first 10 practical use-case examples linked from app/docs.

## Success metrics

1. Time to first useful result <= 30s on warm path.
2. Steps to first value <= 2 for quick ask.
3. Advanced controls hidden by default for first session.
4. Message delivery proof visible for 100% of sent actions.
5. New user can complete one end-to-end task without external guidance.

## Risks and controls

1. Risk: over-simplification hides power users' tools.
   Control: one-tap "expand to expert" at every stage.
2. Risk: relay ack interpreted as full completion.
   Control: explicit status split: `delivered`, `acked`, `replied`.
3. Risk: scope drift into unrelated explorations.
   Control: P0 lane guard; non-umbrella tasks require explicit assignment.

