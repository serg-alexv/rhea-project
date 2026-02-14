# Rhea — Usage Examples

> Concrete examples of how Rhea works in practice.

## Example 1: Morning Routine Generation

**Input:** User wakes at 6:30 AM, has a 9:00 AM meeting, mild sleep debt (1.5h).

**Rhea's output:**
```
06:30 — Wake + 5 min natural light (window/balcony)
06:35 — 10 min gentle movement (stretching, walk)
06:50 — Hydrate + light breakfast
07:10 — Body-first block complete ✓
07:15 — First cognitive block (90 min ultradian)
08:45 — 15 min break (movement, no screens)
09:00 — Meeting
```

**Why this works:** Body-first morning addresses sleep debt through light exposure and movement before cognitive load. The 90-min block aligns with ultradian rhythms.

## Example 2: Tribunal Decision

**Question:** "Should I add a meditation block to mornings?"

**Tribunal (3 models):**
- Model A (Opus): "Yes — 10 min mindfulness reduces cortisol. But for ADHD: body-scan, not sitting meditation."
- Model B (GPT-4o): "Conditional — only if user has >7h sleep. Sleep-deprived meditation can increase drowsiness."
- Model C (Gemini): "Yes — but reframe as 'breathing exercise' to reduce ADHD avoidance."

**Consensus:** Add 5-min breathing exercise after movement block. Not labeled as "meditation." Conditional on adequate sleep.

## Example 3: Memory Benchmark

```bash
$ bash scripts/memory_benchmark.sh

═══════ RHEA MEMORY BENCHMARK ═══════
Layer 1: Git (Structural Memory)     [10/10] ✅
Layer 2: Docs (Semantic Memory)      [15/15] ✅
Layer 3: Entire.io (Episodic Memory) [12/12] ✅
Layer 4: Metrics (Self-Awareness)    [10/10] ✅
Layer 5: Snapshots (Journal)          [8/8]  ✅
Layer 6: Cross-Layer Integration     [15/16] ⚠️ (1 warning)
──────────────────────────────────
TOTAL: 70/71 — 98% — ALL CRITICAL CHECKS PASSED
```

## Example 4: Discomfort Check

When Rhea detects memory bloat:
```
⚠️ D = 165 (T1=150 exceeded)
Recommendation: Schedule cleanup
- 3 docs over 10KB → candidates for summarization
- 12 AUTO-* snapshots older than 30 days → archive
- open_todo_count = 22 → review and close stale items
```

## Example 5: External Oracle Query

When Rhea needs expertise beyond its models:
```
ATLAS_QUERY >>>
Topic: Optimal HRV thresholds for ADHD morning readiness
Context: Building Gaia agent's body-state classifier
Question: What RMSSD/SDNN ranges indicate parasympathetic readiness
         for cognitive work in ADHD adults?
Models already consulted: Opus (inconclusive), Gemini (conflicting data)
<<<

[Human pastes ChatGPT's response]

Rhea integrates the response into docs/architecture.md and updates Gaia's thresholds.
```
