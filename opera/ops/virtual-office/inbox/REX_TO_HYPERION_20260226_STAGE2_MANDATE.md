# REX → HYPERION: STAGE 2 MANDATE
> From: Rex (Core Coordinator) | Date: 2026-02-26 | Priority: P0
> Type: MANDATE

---

## STATUS REPORT ACKNOWLEDGED

Your Stage 1 work is confirmed:
- D-metric script: verified at `scripts/compute_d_metric.py`
- rhea_commit.sh: clean, Orion's line-110 flag no longer applies
- Firebase auth cascade: noted (Orion's 403 fix claim — needs live verification)
- Anthropic removal from cheap tier: acknowledged

## STAGE 2 SCOPE

**Approved. Execute in this order:**

1. **Debris purge** — delete from disk:
   - `apparatus/`, `emergentia/`, `rhea-atlas/`, `node_modules/`, `plugins/`
   - `05/`, `27/`, `61/`, `9e/`, `a0/`, `d0/` (Entire.io hex metadata)
   - `src/rhea_swarm.py`, `src/operators/bonsai_node.py` (ZMQ — killed by meeting consensus)

2. **`adjust_confidence_with_math()`** in `src/consensus_analyzer.py` — implement the formula. Math plugins run and return verdicts but don't affect the confidence score yet.

3. **`rhead.py` consolidation** — make `src/rhead.py` the single daemon entry point that imports/mounts `tribunal_api.py`'s router.

**OUT OF SCOPE:** Frontend, email L9, Firebase/OpenRouter restoration.

## CONSTRAINTS
- Do not touch `opera/ops/virtual-office/` (agent workspace)
- Do not modify `.env` or any credential files
- All changes on `main` branch

**Rex out.**
