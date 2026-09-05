# Binding development boundary
Work only in the stage admitted by the independent validation controller.
Source observations are not runtime qualification. Keep PASS, FAIL, SKIP,
NOT_EXECUTED and OUTCOME_UNKNOWN distinct; never manufacture a receipt.
Do not edit another stage's contract, oracle or evidence to make code pass.
No source relocation, legacy entrypoint startup, remote push or deployment.
These instructions are advisory text: enforce the boundary with dependency
allowlists, separate worker permissions, OS isolation and negative tests.

# 02 — Independent validation
Own independently encoded vectors, black-box runners, fault schedules,
negative controls, gate receipts and promotion verification.
Consume frozen contracts read-only. Never import production encoders,
reducers, hash builders or SQL as expected-output oracles.
Use separate validation checkout and permissions; implementation workers
cannot write the validation outputs used to authorize promotion.
Stage 02 initially proves oracle readiness, not storage correctness.
At stage 03, launch the isolated target and observe complete acknowledgements
from an independent parent. Later stages add separately frozen test suites.
Do not accept a child marker as proof that the client received a reply.
Process kill is not power loss; missing VFS support is NOT_EXECUTED.
Only a reviewed, hash-bound validation run may admit the next stage.
