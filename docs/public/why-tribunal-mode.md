# Why Tribunal Mode Exists

> When one AI model answers a question, you get an opinion.
> When three models answer the same question independently and then compare, you get a decision.

---

## The Problem With Single-Model Answers

Every AI model has blind spots. GPT tends toward confident extrapolation. Claude tends toward careful hedging. Gemini tends toward broad synthesis. DeepSeek brings a different cultural and technical lens. None of them are wrong — they are each incomplete in different ways.

When you ask a single model for a business decision, a technical tradeoff, or a risk assessment, you receive one perspective presented with high confidence. You have no way to know what the model missed, over-weighted, or hallucinated — unless you already know the answer, in which case you did not need to ask.

This is the single-model trust problem: **the output feels authoritative, but you cannot verify it without doing the work yourself.**

---

## What Tribunal Mode Does

Tribunal mode sends the same structured question to multiple AI models simultaneously, collects their independent responses, and produces a comparative analysis. Each model scores the options on predefined criteria. The results are presented side-by-side with individual reasoning exposed.

A real example from our first production tribunal run — evaluating five commercial strategies for an AI product:

| Hypothesis | Model A | Model B | Model C | Average |
|-----------|---------|---------|---------|---------|
| Creative Studio SaaS | 24/40 | 18/40 | 18/40 | 20.0 |
| Agent Ops Platform | 26/40 | 18/40 | 22/40 | 22.0 |
| Tribunal as a Service | 30/40 | 24/40 | 31/40 | **28.3** |
| Open Core | 29/40 | 24/40 | 25/40 | 26.0 |
| Chronobiology iOS | 24/40 | 17/40 | 18/40 | 19.7 |

Three models. 3/3 unanimous on the top pick. 18 seconds total. Under $0.01 in API costs (cheap tier models).

The value is not the average score — it is the **disagreement pattern**. When all three models converge, confidence is high. When they diverge, you know where the uncertainty lives and can investigate further.

---

## Why Not Just Ask One Model Twice?

Asking the same model twice gives you variance, not diversity. The second answer is shaped by the same training data, the same RLHF preferences, the same architecture biases. You learn about the model's confidence interval, not about the problem.

Tribunal mode uses structurally different models — different training corpora, different architectures, different alignment approaches. The disagreements are informative because they come from genuinely different reasoning paths.

---

## What This Is Not

Tribunal mode is not voting. It is not majority-rules. It is not "ask three and pick the most popular."

It is structured multi-perspective analysis. The output includes each model's individual reasoning, not just scores. A 2-1 split with strong dissent from the third model is more valuable than 3-0 agreement with weak reasoning — it tells you the decision has a genuine tradeoff that one model spotted and the others missed.

---

## When To Use It

Tribunal mode is expensive in absolute terms (3x+ the API cost of a single query) but cheap relative to the cost of a wrong decision. Use it for:

- **Strategic decisions** with multiple viable options and no clear winner
- **Risk assessment** where false confidence is dangerous
- **Technical tradeoffs** where different perspectives genuinely matter (performance vs. maintainability vs. cost)
- **Anything you would want a second opinion on** — tribunal gives you three at once

Do not use it for factual lookups, code generation, or tasks where a single model is clearly sufficient. The cost-per-call is small, but the cognitive overhead of reading three answers when one would do is real.

---

## How It Works (Technical)

The tribunal system uses tiered model selection:

1. **Cheap tier** (screening): GPT-4o-mini + Gemini Flash + Sonnet — fast, under $0.01/call. Good for initial filtering and scoring.
2. **Balanced tier** (decisions): GPT-4o + Gemini Pro + Opus — higher quality reasoning, $0.05-0.15/call.
3. **Expensive tier** (critical): o3 + Opus + DeepSeek R1 — maximum reasoning depth, $0.30+/call. Reserved for irreversible decisions.

Each model receives the same structured prompt with explicit scoring criteria. Responses are collected in parallel (not sequentially — no model sees another's answer). A consensus analyzer extracts scores, identifies agreement/disagreement, and produces a verdict with confidence level.

The entire flow is logged with full provenance: which models, which prompt version, which scores, which reasoning. Every tribunal decision is auditable and reproducible.

---

## What We Learned

After running tribunals in production for commercial strategy, architecture decisions, and prioritization:

1. **Unanimous agreement is rare and meaningful.** When three structurally different models converge on the same answer with strong reasoning, the decision is almost certainly correct. Our first commercial strategy tribunal was 3/3 unanimous — we shipped the decision same day.

2. **The cheapest tier is surprisingly good for screening.** Mini/Flash/Sonnet models disagree with their expensive counterparts on rankings less than 15% of the time. Use cheap for filtering, expensive for final calls.

3. **The real value is in the reasoning, not the scores.** A model that scores an option 18/40 while another scores it 31/40 forces you to read both justifications. The disagreement is the insight.

---

*Built as part of [Rhea](https://github.com/serg-alexv/rhea-project) — an open protocol for multi-model AI coordination.*
