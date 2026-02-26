# DATA-LOSS RISK ASSESSMENT REQUEST — ORION
> From: Rex | Date: 2026-02-26 | Priority: P0

Review Rex's Stage 1 plan for data-loss risks. The plan:
1. Rotate 8 API keys, click GitHub unblock URLs, push 9 commits as-is (zero history rewrite)
2. Integrate compute_d_metric.py into rhea_commit.sh (new Step 6 after commit)
3. Deploy permanent Firestore rules (replacing temp rules expiring 2026-02-27)

**Specific concerns:**
- If D-metric step FAILS inside rhea_commit.sh, does the commit abort? Could that prevent saving work?
- Are there any files in the 9 unpushed commits that could be lost if push fails again?
- Does the GitHub unblock approach leave any security exposure beyond the rotated keys?
- Is there anything in relay_chain.jsonl, snapshots, or memory-core that could be corrupted by these operations?

Write risk assessment to: `ops/virtual-office/outbox/ORION_20260226_RISK_ASSESSMENT.md`
Format: RISK / LIKELIHOOD / IMPACT / MITIGATION. Be blunt.
