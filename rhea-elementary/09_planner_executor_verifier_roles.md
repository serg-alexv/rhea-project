09_planner_executor_verifier_roles.md
# Planner / Executor / Verifier Roles (Elementary)

SYSTEM:
Separate responsibilities. Avoid role confusion.

USER:
Define three roles:
- Planner: produces a structured plan + acceptance criteria
- Executor: generates drafts + proposes actions
- Verifier: checks invariants + promotes artifacts
Describe inputs/outputs for each as JSON objects.
End with a short "interface contract" for each role.