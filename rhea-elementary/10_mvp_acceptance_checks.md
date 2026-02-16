10_mvp_acceptance_checks.md
# MVP Acceptance Checks (Elementary)

SYSTEM:
You are doing production readiness. Keep it minimal and testable.

USER:
Provide a 12-item acceptance checklist for an MVP:
- end-to-end job lifecycle works
- verifier blocks bad receipts
- retries don't duplicate work
- TTL cleans drafts
- logs exist for every operation
Each item must have: test method + expected outcome.