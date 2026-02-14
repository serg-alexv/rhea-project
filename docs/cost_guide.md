# Rhea — Cost Guide ($0.05/day Target)

> How Rhea achieves deep AI-powered daily optimization for pennies.

## Budget Architecture

**Target:** $0.05/day (~$1.50/month, ~$18/year)

### Tier Routing (ADR-008)

| Tier | Models | Cost/1K tokens | Use case | % of calls |
|------|--------|----------------|----------|------------|
| Cheap | Sonnet 4, Flash, GPT-4o-mini | $0.001–0.005 | Routine ops, formatting, simple Q&A | ~80% |
| Balanced | GPT-4o, Gemini-2.5-Flash | $0.005–0.02 | Planning, analysis | ~15% |
| Expensive | Gemini-2.5-Pro, GPT-4.5 | $0.02–0.10 | Deep research, critique | ~4% |
| Reasoning | o4-mini, DeepSeek-R1 | $0.01–0.05 | Novel synthesis, mathematical reasoning | ~1% |

### Daily Budget Breakdown

```
Morning schedule generation:  ~2K tokens cheap    = $0.002
2× ultradian block planning: ~1K tokens cheap     = $0.001
Body-state analysis:          ~1K tokens cheap     = $0.001
Evening reflection:           ~2K tokens cheap     = $0.002
1× deep planning (Athena):    ~3K tokens balanced  = $0.015
Overhead (metrics, logging):  ~1K tokens cheap     = $0.001
───────────────────────────────────────────────────
Daily subtotal:                                     $0.022
Buffer (50%):                                       $0.011
───────────────────────────────────────────────────
Daily total:                                        $0.033
```

Well under the $0.05 target.

### Weekly Luxury Budget

One tribunal session per week: ~10K tokens across 3+ models = ~$0.15
Amortized daily: $0.02

**Total with tribunal: ~$0.05/day** ✓

## Cost Discipline Rules

1. **Default to cheap tier.** Every call starts cheap unless explicitly escalated.
2. **Log every escalation.** Athena and Hephaestus must justify balanced/expensive calls.
3. **Free tiers first.** Azure AI Foundry, DeepSeek, and OpenRouter free models for non-critical work.
4. **Batch operations.** Combine multiple cheap queries into single calls where possible.
5. **Cache responses.** If the same question was answered in the last 24h, reuse the cached response.

## What This Buys

For $0.05/day, a user gets:
- Personalized daily schedule optimized for their biology
- Real-time body-state awareness (with HealthKit integration)
- Weekly deep-strategy sessions via multi-model tribunal
- Continuous memory and self-improvement
- Scientific grounding in circadian/ultradian/polyvagal research

## Comparison

| Solution | Monthly cost | Quality |
|----------|-------------|---------|
| Human life coach | $200–500 | High but inconsistent |
| Generic AI chatbot | $20 (subscription) | Low — no memory, no science |
| Rhea | $1.50 | High — memory, multi-model, science-backed |

## Monitoring

Track actual spend in `metrics/memory_metrics.json` (future field: `daily_api_cost`).
Alert if 7-day average exceeds $0.10/day.
