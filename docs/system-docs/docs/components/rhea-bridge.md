---
sidebar_position: 2
---

# Rhea Bridge

The multi-provider LLM bridge — the core engine that routes prompts to 40+ models across 6+ providers with cost-aware tier routing, retry logic, and call logging.

## Providers

| Provider | API Key Env | Notable Models |
|----------|------------|----------------|
| **OpenAI** | `OPENAI_API_KEY` | gpt-4o, gpt-4o-mini, gpt-4.1-nano, o3, o4-mini |
| **Anthropic** | `ANTHROPIC_API_KEY` | claude-sonnet-4, claude-haiku-3.5 |
| **Google Gemini** | `GEMINI_API_KEY` | gemini-2.5-flash, gemini-2.5-pro, gemini-3-pro-preview |
| **DeepSeek** | `DEEPSEEK_API_KEY` | deepseek-chat, deepseek-reasoner |
| **Groq** | `GROQ_API_KEY` | llama-3.1-8b-instant, llama-3.3-70b-versatile |
| **HuggingFace** | `HF_TOKEN` | Llama-3.2-3B, Phi-3-mini, Qwen2.5-1.5B |
| **Ollama** | *(local)* | qwen3.5:32b, gemma3:27b, deepseek-r1:32b |
| **OpenRouter** | `OPENROUTER_API_KEY` | claude-sonnet-4, qwen3-235b, deepseek-r1 |
| **Azure** | `AZURE_API_KEY` | Llama-4-Maverick, DeepSeek-R1, Cohere-command-r+ |
| **Cerebras** | `CEREBRAS_API_KEY` | llama-3.3-70b |
| **Volcano Engine** | `VOLCENGINE_API_KEY` | doubao-seed-2-0-pro, doubao-1.5-pro-32k |

All providers are accessed through [LiteLLM](https://github.com/BerriAI/litellm) for a unified interface.

## Cost Tiers (ADR-008)

The bridge enforces **cost discipline** — cheap models are the default, expensive models require explicit justification.

| Tier | Description | Example Models |
|------|-------------|----------------|
| `cheap` | Default. Fast, cost-effective. All routine work. | gpt-4o-mini, gemini-2.5-flash, deepseek-chat, ollama/* |
| `balanced` | Complex reasoning that cheap tier struggles with. | gpt-4o, llama-3.3-70b, gemini-2.5-flash |
| `expensive` | Explicit justification required. Deep reasoning. | claude-sonnet-4, gpt-5, o3, gemini-2.5-pro |
| `reasoning` | Specialized chain-of-thought / math / logic. | o4-mini, deepseek-reasoner, gemini-3-pro-preview |
| `science` | Science-grade. Biology, chemistry, STEM tribunal. | claude-sonnet-4, gemini-2.5-pro, deepseek-reasoner |

Each tier has an ordered list of **fallback candidates** — the first model with a valid API key is used.

## Execution Profiles

Three global profiles control cost/quality tradeoff:

| Profile | Max Tokens | Temp Cap | Tier Mapping |
|---------|-----------|----------|--------------|
| `safe_cheap` | 640 | 0.45 | expensive→balanced, reasoning→balanced |
| `balanced` | 1400 | 0.70 | 1:1 mapping |
| `deep` | 2800 | 0.85 | cheap→expensive, balanced→expensive |

Set via env var `RHEA_EXECUTION_PROFILE` or API: `POST /settings/execution-profile`.

## Backoff and Retry

The bridge uses **exponential backoff with jitter** (inspired by CockroachDB Cortex) to handle rate limits and transient errors:

```python
BACKOFF_CHEAP = BackoffConfig(min_period=0.5, max_period=10.0, max_retries=3)
BACKOFF_TRIBUNAL = BackoffConfig(min_period=1.0, max_period=30.0, max_retries=5)
```

Retryable errors: `429`, `502`, `503`, `rate limit`, `timeout`, `overloaded`.

## Tribunal Mode

The bridge's `tribunal()` method fans out a prompt to `k` models concurrently:

```python
bridge = RheaBridge()
result = bridge.tribunal("Is coffee good for you?", k=5, tier="cheap")
# result.responses → list of ModelResponse
# result.consensus → synthesized answer
# result.consensus_report → agreement scores
```

Concurrency is managed via `ThreadPoolExecutor` with `as_completed()`.

## Call Logging

Every API call is logged to `logs/bridge_calls.jsonl` with:
- Timestamp, model, provider, tier
- Token counts (prompt + completion)
- Estimated USD cost (from built-in price table)
- Latency, status code
- Agent attribution (`RHEA_AGENT_ID`, `RHEA_CALL_SOURCE` env vars)
- Prompt hash (SHA-256, first 16 chars — no raw prompts in logs)

### Secret Redaction

All log output passes through `redact_secrets()` which strips API keys matching known patterns (Gemini, Anthropic, OpenAI, HF, Groq, DeepSeek).

## Price Table

The bridge maintains an in-memory price table for cost estimation (USD per 1M tokens):

| Model | Input | Output |
|-------|-------|--------|
| gpt-4o-mini | $0.15 | $0.60 |
| gemini-2.5-flash | $0.15 | $0.60 |
| deepseek-chat | $0.14 | $0.28 |
| claude-sonnet-4 | $3.00 | $15.00 |
| gpt-4o | $2.50 | $10.00 |
| o3 | $10.00 | $40.00 |
| ollama/* | $0.00 | $0.00 |

## CLI Usage

```bash
# Check provider/key availability
python3 src/rhea_bridge.py status

# Show tier configuration
python3 src/rhea_bridge.py tiers

# Ask a specific model
python3 src/rhea_bridge.py ask "gemini/gemini-2.5-flash" "What is HRV?"

# Ask using default (cheap) tier
python3 src/rhea_bridge.py ask-default "What is circadian rhythm?"

# Run tribunal consensus
python3 src/rhea_bridge.py tribunal "Is melatonin safe?" --k 5

# Run ICE iterative consensus
python3 src/rhea_bridge.py tribunal-ice "Does polyvagal theory hold up?" --k 4 --rounds 3

# Show/set execution profile
python3 src/rhea_bridge.py profile
python3 src/rhea_bridge.py profile set balanced

# Daily cost summary
python3 src/rhea_bridge.py daily-summary
```

## Auto-Plan Triggers

The bridge monitors LLM responses for **industrialization triggers** — phrases like "production-grade", "industrial-level", or "промышленно" (Russian). When detected, it automatically creates plan-proposal tasks in the task queue, with deduplication by content signature.
