# Event Sourcing for Memory (Advanced)

SYSTEM:
You are a systems architect. Use precise terms. Prefer append-only truth. Avoid hand-wavy claims.

USER:
Design an event-sourced memory system for an LLM agent stack.
Include:
- event types (MessageAppended, DraftCreated, DraftUpdated, VerificationPassed/Failed, ArtifactPromoted, PolicyViolation, ToolCallRequested/Executed)
- append-only log format
- projections (read models) for: CurrentState, ArtifactIndex, TaskBoard, RiskDashboard
- how to rebuild state from events
- how to handle schema evolution (versioned events)
Output: minimal schemas + a short explanation of why event sourcing prevents memory drift.
