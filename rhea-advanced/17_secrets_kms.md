# Secrets, KMS, and "No Raw Keys to Models" (Advanced)

SYSTEM:
You are designing secure secret handling. Models never see raw secrets.

USER:
Specify secret management for an LLM orchestration system:
- where secrets live (OS keychain / env / secret manager)
- how tools use secrets without exposing them to the model
- short-lived tokens, scoped credentials
- audit logging for secret access
- rotation plan
Output: a minimal "secrets contract" and examples of safe vs unsafe patterns.
