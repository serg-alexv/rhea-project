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
    python3 src/rhea_bridge.py tribunal "prompt" [--k 5] [--mode local|chairman]
    python3 src/rhea_bridge.py tribunal-ice "prompt" [--k 5] [--rounds 3]  # ICE iterative
    python3 src/rhea_bridge.py tiers                             # show tier config
    python3 src/rhea_bridge.py daily-summary [YYYY-MM-DD]        # call log summary
"""

import json
import os
import re
import time
import uuid
import litellm
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Optional

# Disable litellm logging to keep dashboard clean
litellm.set_verbose = False
litellm.telemetry = False

# Enable Redis Caching if available (Task #22)
if os.environ.get("REDIS_URL"):
    try:
        from litellm.caching import Cache
        litellm.cache = Cache(type="redis", url=os.environ.get("REDIS_URL"))
        print("[bridge] Redis STM layer active.")
    except Exception as e:
        print(f"[bridge] Redis init failed: {e}")
litellm.suppress_debug_info = True
import logging
logging.getLogger("LiteLLM").setLevel(logging.CRITICAL)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv optional — env vars can be set directly

try:
    from consensus_analyzer import ConsensusAnalyzer
    _HAS_ANALYZER = True
except ImportError:
    _HAS_ANALYZER = False


# ---------------------------------------------------------------------------
# Secret redaction — NEVER log API keys
# ---------------------------------------------------------------------------

_SECRET_PATTERNS = [
    (re.compile(r'AIzaSy[A-Za-z0-9_-]{33}'), '[REDACTED_GEMINI_KEY]'),
    (re.compile(r'sk-ant-[A-Za-z0-9_-]{20,}'), '[REDACTED_ANTHROPIC_KEY]'),
    (re.compile(r'sk-proj-[A-Za-z0-9_-]{20,}'), '[REDACTED_OPENAI_KEY]'),
    (re.compile(r'sk-[A-Za-z0-9]{20,}'), '[REDACTED_OPENAI_KEY]'),
    (re.compile(r'hf_[A-Za-z0-9]{20,}'), '[REDACTED_HF_KEY]'),
    (re.compile(r'gsk_[A-Za-z0-9]{20,}'), '[REDACTED_GROQ_KEY]'),
    (re.compile(r'dsk-[A-Za-z0-9]{20,}'), '[REDACTED_DEEPSEEK_KEY]'),
]


def redact_secrets(text: str) -> str:
    """Remove API keys from any string before logging."""
    for pattern, replacement in _SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ChronosMessage:
    sender: str
    receiver: str
    task_id: str
    msg_type: str  # request, response, escalation, review
    priority: str  # critical, high, normal, low
    payload: dict
    dependencies: list = field(default_factory=list)
    deadline: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


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
    consensus_report: dict = field(default_factory=dict)
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
            "deepseek/deepseek-chat",
            "anthropic/claude-haiku-3-5-20241022",
            "gemini/gemini-2.5-flash",
            "openai/gpt-4o-mini",
            "azure/gpt-4o-mini",
            "gemini/gemini-2.5-flash-8b",
            "openai/gpt-4.1-nano",
            "openrouter/anthropic/claude-sonnet-4",
        ],
    },
    "balanced": {
        "description": "Mid-tier. For complex reasoning that cheap tier struggles with.",
        "candidates": [
            "gemini/gemini-2.5-flash",
            "deepseek/deepseek-chat",
            "openai/gpt-4o",
            "gemini/gemini-2.5-flash",
        ],
    },
    "expensive": {
        "description": "Use ONLY when explicitly justified. Deep reasoning, critique, research.",
        "candidates": [
            "anthropic/claude-sonnet-4-20250514",
            "deepseek/deepseek-chat",
            "deepseek/deepseek-reasoner",
            "gemini/gemini-3.1-pro-preview",
            "gemini/gemini-3-pro-preview",
            "gemini/gemini-2.5-pro",
            "openai/gpt-4.5-preview",
            "openai/o3",
            "openrouter/qwen/qwen3-235b-a22b",
        ],
    },
    "reasoning": {
        "description": "Specialized reasoning models. For chain-of-thought / math / logic.",
        "candidates": [
            "gemini/gemini-3.1-pro-preview",
            "gemini/gemini-3-pro-preview",
            "openai/o4-mini",
            "openai/o3-mini",
            "deepseek/deepseek-reasoner",
            "openrouter/deepseek/deepseek-r1",
        ],
    },
    "science": {
        "description": "Science-grade models. For biology, chemistry, STEM tribunal queries.",
        "candidates": [
            "anthropic/claude-sonnet-4-20250514",
            "gemini/gemini-3.1-pro-preview",
            "gemini/gemini-3-pro-preview",
            "gemini/gemini-2.5-pro",
            "deepseek/deepseek-reasoner",
            "openrouter/qwen/qwen3-235b-a22b",
            "openrouter/qwen/qwen-2.5-72b-instruct",
            "openrouter/deepseek/deepseek-r1",
            "openai/o3",
            "openai/gpt-4.5-preview",
            "openrouter/meta-llama/llama-4-behemoth",
        ],
    },
}

DEFAULT_TIER = "cheap"  # HARD RULE: Sonnet / cheap models by default


# ---------------------------------------------------------------------------
# Price table — approximate USD per 1M tokens (input, output)
# ---------------------------------------------------------------------------

PRICE_TABLE = {
    # Anthropic
    "claude-sonnet-4-20250514": (3.00, 15.00),
    "claude-haiku-3-5-20241022": (0.80, 4.00),
    # OpenAI
    "gpt-4o":           (2.50,  10.00),
    "gpt-4o-mini":      (0.15,   0.60),
    "gpt-4.1":          (2.00,   8.00),
    "gpt-4.1-mini":     (0.40,   1.60),
    "gpt-4.1-nano":     (0.10,   0.40),
    "gpt-4.5-preview":  (75.00, 150.00),
    "o3":               (10.00,  40.00),
    "o3-mini":          (1.10,   4.40),
    "o4-mini":          (1.10,   4.40),
    # Gemini
    "gemini-2.5-pro":   (1.25,  10.00),
    "gemini-2.5-flash": (0.15,   0.60),
    "gemini-2.0-flash": (0.10,   0.40),
    "gemini-2.0-flash-lite": (0.075, 0.30),
    "gemini-1.5-pro":   (1.25,   5.00),
    "gemini-1.5-flash":  (0.075, 0.30),
    # DeepSeek
    "deepseek-chat":     (0.14,  0.28),
    "deepseek-reasoner": (0.55,  2.19),
    # OpenRouter (use the model-id part after /)
    "deepseek/deepseek-r1":              (0.55, 2.19),
    "qwen/qwen3-235b-a22b":             (0.30, 1.20),
    "qwen/qwen-2.5-72b-instruct":       (0.36, 0.36),
    "mistralai/mistral-large-latest":    (2.00, 6.00),
    "meta-llama/llama-4-maverick":       (0.50, 1.50),
    "meta-llama/llama-4-behemoth":       (2.00, 6.00),
    "google/gemini-2.5-pro-preview":     (1.25, 10.00),
    "anthropic/claude-sonnet-4":         (3.00, 15.00),
    # Azure
    "Llama-4-Maverick-17B-128E-Instruct-FP8": (0.50, 1.50),
    "DeepSeek-R1":                       (0.55, 2.19),
    "Cohere-command-r-plus-08-2024":     (2.50, 10.00),
    # HuggingFace (free/cheap inference)
    "meta-llama/Llama-3.2-3B-Instruct":      (0.00, 0.00),
    "microsoft/Phi-3-mini-4k-instruct": (0.00, 0.00),
    "Qwen/Qwen2.5-1.5B-Instruct":     (0.00, 0.00),
}

PRICE_DEFAULT = (1.00, 3.00)  # fallback for unknown models

# Log file paths (relative to project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
CALL_LOG_PATH = _PROJECT_ROOT / "logs" / "bridge_calls.jsonl"
CHRONOS_LOG_PATH = _PROJECT_ROOT / "logs" / "chronos_relay.jsonl"


# ---------------------------------------------------------------------------
# Call logging helpers
# ---------------------------------------------------------------------------

def _compute_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Compute estimated USD cost from token counts."""
    price_in, price_out = PRICE_TABLE.get(model, PRICE_DEFAULT)
    cost = (prompt_tokens * price_in + completion_tokens * price_out) / 1_000_000
    return round(cost, 8)


def _classify_status(error) -> str:
    """Map error string to a short status code."""
    if error is None:
        return "ok"
    err = str(error)
    for code in ("401", "429", "400", "402", "404"):
        if code in err:
            return code
    if "timeout" in err.lower() or "timed out" in err.lower():
        return "timeout"
    return "error"


def _log_call(
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    latency_ms: float,
    error,
) -> None:
    """Append a single JSONL record to the call log."""
    CALL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    status = _classify_status(error)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "model": model,
        "request_id": str(uuid.uuid4()),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cost_usd": _compute_cost(model, prompt_tokens, completion_tokens),
        "latency_ms": round(latency_ms, 1),
        "status": status,
        "error_short": redact_secrets(str(error)[:200]) if error else "",
    }
    try:
        with open(CALL_LOG_PATH, "a") as f:
            f.write(redact_secrets(json.dumps(record)) + "\n")
    except OSError:
        pass  # logging must never break the bridge


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

# TODO(human): Rotate dead API keys in .env file
# Live test (2026-02-26) shows 1/7 providers alive:
#   DeepSeek    — LIVE
#   Anthropic   — invalid key (sk-ant-api03-... auth error)
#   OpenAI      — invalid key (sk-proj-... "Incorrect API key")
#   Gemini      — key flagged as leaked by Google
#   OpenRouter   — "User not found" (account-level issue)
#   HuggingFace — token expired ("Rhea Office 2026-02-26")
#   Azure       — auth OK but 0 deployments (needs Azure portal deploy)
# Action: regenerate keys at each provider's dashboard, update .env

PROVIDERS = {
    "anthropic": ProviderConfig(
        name="anthropic",
        display_name="Anthropic",
        base_url="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
        models=[
            "claude-sonnet-4-20250514",
            "claude-haiku-3-5-20241022",
        ],
        call_method="anthropic",
    ),
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
            "gemini-3.1-pro-preview", "gemini-3-pro-preview",
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
            "qwen/qwen-2.5-72b-instruct",
            "mistralai/mistral-large-latest",
            "meta-llama/llama-4-maverick",
            "meta-llama/llama-4-behemoth",
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
            "meta-llama/Llama-3.2-3B-Instruct",
            "microsoft/Phi-3-mini-4k-instruct",
            "Qwen/Qwen2.5-1.5B-Instruct",
        ],
        call_method="huggingface",
    ),
    "azure": ProviderConfig(
        name="azure",
        display_name="Azure OpenAI",
        base_url=os.environ.get("AZURE_ENDPOINT", ""),
        api_key_env="AZURE_API_KEY",
        models=[
            "gpt-4o", "gpt-4o-mini",
        ],
        call_method="azure_openai",
    ),
}

# Map env vars for LiteLLM Azure OpenAI provider
_azure_base = os.environ.get("AZURE_ENDPOINT", "")
if _azure_base and "AZURE_API_BASE" not in os.environ:
    os.environ["AZURE_API_BASE"] = _azure_base
if "AZURE_API_VERSION" not in os.environ:
    os.environ["AZURE_API_VERSION"] = "2024-12-01-preview"


# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------

try:
    from rhea_profile_manager import profile_manager
    _HAS_PROFILE = True
except ImportError:
    profile_manager = None
    _HAS_PROFILE = False

try:
    from rhea_visual_context import get_context_block
    _HAS_VISUAL = True
except ImportError:
    get_context_block = None
    _HAS_VISUAL = False

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
        mode: Optional[str] = None,
    ) -> ModelResponse:
        """Send a prompt using the default (cheap) tier. This is the preferred entry point."""
        return self.ask_tier(self.default_tier, prompt, system, temperature, max_tokens, mode)

    def ask_tier(
        self,
        tier: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        mode: Optional[str] = None,
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
            resp = self.ask(prompt, candidate, system, temperature, max_tokens, mode)
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
        mode: Optional[str] = None,
    ) -> ModelResponse:
        """Send a prompt to a specific model via LiteLLM. Format: 'provider/model'."""
        
        # --- Nexus/GPT-Profiler & Visual Context Injection ---
        injected = ""
        if _HAS_PROFILE and profile_manager:
            constraints = profile_manager.get_constraints(mode)
            if constraints:
                injected += constraints
        if _HAS_VISUAL and get_context_block:
            visual_context = get_context_block()
            if visual_context:
                injected += f"\n{visual_context}"
        if injected:
            system = f"{system}\n\n{injected}" if system else injected
        # ----------------------------------------------------

        provider_name, model_id = self._resolve_model(model)
        t0 = time.time()
        
        try:
            # Prepare messages for LiteLLM
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            # Call LiteLLM
            response = litellm.completion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            text = response.choices[0].message.content
            usage = getattr(response, 'usage', {})
            token_info = {
                "prompt_tokens": getattr(usage, 'prompt_tokens', 0),
                "completion_tokens": getattr(usage, 'completion_tokens', 0),
                "total_tokens": getattr(usage, 'total_tokens', 0),
            }

            elapsed = time.time() - t0
            latency_ms = elapsed * 1000
            
            _log_call(
                provider_name, model_id,
                token_info["prompt_tokens"],
                token_info["completion_tokens"],
                token_info["total_tokens"],
                latency_ms, None,
            )

            return ModelResponse(
                provider=provider_name, model=model_id,
                text=text, latency_s=round(elapsed, 2),
                tokens_used=token_info["total_tokens"],
            )

        except Exception as e:
            elapsed = time.time() - t0
            latency_ms = elapsed * 1000
            _log_call(provider_name, model_id, 0, 0, 0, latency_ms, str(e))
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
        mode: str = "local",
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

        # --- Consensus analysis ---
        consensus = ""
        consensus_report = {}
        if successful and _HAS_ANALYZER:
            analyzer = ConsensusAnalyzer(bridge=self)
            resp_tuples = [
                (f"{r.provider}/{r.model}", r.text) for r in successful
            ]
            report = analyzer.analyze(resp_tuples, prompt=prompt, mode=mode)
            consensus = report.consensus_text
            consensus_report = report.to_dict()
        elif successful:
            consensus = f"{len(successful)}/{len(responses)} models responded successfully"

        return TribunalResult(
            prompt=prompt,
            responses=responses,
            consensus=consensus,
            consensus_report=consensus_report,
            k=k,
            elapsed_s=round(elapsed, 2),
        )

    def send_chronos(self, message: ChronosMessage) -> bool:
        """Log and relay a CHRONOS inter-agent message using QWRR relay."""
        try:
            # Ensure project root is in path for opera.ops import
            import sys
            root = str(Path(__file__).resolve().parent.parent)
            if root not in sys.path:
                sys.path.append(root)
                
            from opera.ops import rex_pager
            
            # Map Chronos priority to QWRR priority (P0, P1, P2)
            prio_map = {"critical": "P0", "high": "P1", "normal": "P2", "low": "P3"}
            qwr_priority = prio_map.get(message.priority, "P1")
            
            # Convert ChronosMessage to QWRR-compatible envelope
            payload = asdict(message)
            msg_type = f"chronos.{message.msg_type}"
            
            envelope = rex_pager.make_envelope(
                source=message.sender,
                target=message.receiver,
                msg_type=msg_type,
                payload=payload,
                priority=qwr_priority
            )
            
            # Triple-write: local JSONL + Firestore + inbox markdown
            rex_pager._write_local(envelope)
            rex_pager._write_firestore(envelope)
            rex_pager._write_inbox_backup(envelope)
            
            # Append to the audit chain
            rex_pager.chain_append("chronos.relay", message.sender, {
                "msg_id": envelope["id"],
                "task_id": message.task_id,
                "target": message.receiver
            })
            
            print(f"[bridge] CHRONOS relayed via QWRR: {message.sender}→{message.receiver} (seq={envelope['seq']})")
            return True
            
        except Exception as e:
            print(f"[bridge] Chronos relay failed: {e}")
            # Fallback to simple logging
            self._log_chronos(message)
            return False

    def _log_chronos(self, message: ChronosMessage):
        """Append a CHRONOS message to the relay ledger."""
        CHRONOS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        record = asdict(message)
        try:
            with open(CHRONOS_LOG_PATH, "a") as f:
                f.write(redact_secrets(json.dumps(record)) + "\n")
        except OSError:
            pass

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

    def live_test(self) -> dict:
        """Ping every provider with a real API call. Returns actual liveness, not just key presence."""
        probe = "Reply with exactly one word: ping"
        results = {}
        test_models = {}
        for name, cfg in self.providers.items():
            key = os.environ.get(cfg.api_key_env, "")
            if not key and name == "gemini":
                key = os.environ.get("GEMINI_T1_API_KEY", "")
            if not key:
                results[name] = {"live": False, "error": "no_key", "latency_s": 0}
                continue
            test_models[name] = f"{name}/{cfg.models[0]}"

        with ThreadPoolExecutor(max_workers=len(test_models)) as pool:
            futures = {
                pool.submit(self.ask, probe, model, "", 0.0, 5): prov
                for prov, model in test_models.items()
            }
            for future in as_completed(futures):
                prov = futures[future]
                try:
                    resp = future.result()
                    results[prov] = {
                        "live": not bool(resp.error),
                        "model": test_models[prov],
                        "latency_s": resp.latency_s,
                        "text": resp.text[:30] if resp.text else "",
                        "error": resp.error[:120] if resp.error else None,
                    }
                except Exception as e:
                    results[prov] = {"live": False, "error": str(e)[:120], "latency_s": 0}

        alive = sum(1 for r in results.values() if r.get("live"))
        return {"providers": results, "alive": alive, "total": len(self.providers)}

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
                "gemini/gemini-2.5-flash",
                "deepseek/deepseek-chat",
                "openrouter/anthropic/claude-sonnet-4",
                "azure/gpt-4o-mini",
            ]
            return defaults[:k]

        return selected[:k]


# ---------------------------------------------------------------------------
# Daily summary (reads JSONL log)
# ---------------------------------------------------------------------------

def daily_summary(log_path: Path = CALL_LOG_PATH, date_filter=None) -> str:
    """Read bridge_calls.jsonl and produce a human-readable daily summary.

    Args:
        log_path: Path to the JSONL log file.
        date_filter: ISO date string (YYYY-MM-DD) to filter. None = all records.

    Returns:
        Formatted summary string.
    """
    if not log_path.exists():
        return f"No log file found at {log_path}"

    records = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if date_filter:
                ts = rec.get("timestamp", "")
                if not ts.startswith(date_filter):
                    continue
            records.append(rec)

    if not records:
        msg = "No records found"
        if date_filter:
            msg += f" for {date_filter}"
        return msg

    # --- Total cost by provider ---
    cost_by_provider: dict[str, float] = {}
    for r in records:
        prov = r.get("provider", "unknown")
        cost_by_provider[prov] = cost_by_provider.get(prov, 0.0) + r.get("cost_usd", 0.0)

    # --- Top 5 models by usage ---
    model_counts: dict[str, int] = {}
    for r in records:
        m = r.get("model", "unknown")
        model_counts[m] = model_counts.get(m, 0) + 1
    top_models = sorted(model_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # --- Error counts by status ---
    status_counts: dict[str, int] = {}
    for r in records:
        s = r.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1

    # --- Median latency ---
    latencies = [r.get("latency_ms", 0) for r in records]
    med_latency = median(latencies) if latencies else 0.0

    # --- Total tokens ---
    total_prompt = sum(r.get("prompt_tokens", 0) for r in records)
    total_completion = sum(r.get("completion_tokens", 0) for r in records)
    total_all = sum(r.get("total_tokens", 0) for r in records)
    total_cost = sum(r.get("cost_usd", 0.0) for r in records)

    # --- Format output ---
    lines = []
    header = "Bridge Call Summary"
    if date_filter:
        header += f" ({date_filter})"
    lines.append(f"{'=' * 60}")
    lines.append(header)
    lines.append(f"{'=' * 60}")
    lines.append(f"Total calls: {len(records)}")
    lines.append(f"Total tokens: {total_all:,} (prompt: {total_prompt:,}, completion: {total_completion:,})")
    lines.append(f"Total cost:  ${total_cost:.6f}")
    lines.append(f"Median latency: {med_latency:.1f} ms")
    lines.append("")

    lines.append("Cost by Provider:")
    for prov in sorted(cost_by_provider, key=cost_by_provider.get, reverse=True):
        lines.append(f"  {prov:20s} ${cost_by_provider[prov]:.6f}")
    lines.append("")

    lines.append("Top 5 Models by Usage:")
    for model_name, count in top_models:
        lines.append(f"  {model_name:40s} {count:>5d} calls")
    lines.append("")

    lines.append("Status Breakdown:")
    for status in sorted(status_counts, key=status_counts.get, reverse=True):
        label = status if status != "ok" else "ok (success)"
        lines.append(f"  {label:20s} {status_counts[status]:>5d}")
    lines.append(f"{'=' * 60}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import sys
    bridge = RheaBridge()

    if len(sys.argv) < 2:
        print("Usage: rhea_bridge.py {status|tiers|ask|ask-default|ask-tier|tribunal|tribunal-ice|daily-summary}")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "status":
        print(json.dumps(bridge.models_status(), indent=2))

    elif cmd == "live-test":
        print("Probing all providers (real API calls)...")
        result = bridge.live_test()
        for name, info in result["providers"].items():
            status = "LIVE" if info.get("live") else "DEAD"
            err = info.get("error", "")
            lat = info.get("latency_s", 0)
            txt = info.get("text", "")
            print(f"  {name:15s} {status:4s}  {lat:.1f}s  {txt[:25] if txt else err[:60]}")
        print(f"\nAlive: {result['alive']}/{result['total']}")

    elif cmd == "tiers":
        print(json.dumps(bridge.tiers_info(), indent=2))

    elif cmd == "ask":
        if len(sys.argv) < 4:
            print("Usage: rhea_bridge.py ask <provider/model> <prompt> [--mode MODE]")
            sys.exit(1)
        model = sys.argv[2]
        prompt = sys.argv[3]
        mode = None
        if "--mode" in sys.argv:
            idx = sys.argv.index("--mode")
            if idx + 1 < len(sys.argv):
                mode = sys.argv[idx + 1]
        
        resp = bridge.ask(prompt, model, mode=mode)
        print(json.dumps(asdict(resp), indent=2))

    elif cmd == "ask-default":
        if len(sys.argv) < 3:
            print("Usage: rhea_bridge.py ask-default <prompt> [--mode MODE]")
            sys.exit(1)
        prompt = sys.argv[2]
        mode = None
        if "--mode" in sys.argv:
            idx = sys.argv.index("--mode")
            if idx + 1 < len(sys.argv):
                mode = sys.argv[idx + 1]
                
        resp = bridge.ask_default(prompt, mode=mode)
        print(json.dumps(asdict(resp), indent=2))

    elif cmd == "ask-tier":
        if len(sys.argv) < 4:
            print("Usage: rhea_bridge.py ask-tier <tier> <prompt> [--mode MODE]")
            print(f"  Available tiers: {list(MODEL_TIERS.keys())}")
            sys.exit(1)
        tier = sys.argv[2]
        prompt = sys.argv[3]
        mode = None
        if "--mode" in sys.argv:
            idx = sys.argv.index("--mode")
            if idx + 1 < len(sys.argv):
                mode = sys.argv[idx + 1]
                
        resp = bridge.ask_tier(tier, prompt, mode=mode)
        print(json.dumps(asdict(resp), indent=2))

    elif cmd == "tribunal":
        if len(sys.argv) < 3:
            print("Usage: rhea_bridge.py tribunal <prompt> [--k N] [--tier TIER] [--mode local|chairman]")
            sys.exit(1)
        prompt = sys.argv[2]
        k = 5
        tier = "cheap"
        mode = "local"
        if "--k" in sys.argv:
            idx = sys.argv.index("--k")
            if idx + 1 < len(sys.argv):
                k = int(sys.argv[idx + 1])
        if "--tier" in sys.argv:
            idx = sys.argv.index("--tier")
            if idx + 1 < len(sys.argv):
                tier = sys.argv[idx + 1]
        if "--mode" in sys.argv:
            idx = sys.argv.index("--mode")
            if idx + 1 < len(sys.argv):
                mode = sys.argv[idx + 1]
        result = bridge.tribunal(prompt, k=k, tier=tier, mode=mode)
        output = {
            "prompt": result.prompt,
            "k": result.k,
            "tier": tier,
            "mode": mode,
            "elapsed_s": result.elapsed_s,
            "consensus": result.consensus,
            "consensus_report": result.consensus_report,
            "responses": [asdict(r) for r in result.responses],
        }
        print(json.dumps(output, indent=2))

    elif cmd == "tribunal-ice":
        if len(sys.argv) < 3:
            print("Usage: rhea_bridge.py tribunal-ice <prompt> [--k N] [--rounds N] [--tier TIER]")
            sys.exit(1)
        if not _HAS_ANALYZER:
            print("ERROR: consensus_analyzer.py not found. Cannot run ICE mode.")
            sys.exit(1)
        prompt = sys.argv[2]
        k = 5
        rounds = 3
        tier = "cheap"
        if "--k" in sys.argv:
            idx = sys.argv.index("--k")
            if idx + 1 < len(sys.argv):
                k = int(sys.argv[idx + 1])
        if "--rounds" in sys.argv:
            idx = sys.argv.index("--rounds")
            if idx + 1 < len(sys.argv):
                rounds = int(sys.argv[idx + 1])
        if "--tier" in sys.argv:
            idx = sys.argv.index("--tier")
            if idx + 1 < len(sys.argv):
                tier = sys.argv[idx + 1]
        analyzer = ConsensusAnalyzer(bridge=bridge)
        report = analyzer.analyze_ice(prompt, k=k, rounds=rounds, tier=tier)
        print(json.dumps(report.to_dict(), indent=2))

    elif cmd == "send-chronos":
        if len(sys.argv) < 7:
            print("Usage: rhea_bridge.py send-chronos <sender> <receiver> <task_id> <type> <priority> <payload_json>")
            sys.exit(1)
        try:
            payload = json.loads(sys.argv[7])
        except json.JSONDecodeError:
            print("ERROR: Invalid JSON for payload")
            sys.exit(1)
            
        msg = ChronosMessage(
            sender=sys.argv[2],
            receiver=sys.argv[3],
            task_id=sys.argv[4],
            msg_type=sys.argv[5],
            priority=sys.argv[6],
            payload=payload
        )
        success = bridge.send_chronos(msg)
        print(json.dumps({"success": success, "message": "CHRONOS message logged and relayed"}, indent=2))

    elif cmd == "daily-summary":
        date_arg = None
        if len(sys.argv) >= 3:
            date_arg = sys.argv[2]  # e.g. "2026-02-16"
        print(daily_summary(date_filter=date_arg))

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
