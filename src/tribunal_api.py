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
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).parent))
RULIAD_ROOT = Path(__file__).parent.parent / "friends" / "ruliad" / "explorer"
sys.path.insert(0, str(RULIAD_ROOT))
from rhea_bridge import RheaBridge
from consensus_analyzer import ConsensusAnalyzer, math_augment, detect_math_domains
from rhea_profile_manager import profile_manager
from rhea_visual_context import update_state, get_health_history

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

# ---------------------------------------------------------------------------
# Session history (in-memory, reset on process restart)
# ---------------------------------------------------------------------------

_session_history: list[dict] = []

# ---------------------------------------------------------------------------
# Ontology state
# ---------------------------------------------------------------------------

_active_ontology: str = "general"

ONTOLOGY_PROMPTS: dict[str, str] = {
    "general": "",
    "pharmacology": (
        "You are analyzing this from a pharmacological perspective. "
        "Consider drug interactions, receptor binding, dose-response relationships, and ADME properties."
    ),
    "biochemistry": (
        "You are analyzing this from a biochemistry perspective. "
        "Consider molecular mechanisms, enzyme kinetics, metabolic pathways, and protein structure-function."
    ),
    "logic": (
        "You are analyzing this from a formal logic perspective. "
        "Consider logical consistency, proof structure, axiom systems, and inference rules."
    ),
    "topology": (
        "You are analyzing this from a topological perspective. "
        "Consider continuity, connectedness, compactness, and homeomorphic invariants."
    ),
    "systems_biology": (
        "You are analyzing this from a systems biology perspective. "
        "Consider network dynamics, feedback loops, emergent properties, and multi-scale interactions."
    ),
}

# ---------------------------------------------------------------------------
# Ruliad math engine (lazy-loaded, plugin auto-discovery)
# ---------------------------------------------------------------------------

_ont_engine = None


def _get_engine():
    global _ont_engine
    if _ont_engine is None:
        from core.engine import OntologyEngine
        _ont_engine = OntologyEngine(project_root=Path(__file__).parent.parent)
        for pf in sorted((RULIAD_ROOT / "plugins").glob("*.py")):
            if not pf.name.startswith("_"):
                try:
                    g = {"__file__": str(pf)}
                    exec(pf.read_text(), g)
                    if "register_plugin" in g:
                        g["register_plugin"](_ont_engine)
                except Exception as e:
                    print(f"[math-verify] plugin load failed: {pf.stem}: {e}")
    return _ont_engine


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


class MathVerifyRequest(BaseModel):
    hypothesis: str
    domain: str = "general"
    skip_tribunal: bool = False


# ---------------------------------------------------------------------------
# New request/response models — sceptic, session rewind, ontology switch
# ---------------------------------------------------------------------------

class TribunalScepticRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000, description="The question to send to the sceptic tribunal")
    k: int = Field(default=5, ge=2, le=10, description="Number of models to query (2-10)")
    tier: str = Field(default="cheap", description="Cost tier: cheap, balanced, expensive")
    system: str = Field(default="", max_length=2000, description="Optional system prompt")
    devil_advocate: bool = Field(default=True, description="When True, models actively critique the consensus answer")


class TribunalScepticResponse(BaseModel):
    prompt: str
    k: int
    elapsed_s: float
    consensus: str
    agreement_score: float
    confidence: float
    models_responded: int
    models_queried: int
    counterarguments: list[str]
    strongest_challenge: str
    responses: list  # list[ModelInfo] — reuse existing model
    meta: dict = {}


class SessionRewindRequest(BaseModel):
    step: int = Field(..., ge=0, description="Zero-based index of the history step to rewind to")


class OntologySwitchRequest(BaseModel):
    ontology: str = Field(
        ...,
        description="Ontology lens to apply to all subsequent tribunal calls. "
                    "Valid values: general, pharmacology, biochemistry, logic, topology, systems_biology",
    )


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
    math_verification: dict = {}
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
    math_verification: dict = {}
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

@app.get("/actuator/health")
async def actuator_health():
    """Returns historical health pulses for the MRI heatmap."""
    return get_health_history()

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

    # Prepend active ontology prompt when a non-default ontology is selected
    effective_system = req.system
    if _active_ontology != "general":
        ontology_prefix = ONTOLOGY_PROMPTS.get(_active_ontology, "")
        if ontology_prefix:
            effective_system = (ontology_prefix + "\n\n" + req.system).strip()

    result = bridge.tribunal(
        prompt=req.prompt,
        k=req.k,
        tier=req.tier,
        mode=req.mode,
        system=effective_system,
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

    # --- Math augmentation: if prompt touches math domains, enrich with Ruliad ---
    math_ver = {}
    if detect_math_domains(req.prompt):
        try:
            from consensus_analyzer import ConsensusReport as _CR, run_math_verification
            engine = _get_engine()
            _tmp = _CR(
                confidence=report.get("confidence", 0.0),
                agreement_score=report.get("agreement_score", 0.0),
                analysis_method=report.get("analysis_method", "unknown"),
            )
            _tmp = math_augment(_tmp, req.prompt, engine)
            math_ver = _tmp.math_verification
            report["confidence"] = _tmp.confidence
            report["agreement_score"] = _tmp.agreement_score
            report["analysis_method"] = _tmp.analysis_method
        except Exception as e:
            math_ver = {"error": str(e)}

    _log_api_call("/tribunal", req.dict(), elapsed, "ok")

    tribunal_response = TribunalResponse(
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
        math_verification=math_ver,
        meta=report.get("meta", {}),
    )

    # Append to session history for rewind support
    _session_history.append({
        "step": len(_session_history),
        "endpoint": "/tribunal",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request": req.dict(),
        "ontology": _active_ontology,
        "response": tribunal_response.dict(),
    })

    return tribunal_response


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

    # --- Math augmentation for ICE ---
    math_ver = {}
    if detect_math_domains(req.prompt):
        try:
            engine = _get_engine()
            report = math_augment(report, req.prompt, engine)
            math_ver = report.math_verification
            rd = report.to_dict()  # refresh dict from augmented report
        except Exception as e:
            math_ver = {"error": str(e)}

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
        math_verification=math_ver,
        meta=rd.get("meta", {}),
    )


@app.post("/tribunal/math-verify", dependencies=[Depends(verify_api_key)])
async def math_verify(req: MathVerifyRequest):
    from core.engine import Hypothesis
    engine = _get_engine()
    h = Hypothesis(title=req.hypothesis[:80], statement=req.hypothesis, domain=req.domain)
    results = {}
    for name in engine.registry.list_plugins():
        p = engine.registry.get(name)
        if p and p.verify:
            try:
                results[name] = p.verify(h)
            except Exception as e:
                results[name] = {"error": str(e)}
    verdicts = {k: v.get("overall", "unknown") for k, v in results.items() if isinstance(v, dict)}
    return {"hypothesis": req.hypothesis, "plugin_results": results, "verdicts": verdicts}


# ---------------------------------------------------------------------------
# POST /tribunal/sceptic — Adversarial / Devil's-Advocate Tribunal
# ---------------------------------------------------------------------------

@app.post("/tribunal/sceptic", response_model=TribunalScepticResponse, dependencies=[Depends(verify_api_key), Depends(check_rate_limit)])
async def tribunal_sceptic(req: TribunalScepticRequest):
    """
    Adversarial tribunal: query k models for an initial answer, then have each
    model actively critique the best (consensus) answer.  Returns both the
    consensus position AND the strongest counterarguments found.
    """
    t0 = time.time()
    bridge = get_bridge()

    # Prepend active ontology prefix (same logic as /tribunal)
    effective_system = req.system
    if _active_ontology != "general":
        ontology_prefix = ONTOLOGY_PROMPTS.get(_active_ontology, "")
        if ontology_prefix:
            effective_system = (ontology_prefix + "\n\n" + req.system).strip()

    # Step 1: initial tribunal pass for consensus
    result = bridge.tribunal(
        prompt=req.prompt,
        k=req.k,
        tier=req.tier,
        mode="local",
        system=effective_system,
    )
    report = result.consensus_report
    consensus_text = report.get("consensus_text", result.consensus)

    # Step 2: each model critiques the consensus (devil's advocate mode)
    counterarguments: list[str] = []
    if req.devil_advocate:
        critique_prompt = (
            f"The following answer was produced by an AI consensus panel:\n\n"
            f"\"\"\"\n{consensus_text}\n\"\"\"\n\n"
            f"Original question: {req.prompt}\n\n"
            f"Your task: identify the strongest flaw, gap, or counterargument against this consensus answer. "
            f"Be specific and adversarial. Do NOT simply agree with the consensus."
        )
        for r in result.responses:
            if r.error:
                continue
            try:
                critique_result = bridge.ask(
                    prompt=critique_prompt,
                    model=r.model,
                    system="You are a critical adversary. Your job is to find flaws, not to agree.",
                    tier=req.tier,
                )
                critique_text = critique_result.text.strip() if hasattr(critique_result, "text") else str(critique_result).strip()
                if critique_text:
                    counterarguments.append(critique_text)
            except Exception as exc:
                counterarguments.append(f"[critique error from {r.model}: {exc}]")

    # Step 3: determine the strongest single challenge
    strongest_challenge = ""
    if counterarguments:
        if len(counterarguments) == 1:
            strongest_challenge = counterarguments[0]
        else:
            # Ask a cheap model to synthesise the most potent challenge
            try:
                synthesis_prompt = (
                    f"Below are {len(counterarguments)} critiques of a consensus answer.\n\n"
                    + "\n\n---\n\n".join(f"Critique {i+1}:\n{c}" for i, c in enumerate(counterarguments))
                    + "\n\nSynthesize these into a single, maximally powerful counterargument in 3-5 sentences."
                )
                synth = bridge.ask(prompt=synthesis_prompt, tier=req.tier)
                strongest_challenge = synth.text.strip() if hasattr(synth, "text") else str(synth).strip()
            except Exception:
                strongest_challenge = counterarguments[0]

    elapsed = time.time() - t0

    response_models = [
        ModelInfo(
            model=r.model,
            provider=r.provider,
            text=r.text,
            latency_s=r.latency_s,
            tokens_used=r.tokens_used,
            error=r.error,
        )
        for r in result.responses
    ]

    _log_api_call("/tribunal/sceptic", req.dict(), elapsed, "ok")

    sceptic_response = TribunalScepticResponse(
        prompt=req.prompt,
        k=req.k,
        elapsed_s=round(elapsed, 2),
        consensus=consensus_text,
        agreement_score=report.get("agreement_score", 0.0),
        confidence=report.get("confidence", 0.0),
        models_responded=report.get("successful_count", len([r for r in result.responses if not r.error])),
        models_queried=report.get("model_count", len(result.responses)),
        counterarguments=counterarguments,
        strongest_challenge=strongest_challenge,
        responses=response_models,
        meta=report.get("meta", {}),
    )

    # Append to session history
    _session_history.append({
        "step": len(_session_history),
        "endpoint": "/tribunal/sceptic",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request": req.dict(),
        "ontology": _active_ontology,
        "response": sceptic_response.dict(),
    })

    return sceptic_response


# ---------------------------------------------------------------------------
# GET /session/history  +  POST /session/rewind
# ---------------------------------------------------------------------------

@app.get("/session/history", dependencies=[Depends(verify_api_key)])
async def session_history():
    """Return the list of all tribunal calls made in this session (in order)."""
    return {
        "session_length": len(_session_history),
        "history": [
            {
                "step": entry["step"],
                "endpoint": entry["endpoint"],
                "timestamp": entry["timestamp"],
                "ontology": entry.get("ontology", "general"),
                "prompt": entry["request"].get("prompt", ""),
                "consensus": entry["response"].get("consensus", ""),
            }
            for entry in _session_history
        ],
    }


@app.post("/session/rewind", dependencies=[Depends(verify_api_key)])
async def session_rewind(req: SessionRewindRequest):
    """
    Rewind session context to step N.  Returns the full request+response state
    recorded at that step so callers can restore their own context to that point.
    The in-memory history is NOT truncated — rewind is non-destructive.
    """
    if not _session_history:
        raise HTTPException(status_code=404, detail="Session history is empty — no steps to rewind to")
    if req.step >= len(_session_history):
        raise HTTPException(
            status_code=400,
            detail=f"Step {req.step} does not exist. History has {len(_session_history)} step(s) (0-indexed).",
        )
    entry = _session_history[req.step]
    return {
        "rewound_to_step": req.step,
        "total_steps": len(_session_history),
        "endpoint": entry["endpoint"],
        "timestamp": entry["timestamp"],
        "ontology": entry.get("ontology", "general"),
        "request": entry["request"],
        "response": entry["response"],
    }


# ---------------------------------------------------------------------------
# POST /ontology/switch  +  GET /ontology
# ---------------------------------------------------------------------------

@app.get("/ontology", dependencies=[Depends(verify_api_key)])
async def get_ontology():
    """Return the currently active ontology and all available options."""
    return {
        "active": _active_ontology,
        "available": list(ONTOLOGY_PROMPTS.keys()),
        "active_prompt": ONTOLOGY_PROMPTS.get(_active_ontology, ""),
    }


@app.post("/ontology/switch", dependencies=[Depends(verify_api_key)])
async def ontology_switch(req: OntologySwitchRequest):
    """
    Switch the active research ontology lens.  All subsequent /tribunal calls
    will have the chosen ontology's system-prompt prefix prepended to their
    system field until a new ontology is selected.
    """
    global _active_ontology
    if req.ontology not in ONTOLOGY_PROMPTS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown ontology '{req.ontology}'. "
                f"Valid values: {', '.join(ONTOLOGY_PROMPTS.keys())}"
            ),
        )
    previous = _active_ontology
    _active_ontology = req.ontology
    return {
        "status": "ok",
        "previous": previous,
        "active": _active_ontology,
        "prompt_prefix": ONTOLOGY_PROMPTS[_active_ontology],
    }


# ---------------------------------------------------------------------------
# Demo endpoints (no auth required — first-user showcase)
# ---------------------------------------------------------------------------

# Canonical showcase hypotheses, one per plugin domain
_DEMO_HYPOTHESES = {
    "game_theory": (
        "In a 2-player Prisoner's Dilemma, mutual cooperation is not a Nash equilibrium"
    ),
    "dynamical_systems": (
        "The Lorenz system exhibits sensitive dependence on initial conditions"
    ),
    "information_geometry": (
        "The Gaussian family forms a regular statistical manifold with positive-definite Fisher metric"
    ),
    "proof_theory": (
        "If knowledge implies belief, and belief implies commitment, then knowledge implies commitment"
    ),
    "category_theory": (
        "The symmetric group S3 satisfies associativity and identity axioms"
    ),
}

_DOMAIN_ORDER = [
    "game_theory",
    "dynamical_systems",
    "information_geometry",
    "proof_theory",
    "category_theory",
]


def _extract_key_values(domain: str, result: dict) -> dict:
    """Pull 1-2 interesting computed values out of a plugin verify() result."""
    checks = result.get("checks", [])

    if domain == "game_theory":
        mixed = next((c for c in checks if c.get("check") == "mixed_nash_equilibrium"), {})
        pure = next((c for c in checks if c.get("check") == "pure_nash_equilibrium"), {})
        return {
            "game_value": mixed.get("game_value"),
            "pure_nash_cells": pure.get("pure_nash_cells", []),
            "mixed_nash_computed": mixed.get("exists", False),
        }

    if domain == "dynamical_systems":
        chaos = next((c for c in checks if c.get("check") == "positive_lyapunov_exponent_proxy"), {})
        stab = next((c for c in checks if "eigenvalue_stability" in c.get("check", "")), {})
        return {
            "system": result.get("system"),
            "lambda_proxy": chaos.get("lambda_proxy"),
            "chaos_detected": chaos.get("status") == "verified",
            "first_equilibrium_stability": stab.get("stability_class"),
        }

    if domain == "information_geometry":
        pd = next((c for c in checks if c.get("check") == "positive_definiteness"), {})
        kl = next((c for c in checks if c.get("check") == "kl_divergence_sanity"), {})
        return {
            "fisher_min_eigenvalue": pd.get("min_eigenvalue"),
            "fisher_is_positive_definite": pd.get("is_positive_definite"),
            "kl_divergence": kl.get("kl_value"),
            "kl_label": kl.get("label"),
        }

    if domain == "proof_theory":
        taut = next((c for c in checks if c.get("check") == "tautology"), {})
        cons = next((c for c in checks if c.get("check") == "logical_consistency"), {})
        return {
            "is_tautology": taut.get("status") == "tautology",
            "is_consistent": cons.get("status") == "consistent",
            "atoms": result.get("atoms", []),
            "tautology_note": taut.get("note", ""),
        }

    if domain == "category_theory":
        assoc = next((c for c in checks if c.get("check") == "associativity"), {})
        identity = next((c for c in checks if c.get("check") == "identity"), {})
        return {
            "finite_model": result.get("finite_model_used"),
            "associativity": assoc.get("status"),
            "identity_element": identity.get("detail", ""),
        }

    return {}


def _run_demo_domain(domain: str) -> dict:
    """Run a single domain through the math-verify pipeline. Returns a result dict."""
    from core.engine import Hypothesis as _Hypothesis
    hypothesis_text = _DEMO_HYPOTHESES[domain]
    engine = _get_engine()
    plugin = engine.registry.get(domain)
    if plugin is None:
        return {
            "domain": domain,
            "hypothesis": hypothesis_text,
            "verdict": "plugin_not_loaded",
            "key_values": {},
            "error": f"Plugin '{domain}' not registered",
        }
    h = _Hypothesis(
        title=hypothesis_text[:80],
        statement=hypothesis_text,
        domain=domain,
    )
    try:
        result = plugin.verify(h)
        verdict = result.get("overall", "unknown")
        key_values = _extract_key_values(domain, result)
        return {
            "domain": domain,
            "hypothesis": hypothesis_text,
            "verdict": verdict,
            "key_values": key_values,
        }
    except Exception as exc:
        return {
            "domain": domain,
            "hypothesis": hypothesis_text,
            "verdict": "error",
            "key_values": {},
            "error": str(exc),
        }


@app.get("/demo/math")
async def demo_math_all():
    """
    One-click demo: run all 5 Ruliad math plugins on canonical showcase hypotheses.
    No authentication required.
    """
    t0 = time.time()
    results = []
    success_count = 0

    for domain in _DOMAIN_ORDER:
        dr = _run_demo_domain(domain)
        results.append(dr)
        if dr.get("verdict") not in ("error", "plugin_not_loaded"):
            success_count += 1

    elapsed = round(time.time() - t0, 3)
    return {
        "summary": f"{success_count}/{len(_DOMAIN_ORDER)} plugins computed real mathematical verification",
        "elapsed_s": elapsed,
        "plugins_run": len(_DOMAIN_ORDER),
        "plugins_succeeded": success_count,
        "results": results,
    }


@app.get("/demo/math/{domain}")
async def demo_math_domain(domain: str):
    """
    Single-domain demo: run one Ruliad math plugin on its canonical showcase hypothesis.
    Valid domains: game_theory, dynamical_systems, information_geometry, proof_theory, category_theory.
    No authentication required.
    """
    if domain not in _DEMO_HYPOTHESES:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Unknown domain '{domain}'. "
                f"Valid domains: {', '.join(_DOMAIN_ORDER)}"
            ),
        )
    t0 = time.time()
    result = _run_demo_domain(domain)
    elapsed = round(time.time() - t0, 3)
    return {
        "elapsed_s": elapsed,
        **result,
    }


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
    import logging
    # Suppress verbose logging
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    port = int(os.environ.get("TRIBUNAL_PORT", "8400"))
    # Run silently
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
