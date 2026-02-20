# PROC-003: TRIBUNAL AUDIT (THE CIRCLE)
> Goal: Multi-model verification of high-stakes architectural or public-facing changes.

## 1. TRIGGER
Triggered for "Brave Updates," "GitHub Reshapes," or changes to "Core Principles."

## 2. THE PIPELINE (The Circle)
1.  **DRAFT:** Node (Orion/Rex) creates a proposed artifact.
2.  **TRIBUNAL:** Execute `src/rhea_bridge.py tribunal` with:
    *   `--k 5` (Minimum 5 diverse models).
    *   `--mode chairman` (Synthesis by a reasoning model).
3.  **RECEIPT:** Save the full JSON consensus report to `docs/decisions/ADR-XXX_VERDICT.md`.
4.  **REFLEXIVE SPRINT:** Node must "Rethink" the draft based on the **Dissent Points** in the report.
5.  **ACTUATION:** Perform surgery on the draft and commit.

## 3. VERIFICATION
The update is only "DONE" if the final commit message references the ADR-XXX Verdict ID.
