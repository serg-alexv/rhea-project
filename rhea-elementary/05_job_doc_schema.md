05_job_doc_schema.md
# Job Document Schema (Elementary)

SYSTEM:
You produce schemas that are safe for retries and concurrency.

USER:
Design a "jobs/{jid}" document schema for agent orchestration.
Must include:
- type, status, priority
- idempotencyKey
- leaseUntil, attempt
- input, output, errors
- createdAt, expireAt
Also provide a state transition table in plain text (new -> processing -> done/failed; retry rules).