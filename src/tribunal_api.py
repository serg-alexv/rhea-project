#!/usr/bin/env python3
"""
tribunal_api.py — FastAPI wrapper for Rhea Tribunal consensus API.

Endpoints:
    POST /tribunal          — Level 1 (local) or Level 2 (chairman) consensus
    POST /tribunal/ice      — Level 3 (ICE iterative) consensus
    GET  /health            — Health check
    GET  /models            — Available models and providers

Usage:
    uvicorn tribunal_api:app --host 0.0.0.0 --port 8400
    # or: python3 src/tribunal_api.py
"""
from __future__ import annotations

import os
import sys
import time
import json
import hashlib
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).parent))
from rhea_bridge import RheaBridge
from consensus_analyzer import ConsensusAnalyzer
from rhea_profile_manager import profile_manager
from rhea_visual_context import update_state

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Rhea Tribunal API",
    description="Multi-model consensus as a service. Send a prompt, get structured agreement analysis across 3-7 AI models.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Singleton bridge + analyzer
_bridge = None
_analyzer = None
_command_queue: list[dict] = []
_receipts: dict[str, dict] = {}


def get_bridge() -> RheaBridge:
    global _bridge
    if _bridge is None:
        _bridge = RheaBridge()
    return _bridge


def get_analyzer() -> ConsensusAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = ConsensusAnalyzer(bridge=get_bridge())
    return _analyzer


# ---------------------------------------------------------------------------
# API key auth (simple token-based, production would use DB)
# ---------------------------------------------------------------------------

TRIBUNAL_API_KEYS = set()
_keys_env = os.environ.get("TRIBUNAL_API_KEYS", "")
if _keys_env:
    TRIBUNAL_API_KEYS = {k.strip() for k in _keys_env.split(",") if k.strip()}

# If no keys configured, generate a dev key on startup
if not TRIBUNAL_API_KEYS:
    _dev_key = "dev-" + secrets.token_hex(16)
    TRIBUNAL_API_KEYS.add(_dev_key)


async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    if not TRIBUNAL_API_KEYS:
        # FAIL-CLOSED: No keys configured means no one gets in.
        raise HTTPException(status_code=401, detail="API is locked: No keys configured in TRIBUNAL_API_KEYS")
    if not x_api_key or x_api_key not in TRIBUNAL_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# ---------------------------------------------------------------------------
# Rate limiting (in-memory token bucket, per API key)
# ---------------------------------------------------------------------------

RATE_LIMIT_PER_MINUTE = int(os.environ.get("TRIBUNAL_RATE_LIMIT", "30"))
RATE_LIMIT_DAILY = int(os.environ.get("TRIBUNAL_DAILY_LIMIT", "1000"))

_rate_buckets: dict[str, list[float]] = {}


async def check_rate_limit(x_api_key: str = Header(None, alias="X-API-Key")):
    key = x_api_key or "anonymous"
    now = time.time()
    if key not in _rate_buckets:
        _rate_buckets[key] = []

    # Prune entries older than 24h
    _rate_buckets[key] = [t for t in _rate_buckets[key] if now - t < 86400]

    # Daily check
    if len(_rate_buckets[key]) >= RATE_LIMIT_DAILY:
        raise HTTPException(status_code=429, detail=f"Daily limit ({RATE_LIMIT_DAILY} calls) exceeded")

    # Per-minute check
    recent = sum(1 for t in _rate_buckets[key] if now - t < 60)
    if recent >= RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail=f"Rate limit ({RATE_LIMIT_PER_MINUTE}/min) exceeded")

    _rate_buckets[key].append(now)


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------

class TribunalRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000, description="The question to send to the tribunal")
    k: int = Field(default=5, ge=2, le=10, description="Number of models to query (2-10)")
    tier: str = Field(default="cheap", description="Cost tier: cheap, balanced, expensive")
    mode: str = Field(default="local", description="Analysis mode: local (L1, free), chairman (L2, +1 API call)")
    system: str = Field(default="", max_length=2000, description="Optional system prompt")


class TribunalICERequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000, description="The question to send to the tribunal")
    k: int = Field(default=5, ge=2, le=7, description="Number of models (2-7, ICE is expensive)")
    rounds: int = Field(default=2, ge=1, le=5, description="Max critique rounds (1-5, optimal: 2-3)")
    tier: str = Field(default="cheap", description="Cost tier for queries + critiques")
    chairman_tier: str = Field(default="balanced", description="Cost tier for final chairman synthesis")

class SetModeRequest(BaseModel):
    mode: str = Field(..., description="The mode to set as default (e.g. operator_first, loop_killer)")

class HydrateMemoryRequest(BaseModel):
    id: str = Field(..., description="The ID of the memory entity to load (e.g. ORION.md)")

class VisualSyncRequest(BaseModel):
    tab_id: int
    state: dict

class ActuatorCommand(BaseModel):
    action: str # CLICK, TYPE, SCROLL
    elementId: Optional[int] = None
    text: Optional[str] = None
    tab_id: Optional[int] = None

class ActuatorReceipt(BaseModel):
    command_id: str
    status: str
    error: Optional[str] = None


class ModelInfo(BaseModel):
    model: str
    provider: str
    text: str
    latency_s: float
    tokens_used: int
    error: Optional[str] = None


class TribunalResponse(BaseModel):
    prompt: str
    k: int
    mode: str
    elapsed_s: float
    consensus: str
    agreement_score: float
    confidence: float
    models_responded: int
    models_queried: int
    analysis_method: str
    agreement_points: list
    divergence_points: list
    stance_summary: dict
    responses: list[ModelInfo]
    meta: dict = {}


class TribunalICEResponse(BaseModel):
    prompt: str
    k: int
    rounds_completed: int
    convergence_achieved: bool
    elapsed_s: float
    consensus: str
    agreement_score: float
    confidence: float
    chairman_model: str
    analysis_method: str
    round_history: list
    agreement_points: list
    divergence_points: list
    stance_summary: dict
    meta: dict = {}


# ---------------------------------------------------------------------------
# Call logging (with secret redaction)
# ---------------------------------------------------------------------------

CALL_LOG = Path(__file__).parent.parent / "logs" / "tribunal_api_calls.jsonl"

# Import redaction from bridge
from rhea_bridge import redact_secrets


def _log_api_call(endpoint: str, request_data: dict, elapsed_s: float, status: str):
    CALL_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "prompt_hash": hashlib.sha256(request_data.get("prompt", "").encode()).hexdigest()[:16],
        "k": request_data.get("k", 0),
        "elapsed_s": elapsed_s,
        "status": status,
    }
    with open(CALL_LOG, "a") as f:
        f.write(redact_secrets(json.dumps(entry)) + "\n")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    bridge = get_bridge()
    status = bridge.models_status()
    return {
        "status": "ok",
        "providers_available": status["summary"]["available_providers"],
        "providers_total": status["summary"]["total_providers"],
        "total_models": status["summary"]["total_models"],
        "analyzer_version": "v2-ice-council",
        "profile_mode": profile_manager.get_active_mode(),
    }


@app.get("/models")
async def models():
    bridge = get_bridge()
    return bridge.models_status()

@app.get("/modes")
async def get_modes():
    """Get active and available cognitive stance modes."""
    return {
        "active": profile_manager.get_active_mode(),
        "available": profile_manager.get_available_modes(),
    }

@app.get("/memories")
async def get_memories():
    """List available memory entities (Nexus branches, snapshots)."""
    return profile_manager.list_memory_entities()

@app.post("/memories/hydrate", dependencies=[Depends(verify_api_key)])
async def hydrate_memory(req: HydrateMemoryRequest):
    """Arm the system with a specific memory entity."""
    if profile_manager.hydrate_memory(req.id):
        return {"status": "ok", "armed_with": req.id}
    else:
        raise HTTPException(status_code=400, detail=f"Memory entity not found: {req.id}")

@app.post("/actuator/sync", dependencies=[Depends(verify_api_key)])
async def actuator_sync(req: VisualSyncRequest):
    """Receive visual state from the browser extension."""
    update_state(req.state)
    print(f"[Actuator] Sync from Tab {req.tab_id}: {req.state['url']}")
    return {"status": "ok"}

@app.post("/actuator/command", dependencies=[Depends(verify_api_key)])
async def actuator_command(req: ActuatorCommand):
    """Queue a command for the browser extension to execute."""
    command_id = str(uuid.uuid4())[:8]
    cmd = req.dict()
    cmd["id"] = command_id
    _command_queue.append(cmd)
    print(f"[Actuator] Queued Command {command_id}: {req.action}")
    return {"status": "ok", "command_id": command_id}

@app.get("/actuator/command")
async def actuator_get_command():
    """Extension polls this to get the next command."""
    if not _command_queue:
        return {"status": "empty"}
    return _command_queue.pop(0)

@app.post("/actuator/receipt")
async def actuator_receipt(req: ActuatorReceipt):
    """Extension reports the result of a command."""
    _receipts[req.command_id] = req.dict()
    print(f"[Actuator] Receipt for {req.command_id}: {req.status}")
    return {"status": "ok"}

@app.post("/modes", dependencies=[Depends(verify_api_key)])
async def set_mode(req: SetModeRequest):
    """Set the active cognitive stance mode (Hot Swap)."""
    if profile_manager.set_active_mode(req.mode):
        return {"status": "ok", "active": req.mode}
    else:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {req.mode}")

@app.post("/tribunal", response_model=TribunalResponse, dependencies=[Depends(verify_api_key), Depends(check_rate_limit)])
async def tribunal(req: TribunalRequest):
    t0 = time.time()
    bridge = get_bridge()

    result = bridge.tribunal(
        prompt=req.prompt,
        k=req.k,
        tier=req.tier,
        mode=req.mode,
        system=req.system,
    )

    elapsed = time.time() - t0
    report = result.consensus_report

    response_models = []
    for r in result.responses:
        response_models.append(ModelInfo(
            model=r.model,
            provider=r.provider,
            text=r.text,
            latency_s=r.latency_s,
            tokens_used=r.tokens_used,
            error=r.error,
        ))

    _log_api_call("/tribunal", req.dict(), elapsed, "ok")

    return TribunalResponse(
        prompt=req.prompt,
        k=req.k,
        mode=req.mode,
        elapsed_s=round(elapsed, 2),
        consensus=report.get("consensus_text", result.consensus),
        agreement_score=report.get("agreement_score", 0.0),
        confidence=report.get("confidence", 0.0),
        models_responded=report.get("successful_count", len([r for r in result.responses if not r.error])),
        models_queried=report.get("model_count", len(result.responses)),
        analysis_method=report.get("analysis_method", "unknown"),
        agreement_points=report.get("agreement_points", []),
        divergence_points=report.get("divergence_points", []),
        stance_summary=report.get("stance_summary", {}),
        responses=response_models,
        meta=report.get("meta", {}),
    )


@app.post("/tribunal/ice", response_model=TribunalICEResponse, dependencies=[Depends(verify_api_key), Depends(check_rate_limit)])
async def tribunal_ice(req: TribunalICERequest):
    t0 = time.time()
    analyzer = get_analyzer()

    report = analyzer.analyze_ice(
        prompt=req.prompt,
        k=req.k,
        rounds=req.rounds,
        tier=req.tier,
        chairman_tier=req.chairman_tier,
    )

    elapsed = time.time() - t0
    rd = report.to_dict()

    _log_api_call("/tribunal/ice", req.dict(), elapsed, "ok")

    return TribunalICEResponse(
        prompt=req.prompt,
        k=req.k,
        rounds_completed=rd.get("rounds_completed", 0),
        convergence_achieved=rd.get("convergence_achieved", False),
        elapsed_s=round(elapsed, 2),
        consensus=rd.get("consensus_text", ""),
        agreement_score=rd.get("agreement_score", 0.0),
        confidence=rd.get("confidence", 0.0),
        chairman_model=rd.get("chairman_model", ""),
        analysis_method=rd.get("analysis_method", ""),
        round_history=rd.get("round_history", []),
        agreement_points=rd.get("agreement_points", []),
        divergence_points=rd.get("divergence_points", []),
        stance_summary=rd.get("stance_summary", {}),
        meta=rd.get("meta", {}),
    )


# ---------------------------------------------------------------------------
# Startup event
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup():
    # Print dev key if auto-generated
    if _keys_env == "":
        print(f"\n  Dev API key: {_dev_key}")
        print(f"  Usage: curl -H 'X-API-Key: {_dev_key}' -X POST ...\n")


# ---------------------------------------------------------------------------
# Direct execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("TRIBUNAL_PORT", "8400"))
    print(f"Starting Rhea Tribunal API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
