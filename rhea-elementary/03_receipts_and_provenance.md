03_receipts_and_provenance.md
# Receipts & Provenance (Elementary)

SYSTEM:
Every stored claim needs provenance. No provenance => hypothesis.

USER:
Define a "Receipt" object and rules for using it.
Requirements:
- receipt fields: source_type, ref, timestamp, excerpt(optional), hash(optional), confidence
- when to require receipts (facts, decisions, plans)
- how to store "hypotheses" safely without polluting facts
Output: JSON schema-ish examples + brief rules.