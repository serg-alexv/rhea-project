#!/usr/bin/env python3
"""
rhea_bridge.py — Multi-model API bridge for Rhea
Supports 6 providers, 40+ models, tribunal mode.

Usage:
    python3 src/rhea_bridge.py status
    python3 src/rhea_bridge.py ask "provider/model" "prompt"
    python3 src/rhea_bridge.py tribunal "prompt" [--k 5]
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
        base_url="https://api-inference.huggingface.co/models",
        api_key_env="HF_API_KEY",
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
        api_key_env="AZURE_AI_KEY",
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
    """Multi-provider LLM bridge with tribunal support."""

    def __init__(self):
        self.providers = PROVIDERS

    # --- public API ---

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
                text, tokens = self._call_gemini(
                    cfg, api_key, model_id, prompt, system, temperature, max_tokens
                )
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
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> TribunalResult:
        """Query k diverse models in parallel, return all responses."""
        if models is None:
            models = self._select_diverse_models(k)
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
        }
        return status

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

    def _select_diverse_models(self, k: int) -> list:
        """Pick k models across different providers for tribunal diversity."""
        available = []
        for name, cfg in self.providers.items():
            if os.environ.get(cfg.api_key_env):
                for m in cfg.models:
                    available.append(f"{name}/{m}")

        if not available:
            # Return defaults even without keys (will fail gracefully)
            defaults = [
                "openai/gpt-4o",
                "gemini/gemini-2.5-pro",
                "deepseek/deepseek-chat",
                "openrouter/qwen/qwen3-235b-a22b",
                "azure/gpt-4o-mini",
            ]
            return defaults[:k]

        # Pick one model per provider, round-robin
        selected = []
        providers_with_models = [
            (name, cfg) for name, cfg in self.providers.items()
            if os.environ.get(cfg.api_key_env) and cfg.models
        ]
        idx = 0
        while len(selected) < k and idx < 100:
            for name, cfg in providers_with_models:
                model_idx = idx // len(providers_with_models)
                if model_idx < len(cfg.models) and len(selected) < k:
                    selected.append(f"{name}/{cfg.models[model_idx]}")
            idx += 1

        return selected[:k]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import sys
    bridge = RheaBridge()

    if len(sys.argv) < 2:
        print("Usage: rhea_bridge.py {status|ask|tribunal}")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "status":
        print(json.dumps(bridge.models_status(), indent=2))

    elif cmd == "ask":
        if len(sys.argv) < 4:
            print("Usage: rhea_bridge.py ask <provider/model> <prompt>")
            sys.exit(1)
        model = sys.argv[2]
        prompt = sys.argv[3]
        resp = bridge.ask(prompt, model)
        print(json.dumps(asdict(resp), indent=2))

    elif cmd == "tribunal":
        if len(sys.argv) < 3:
            print("Usage: rhea_bridge.py tribunal <prompt> [--k N]")
            sys.exit(1)
        prompt = sys.argv[2]
        k = 5
        if "--k" in sys.argv:
            idx = sys.argv.index("--k")
            if idx + 1 < len(sys.argv):
                k = int(sys.argv[idx + 1])
        result = bridge.tribunal(prompt, k=k)
        output = {
            "prompt": result.prompt,
            "k": result.k,
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
