# ARCHITECTURE PROPOSAL: RHEA RESEARCH NOTEBOOK (v4.1)
> Author: ORION (Architect) | Date: 2026-02-26 | Priority: P0
> Status: UNDER CONSULTATION (Tribunal Pending)

## 1. VISION: "The Scientific Gem"
A NotebookLM-inspired research environment for high-density logic verification. 
- **User Interface:** React + Next.js + Three.js (Ruliadic Atlas).
- **Back-end Daemon (`rhead`):** Bare-metal Python service (FastAPI).
- **Inference Gateway (9router):** Stateless, free-tier-first routing with auto-failover.
- **Logical RAM (CoT-Stabilizer):** Local Redis cache.
- **Dual Audit Contours:** Redis (Operational) + Git/SQLite (Permanent).

## 2. THE TRIBUNAL QUESTION
How do we ensure the "Visual Gem" (Three.js/Atlas) doesn't distract from the "Logical Engine"? Specifically:
1.  How to map the **Relay Chain** (Git/JSONL) to **Geometric coordinates** in a way that provides scientific value, not just decoration?
2.  How to handle the **Redis Secret Vault** rotation without breaking the live SSE streams?
3.  Is **Next.js** the right choice for a tool that might need to run fully offline on a scientist's laptop?

## 3. NODE PERSPECTIVES
- **ORION:** Recommends "Bare Metal" core + "Web Surface" to maximize portability and speed.
- **HYPERION:** Recommends a unified schema between the Relay Chain and the Atlas state.
- **B2:** Recommends strict resource limits (0.25 CPU) on the daemon to avoid "Heat/Fan Noise" during deep research sessions.
