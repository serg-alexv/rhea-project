# Show HN: Multi-Model Consensus API — Ask 5 LLMs, Get Structured Agreement

**URL:** https://github.com/serg-alexv/rhea-project

We built an API that queries multiple LLMs in parallel and returns structured consensus analysis instead of raw text.

**The problem:** Every LLM hallucinates differently. A single model gives you an answer with no way to gauge confidence. You can ask multiple models manually, but comparing 5 freeform responses is tedious.

**What we built:** `POST /tribunal` — send one prompt, get back:
- Responses from 3-7 models (GPT-4o, Gemini, DeepSeek, Mistral, etc.)
- Agreement score (0-100%) with confidence rating
- Stance detection per model (affirmative/negative/qualified)
- Specific agreement and divergence points
- Pairwise similarity matrix

Three analysis levels:
- **L1 (free):** TF-IDF + stance heuristics, no extra API calls
- **L2 (+1 call):** Chairman model synthesizes all responses (Karpathy's LLM Council pattern)
- **L3 (premium):** ICE iterative consensus — models critique each other in rounds until convergence (+7-15% accuracy per the ICE paper)

**Tech:** Python, FastAPI, no dependencies on specific providers. Routes across 6 providers with cost-tier awareness (cheap models by default, expensive on request).

**Why this matters:** Healthcare orgs need claim verification. Legal teams need document analysis confidence. Anyone building with LLMs needs a "how wrong might this be?" signal. Multi-model consensus gives you that.

Self-hosted (MIT). Also available as API ($0.05/call standard, $0.25/call ICE premium).

Happy to answer questions about the consensus scoring, ICE implementation, or anything else.
