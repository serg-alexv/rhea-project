#!/usr/bin/env python3
"""
rhea_bridge.py — Multi-model API bridge for Rhea
Supports 6 providers, 40+ models, tribunal mode.
Enforces cost-aware tiered routing (cheap → balanced → expensive).

Usage:
    python3 src/rhea_bridge.py status
    python3 src/rhea_bridge.py ask "provider/model" "prompt"
    python3 src/rhea_bridge.py ask-default "prompt"              # uses cheap tier
    python3 src/rhea_bridge.py ask-tier "balanced" "prompt"      # explicit tier
    python3 src/rhea_bridge.py tribunal "prompt" [--k 5]
    python3 src/rhea_bridge.py tiers                             # show tier config
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv optional — env vars can be set directly


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ModelResponse:
    provider: str
    model: str
    text: str
    latency_s: float
    tokens_used: int = 0
    error: Optional[str] = None
    tier: str = ""  # which cost tier was used


@dataclass
class TribunalResult:
    prompt: str
    responses: list = field(default_factory=list)
    consensus: str = ""
    k: int = 5
    elapsed_s: float = 0.0


@dataclass
class ProviderConfig:
    name: str
    display_name: str
    base_url: str
    api_key_env: str
    models: list = field(default_factory=list)
    call_method: str = "openai_compatible"


# ---------------------------------------------------------------------------
# Tiered model config — COST DISCIPLINE (ADR-008)
# ---------------------------------------------------------------------------
# Sonnet is the default working brain. Expensive models require justification.
# Each tier is an ordered list of fallback candidates (first available wins).
# Format: "provider/model"

MODEL_TIERS = {
    "cheap": {
        "description": "Default tier. Fast, cost-effective. Use for all routine work.",
        "candidates": [
            "openrouter/anthropic/claude-sonnet-4",
            "gemini/gemini-2.0-flash",
            "openai/gpt-4o-mini",
            "deepseek/deepseek-chat",
            "azure/gpt-4o-mini",
            "gemini/gemini-2.0-flash-lite",
            "openai/gpt-4.1-nano",
        ],
    },
    "balanced": {
        "description": "Mid-tier. For complex reasoning that cheap tier struggles with.",
        "candidates": [
            "openai/gpt-4o",
            "gemini/gemini-2.5-flash",
            "openai/gpt-4.1",
            "openrouter/mistralai/mistral-large-latest",
            "azure/gpt-4o",
        ],
    },
    "expensive": {
        "description": "Use ONLY when explicitly justified. Deep reasoning, critique, research.",
        "candidates": [
            "gemini/gemini-2.5-pro",
            "openai/gpt-4.5-preview",
            "openai/o3",
            "openrouter/google/gemini-2.5-pro-preview",
            "openrouter/qwen/qwen3-235b-a22b",
        ],
    },
    "reasoning": {
        "description": "Specialized reasoning models. For chain-of-thought / math / logic.",
        "candidates": [
            "openai/o4-mini",
            "openai/o3-mini",
            "deepseek/deepseek-reasoner",
            "openrouter/deepseek/deepseek-r1",
            "azure/DeepSeek-R1",
        ],
    },
}

DEFAULT_TIER = "cheap"  # HARD RULE: Sonnet / cheap models by default


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

PROVIDERS = {
    "openai": ProviderConfig(
        name="openai",
        display_name="OpenAI",
        base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        models=[
            "gpt-4o", "gpt-4o-mini",
            "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano",
            "o3", "o3-mini", "o4-mini",
            "gpt-4.5-preview",
        ],
        call_method="openai_compatible",
    ),
    "gemini": ProviderConfig(
        name="gemini",
        display_name="Google Gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        api_key_env="GEMINI_API_KEY",
        models=[
            "gemini-2.5-pro", "gemini-2.5-flash",
            "gemini-2.0-flash", "gemini-2.0-flash-lite",
            "gemini-1.5-pro", "gemini-1.5-flash",
        ],
        call_method="gemini",
    ),
    "deepseek": ProviderConfig(
        name="deepseek",
        display_name="DeepSeek",
        base_url="https://api.deepseek.com/v1",
        api_key_env="DEEPSEEK_API_KEY",
        models=["deepseek-chat", "deepseek-reasoner"],
        call_method="openai_compatible",
    ),
    "openrouter": ProviderConfig(
        name="openrouter",
        display_name="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
        models=[
            "deepseek/deepseek-r1",
            "qwen/qwen3-235b-a22b",
            "mistralai/mistral-large-latest",
            "meta-llama/llama-4-maverick",
            "google/gemini-2.5-pro-preview",
            "anthropic/claude-sonnet-4",
        ],
        call_method="openai_compatible",
    ),
    "huggingface": ProviderConfig(
        name="huggingface",
        display_name="HuggingFace",
        base_url="https://router.huggingface.co/models",
        api_key_env="HF_TOKEN",
        models=[
            "core42/jais-adaptive-7b-chat",
            "mistralai/Mistral-7B-Instruct-v0.3",
            "HuggingFaceH4/zephyr-7b-beta",
        ],
        call_method="huggingface",
    ),
    "azure": ProviderConfig(
        name="azure",
        display_name="Azure AI Foundry",
        base_url="https://models.inference.ai.azure.com",
        api_key_env="AZURE_API_KEY",
        models=[
            "gpt-4o", "gpt-4o-mini",
            "Llama-4-Maverick-17B-128E-Instruct-FP8",
            "DeepSeek-R1",
            "Cohere-command-r-plus-08-2024",
        ],
        call_method="openai_compatible",
    ),
}


# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------

class RheaBridge:
    """Multi-provider LLM bridge with tiered cost-aware routing and tribunal support."""

    def __init__(self):
        self.providers = PROVIDERS
        self.tiers = MODEL_TIERS
        self.default_tier = DEFAULT_TIER

    # --- public API: tiered (preferred) ---

    def ask_default(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ModelResponse:
        """Send a prompt using the default (cheap) tier. This is the preferred entry point."""
        return self.ask_tier(self.default_tier, prompt, system, temperature, max_tokens)

    def ask_tier(
        self,
        tier: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ModelResponse:
        """Send a prompt using a specific cost tier. Falls through candidates until one works."""
        tier_cfg = self.tiers.get(tier)
        if not tier_cfg:
            return ModelResponse(
                provider="", model="", text="", latency_s=0, tier=tier,
                error=f"Unknown tier: {tier}. Valid: {list(self.tiers.keys())}",
            )

        # Try candidates in order; first available provider wins
        last_error = None
        for candidate in tier_cfg["candidates"]:
            provider_name, model_id = self._resolve_model(candidate)
            cfg = self.providers.get(provider_name)
            if not cfg:
                continue
            api_key = os.environ.get(cfg.api_key_env, "")
            if not api_key and cfg.name == "gemini":
                api_key = os.environ.get("GEMINI_T1_API_KEY", "")
            if not api_key:
                continue  # skip providers without keys
            resp = self.ask(prompt, candidate, system, temperature, max_tokens)
            resp.tier = tier
            if not resp.error:
                return resp
            last_error = resp.error

        # All candidates failed
        return ModelResponse(
            provider="", model="", text="", latency_s=0, tier=tier,
            error=f"All {tier} tier candidates failed. Last error: {last_error}",
        )

    # --- public API: direct model (use when you know exactly what you need) ---

    def ask(
        self,
        prompt: str,
        model: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ModelResponse:
        """Send a prompt to a specific model. Format: 'provider/model'."""
        provider_name, model_id = self._resolve_model(model)
        cfg = self.providers.get(provider_name)
        if not cfg:
            return ModelResponse(
                provider=provider_name, model=model_id,
                text="", latency_s=0, error=f"Unknown provider: {provider_name}",
            )

        api_key = os.environ.get(cfg.api_key_env, "")
        # Gemini fallback: try T1 key if main key unavailable or rate-limited
        if not api_key and cfg.name == "gemini":
            api_key = os.environ.get("GEMINI_T1_API_KEY", "")
        if not api_key:
            return ModelResponse(
                provider=provider_name, model=model_id,
                text="", latency_s=0,
                error=f"No API key: set {cfg.api_key_env}",
            )

        t0 = time.time()
        try:
            if cfg.call_method == "openai_compatible":
                text, tokens = self._call_openai_compatible(
                    cfg, api_key, model_id, prompt, system, temperature, max_tokens
                )
            elif cfg.call_method == "gemini":
                try:
                    text, tokens = self._call_gemini(
                        cfg, api_key, model_id, prompt, system, temperature, max_tokens
                    )
                except Exception as gemini_err:
                    # Retry with T1 key on rate limit
                    t1_key = os.environ.get("GEMINI_T1_API_KEY", "")
                    if t1_key and t1_key != api_key and "429" in str(gemini_err):
                        text, tokens = self._call_gemini(
                            cfg, t1_key, model_id, prompt, system, temperature, max_tokens
                        )
                    else:
                        raise
            elif cfg.call_method == "huggingface":
                text, tokens = self._call_huggingface(
                    cfg, api_key, model_id, prompt, system, temperature, max_tokens
                )
            else:
                return ModelResponse(
                    provider=provider_name, model=model_id,
                    text="", latency_s=0,
                    error=f"Unknown call method: {cfg.call_method}",
                )
            elapsed = time.time() - t0
            return ModelResponse(
                provider=provider_name, model=model_id,
                text=text, latency_s=round(elapsed, 2), tokens_used=tokens,
            )
        except Exception as e:
            elapsed = time.time() - t0
            return ModelResponse(
                provider=provider_name, model=model_id,
                text="", latency_s=round(elapsed, 2), error=str(e),
            )

    def tribunal(
        self,
        prompt: str,
        k: int = 5,
        system: str = "",
        models: list = None,
        tier: str = "cheap",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> TribunalResult:
        """Query k diverse models in parallel, return all responses.

        By default uses cheap-tier models for cost discipline.
        Pass tier="balanced" or tier="expensive" for harder problems.
        Pass models=[...] to override tier selection entirely.
        """
        if models is None:
            models = self._select_diverse_models(k, tier=tier)
        else:
            models = models[:k]

        t0 = time.time()
        responses = []

        with ThreadPoolExecutor(max_workers=min(k, 10)) as pool:
            futures = {
                pool.submit(
                    self.ask, prompt, m, system, temperature, max_tokens
                ): m
                for m in models
            }
            for future in as_completed(futures):
                try:
                    responses.append(future.result())
                except Exception as e:
                    model_key = futures[future]
                    responses.append(ModelResponse(
                        provider="?", model=model_key,
                        text="", latency_s=0, error=str(e),
                    ))

        elapsed = time.time() - t0
        successful = [r for r in responses if not r.error]
        consensus = ""
        if successful:
            consensus = f"{len(successful)}/{len(responses)} models responded successfully"

        return TribunalResult(
            prompt=prompt,
            responses=responses,
            consensus=consensus,
            k=k,
            elapsed_s=round(elapsed, 2),
        )

    def models_status(self) -> dict:
        """Return provider availability and model counts."""
        status = {"providers": {}}
        for name, cfg in self.providers.items():
            key = os.environ.get(cfg.api_key_env, "")
            status["providers"][name] = {
                "display_name": cfg.display_name,
                "available": bool(key),
                "api_key_env": cfg.api_key_env,
                "key_set": bool(key),
                "models": cfg.models,
                "model_count": len(cfg.models),
                "base_url": cfg.base_url,
            }
        total_models = sum(len(c.models) for c in self.providers.values())
        available = sum(
            1 for c in self.providers.values()
            if os.environ.get(c.api_key_env)
        )
        status["summary"] = {
            "total_providers": len(self.providers),
            "available_providers": available,
            "total_models": total_models,
            "default_tier": self.default_tier,
        }
        return status

    def tiers_info(self) -> dict:
        """Return tier configuration with availability status."""
        info = {}
        for tier_name, tier_cfg in self.tiers.items():
            candidates_status = []
            for candidate in tier_cfg["candidates"]:
                provider_name, model_id = self._resolve_model(candidate)
                cfg = self.providers.get(provider_name)
                has_key = bool(cfg and os.environ.get(cfg.api_key_env, ""))
                candidates_status.append({
                    "model": candidate,
                    "available": has_key,
                })
            info[tier_name] = {
                "description": tier_cfg["description"],
                "is_default": tier_name == self.default_tier,
                "candidates": candidates_status,
                "available_count": sum(1 for c in candidates_status if c["available"]),
            }
        return info

    # --- private: provider-specific call methods ---

    def _call_openai_compatible(self, cfg, api_key, model, prompt, system, temperature, max_tokens):
        import requests
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if cfg.name == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/serg-alexv/rhea-project"
            headers["X-Title"] = "Rhea"

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = requests.post(
            f"{cfg.base_url}/chat/completions",
            headers=headers, json=body, timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        return text, tokens

    def _call_gemini(self, cfg, api_key, model, prompt, system, temperature, max_tokens):
        import requests
        url = f"{cfg.base_url}/models/{model}:generateContent?key={api_key}"
        contents = []
        if system:
            contents.append({"role": "user", "parts": [{"text": system}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        body = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        resp = requests.post(url, json=body, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)
        return text, tokens

    def _call_huggingface(self, cfg, api_key, model, prompt, system, temperature, max_tokens):
        import requests
        headers = {"Authorization": f"Bearer {api_key}"}
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        body = {
            "inputs": full_prompt,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "return_full_text": False,
            },
        }
        resp = requests.post(
            f"{cfg.base_url}/{model}",
            headers=headers, json=body, timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            text = data[0].get("generated_text", "")
        else:
            text = str(data)
        return text, 0

    # --- private: model resolution ---

    def _resolve_model(self, model_str: str):
        """Parse 'provider/model' format. If no slash, try to auto-detect."""
        if "/" in model_str:
            parts = model_str.split("/", 1)
            # Handle multi-segment model IDs (e.g. openrouter deepseek/deepseek-r1)
            provider_candidate = parts[0].lower()
            if provider_candidate in self.providers:
                return provider_candidate, parts[1]
            # Might be a model ID with slashes (openrouter style)
            return "openrouter", model_str

        # Auto-detect: search all providers
        model_lower = model_str.lower()
        for name, cfg in self.providers.items():
            for m in cfg.models:
                if m.lower() == model_lower:
                    return name, m
        # Default to openai
        return "openai", model_str

    def _select_diverse_models(self, k: int, tier: str = "cheap") -> list:
        """Pick k models across different providers for tribunal diversity.

        Prefers models from the specified tier, then fills remaining slots
        from other available models to ensure provider diversity.
        """
        # Start with tier candidates that have available keys
        tier_cfg = self.tiers.get(tier, self.tiers[self.default_tier])
        tier_candidates = []
        seen_providers = set()
        for candidate in tier_cfg["candidates"]:
            provider_name, model_id = self._resolve_model(candidate)
            cfg = self.providers.get(provider_name)
            if not cfg:
                continue
            api_key = os.environ.get(cfg.api_key_env, "")
            if not api_key and cfg.name == "gemini":
                api_key = os.environ.get("GEMINI_T1_API_KEY", "")
            if api_key and provider_name not in seen_providers:
                tier_candidates.append(candidate)
                seen_providers.add(provider_name)

        selected = tier_candidates[:k]

        # If we need more, fill from other providers not yet represented
        if len(selected) < k:
            for name, cfg in self.providers.items():
                if name in seen_providers:
                    continue
                if os.environ.get(cfg.api_key_env) and cfg.models:
                    selected.append(f"{name}/{cfg.models[0]}")
                    seen_providers.add(name)
                    if len(selected) >= k:
                        break

        if not selected:
            # Fallback defaults (will fail gracefully if no keys)
            defaults = [
                "openai/gpt-4o-mini",
                "gemini/gemini-2.0-flash",
                "deepseek/deepseek-chat",
                "openrouter/anthropic/claude-sonnet-4",
                "azure/gpt-4o-mini",
            ]
            return defaults[:k]

        return selected[:k]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import sys
    bridge = RheaBridge()

    if len(sys.argv) < 2:
        print("Usage: rhea_bridge.py {status|tiers|ask|ask-default|ask-tier|tribunal}")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "status":
        print(json.dumps(bridge.models_status(), indent=2))

    elif cmd == "tiers":
        print(json.dumps(bridge.tiers_info(), indent=2))

    elif cmd == "ask":
        if len(sys.argv) < 4:
            print("Usage: rhea_bridge.py ask <provider/model> <prompt>")
            sys.exit(1)
        model = sys.argv[2]
        prompt = sys.argv[3]
        resp = bridge.ask(prompt, model)
        print(json.dumps(asdict(resp), indent=2))

    elif cmd == "ask-default":
        if len(sys.argv) < 3:
            print("Usage: rhea_bridge.py ask-default <prompt>")
            sys.exit(1)
        prompt = sys.argv[2]
        resp = bridge.ask_default(prompt)
        print(json.dumps(asdict(resp), indent=2))

    elif cmd == "ask-tier":
        if len(sys.argv) < 4:
            print("Usage: rhea_bridge.py ask-tier <tier> <prompt>")
            print(f"  Available tiers: {list(MODEL_TIERS.keys())}")
            sys.exit(1)
        tier = sys.argv[2]
        prompt = sys.argv[3]
        resp = bridge.ask_tier(tier, prompt)
        print(json.dumps(asdict(resp), indent=2))

    elif cmd == "tribunal":
        if len(sys.argv) < 3:
            print("Usage: rhea_bridge.py tribunal <prompt> [--k N] [--tier TIER]")
            sys.exit(1)
        prompt = sys.argv[2]
        k = 5
        tier = "cheap"
        if "--k" in sys.argv:
            idx = sys.argv.index("--k")
            if idx + 1 < len(sys.argv):
                k = int(sys.argv[idx + 1])
        if "--tier" in sys.argv:
            idx = sys.argv.index("--tier")
            if idx + 1 < len(sys.argv):
                tier = sys.argv[idx + 1]
        result = bridge.tribunal(prompt, k=k, tier=tier)
        output = {
            "prompt": result.prompt,
            "k": result.k,
            "tier": tier,
            "elapsed_s": result.elapsed_s,
            "consensus": result.consensus,
            "responses": [asdict(r) for r in result.responses],
        }
        print(json.dumps(output, indent=2))

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
