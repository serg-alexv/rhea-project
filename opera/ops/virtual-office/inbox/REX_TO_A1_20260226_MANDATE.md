# MANDATE: A1 RESTART (STAGE 2)
> From: Rex (Product Owner) | To: A1 (Conductor)
> Date: 2026-02-26 | Priority: P0

## Context
Stage 1 (D-Metric Loop) is complete and stable. The workspace has been stabilized, and the `hyperion/memory` branch is synced and cleaned of secrets. Inter-agent communication via Firebase is operational and hardened.

## Mission
Initialize and execute Stage 2 tasks under full chain verification. Your primary goal is to establish the core orchestration plumbing for the Rhea system.

## Task List (Priority Order)
1.  **Task #14:** Wire CHRONOS inter-agent messages into `src/rhea_bridge.py`.
2.  **Task #10:** Codify the 5-7 Auto-Tribunal Triggers in `docs/CORE_RULES.md`.
3.  **Task #15:** Implement QWRR Phase 1 (Leases & Fencing) to prevent "zombie" agent collisions.
4.  **Task #16:** Harden CI enforcement (ensure commits fail if checkpoint trailers are missing).

## Constraints
- **Chain Integrity:** Every completed task MUST produce an entry in `relay_chain.jsonl`.
- **Audit Trail:** Use `bash scripts/rhea_commit.sh` for all commits.
- **Cost Discipline:** Use the "cheap" tier by default. Escalate to "reasoning" (DeepSeek-R1) ONLY for Task #10 design.
- **No-Data-Loss:** Proceed with full transparency. Zero history rewrite. Zero file deletion without a chain entry.

## Success Criteria
- At least 4 of the 10 P1 tasks (as mapped above) completed with chain verification passing.
- D-metric stable or trending downward.

**A1: You are cleared for ignition. Report your ALIVE signal once initialized.**
