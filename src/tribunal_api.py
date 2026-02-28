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
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Global event bus — SSE radio frequency for all agents
# ---------------------------------------------------------------------------
import asyncio
import collections

_EVENT_BUS: asyncio.Queue = None  # lazy-init per event loop
_SUBSCRIBERS: list = []  # list of asyncio.Queue (one per SSE client)

def _broadcast_event(event: dict):
    """Push event to all connected SSE subscribers."""
    dead = []
    for q in _SUBSCRIBERS:
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _SUBSCRIBERS.remove(q)

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).parent))
RULIAD_ROOT = Path(__file__).parent.parent / "friends" / "ruliad" / "explorer"
sys.path.insert(0, str(RULIAD_ROOT))

from rhea_bridge import RheaBridge
from consensus_analyzer import ConsensusAnalyzer, math_augment, detect_math_domains
from rhea_profile_manager import profile_manager
from rhea_visual_context import update_state, get_health_history
import aletheia_pipeline as aletheia
from aletheia_api import aletheia_router

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Rhea Tribunal API",
    description="Multi-model consensus as a service. Send a prompt, get structured agreement analysis across 3-7 AI models.",
    version="0.1.0",
)

# Expose Aletheia read-only endpoints under /api/aletheia (mirrors rhead /aletheia)
app.include_router(aletheia_router, prefix="/aletheia")

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


class OfficeActionRequest(BaseModel):
    action: str = Field(..., description="wake|boot|drain|lease|ping")
    target: str = Field(default="ALL", description="Agent desk name or ALL")
    source: str = Field(default="ORION", description="Sender desk for ping")
    message: str = Field(default="UI pulse check-in", max_length=4000)
    priority: str = Field(default="P1")
    ttl_s: int = Field(default=86400, ge=60, le=604800)


class ExecutionProfileRequest(BaseModel):
    profile: str = Field(..., description="safe_cheap|balanced|deep")


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
BRIDGE_CALL_LOG = Path(__file__).parent.parent / "logs" / "bridge_calls.jsonl"
OFFICE_ROOT = _PROJECT_ROOT / "opera" / "ops" / "virtual-office"
OFFICE_MAILBOX_LOG = OFFICE_ROOT / "relay_mailbox.jsonl"
OFFICE_ACKS_LOG = OFFICE_ROOT / "relay_acks.jsonl"
OFFICE_LEASES_DIR = OFFICE_ROOT / "leases"
OFFICE_SNAPSHOTS_DIR = OFFICE_ROOT / "snapshots"
REX_PAGER_PATH = _PROJECT_ROOT / "opera" / "ops" / "rex_pager.py"

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


def _parse_ts(ts: str) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def _hour_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _read_jsonl_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records: list[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if isinstance(rec, dict):
                records.append(rec)
    return records


def _message_body(msg: dict) -> str:
    payload = msg.get("payload")
    if isinstance(payload, dict):
        body = payload.get("body")
        if isinstance(body, str) and body.strip():
            return body.strip()
        nested = payload.get("payload")
        if isinstance(nested, dict):
            for key in ("instruction", "note", "context", "topic", "action"):
                val = nested.get(key)
                if isinstance(val, str) and val.strip():
                    return val.strip()
        return json.dumps(payload, ensure_ascii=False)[:500]
    return str(payload or "")[:500]


def _is_question_msg(msg: dict, body: str) -> bool:
    msg_type = str(msg.get("type") or "").lower()
    if "request" in msg_type:
        return True
    payload = msg.get("payload")
    if isinstance(payload, dict) and str(payload.get("msg_type") or "").lower() == "request":
        return True
    body_l = body.lower()
    if "?" in body:
        return True
    if "reply" in body_l or "please report" in body_l or "status check" in body_l:
        return True
    return False


def _summarize_office_state() -> dict:
    now = datetime.now(timezone.utc)
    mailbox = _read_jsonl_records(OFFICE_MAILBOX_LOG)
    ack_records = _read_jsonl_records(OFFICE_ACKS_LOG)
    acked_ids = {
        str(rec.get("message_id", "")).strip()
        for rec in ack_records
        if str(rec.get("message_id", "")).strip()
    }

    pending_by_target: dict[str, list[dict]] = {}
    queue_preview: list[dict] = []
    pending_total_count = 0
    for msg in mailbox:
        msg_id = str(msg.get("id", "")).strip()
        if msg_id and msg_id in acked_ids:
            continue
        pending_total_count += 1
        target = str(msg.get("target", "")).upper().strip() or "UNKNOWN"
        body = _message_body(msg)
        ts = _parse_ts(str(msg.get("timestamp", "")))
        age_min = None
        if ts:
            age_min = max(0.0, (now - ts).total_seconds() / 60.0)
        is_question = _is_question_msg(msg, body)
        pending_entry = {
            "id": msg_id,
            "seq": int(msg.get("seq") or 0),
            "source": str(msg.get("source") or "unknown"),
            "target": target,
            "priority": str(msg.get("priority") or "P1"),
            "type": str(msg.get("type") or "msg.send"),
            "timestamp": msg.get("timestamp"),
            "age_min": round(age_min, 1) if age_min is not None else None,
            "body": body,
            "is_question": is_question,
        }
        pending_by_target.setdefault(target, []).append(pending_entry)
        queue_preview.append(pending_entry)

    leases: dict[str, dict] = {}
    if OFFICE_LEASES_DIR.exists():
        for path in OFFICE_LEASES_DIR.glob("*.json"):
            lease = _read_json_file(path)
            agent = str(lease.get("agent") or path.stem).upper().strip()
            if agent:
                leases[agent] = lease

    snapshots: dict[str, dict] = {}
    if OFFICE_SNAPSHOTS_DIR.exists():
        for path in OFFICE_SNAPSHOTS_DIR.glob("*.json"):
            snap = _read_json_file(path)
            agent = str(snap.get("agent") or path.stem).upper().strip()
            if agent:
                snapshots[agent] = snap

    agents = sorted(set(leases.keys()) | set(snapshots.keys()) | set(pending_by_target.keys()))
    rows = []
    for agent in agents:
        pending = pending_by_target.get(agent, [])
        pending_count = len(pending)
        question_count = sum(1 for p in pending if p["is_question"])
        oldest_pending_min = max((float(p["age_min"]) for p in pending if p["age_min"] is not None), default=0.0)
        newest_pending_ts = None
        if pending:
            newest_pending = max(
                pending,
                key=lambda p: p["seq"],
            )
            newest_pending_ts = newest_pending.get("timestamp")

        lease = leases.get(agent, {})
        lease_expires_at = str(lease.get("expires_at") or "")
        lease_renewed_at = str(lease.get("renewed_at") or lease.get("acquired_at") or "")
        lease_expired = True
        lease_ts = _parse_ts(lease_expires_at)
        if lease_ts:
            lease_expired = lease_ts <= now

        snap = snapshots.get(agent, {})
        snapshot_saved_at = str(snap.get("saved_at") or "")
        last_activity = None
        for ts in (lease_renewed_at, snapshot_saved_at, newest_pending_ts):
            dt = _parse_ts(str(ts))
            if dt and (last_activity is None or dt > last_activity):
                last_activity = dt

        if pending_count > 0 and lease_expired:
            status = "stuck"
        elif question_count > 0:
            status = "needs_attention"
        elif lease and not lease_expired:
            status = "alive"
        elif pending_count > 0:
            status = "needs_attention"
        else:
            status = "idle"

        rows.append(
            {
                "agent": agent,
                "status": status,
                "lease_token": int(lease.get("lease_token") or 0),
                "lease_expired": lease_expired,
                "lease_expires_at": lease_expires_at or None,
                "lease_renewed_at": lease_renewed_at or None,
                "snapshot_last_seq": int(snap.get("last_seq_applied") or 0),
                "snapshot_saved_at": snapshot_saved_at or None,
                "pending_count": pending_count,
                "question_count": question_count,
                "oldest_pending_min": round(oldest_pending_min, 1) if pending_count else 0.0,
                "last_activity_at": last_activity.isoformat().replace("+00:00", "Z") if last_activity else None,
            }
        )

    status_weight = {
        "stuck": 0,
        "needs_attention": 1,
        "alive": 2,
        "idle": 3,
    }
    rows.sort(
        key=lambda r: (
            status_weight.get(r["status"], 9),
            -int(r["pending_count"]),
            -int(r["question_count"]),
            r["agent"],
        )
    )

    queue_preview.sort(key=lambda m: int(m.get("seq") or 0), reverse=True)
    queue_preview = queue_preview[:14]

    return {
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "office_root": str(OFFICE_ROOT),
        "mailbox_total": len(mailbox),
        "pending_total": pending_total_count,
        "stuck_total": sum(1 for r in rows if r["status"] == "stuck"),
        "question_total": sum(int(r["question_count"]) for r in rows),
        "agents": rows,
        "queue_preview": queue_preview,
    }


def _resolve_action_targets(target: str, agent_rows: list[dict]) -> list[str]:
    raw = (target or "").strip().upper()
    if raw and raw != "ALL":
        return [raw]

    skip = {"ALL", "UNKNOWN", "PERSONAL", "--INTERVAL"}
    targets = [
        str(row.get("agent", "")).upper()
        for row in agent_rows
        if str(row.get("agent", "")).upper() not in skip
        and not str(row.get("agent", "")).startswith("--")
        and (int(row.get("pending_count", 0)) > 0 or not bool(row.get("lease_expired", True)))
    ]
    if targets:
        return sorted(set(targets))
    # Fallback set for cold starts with no pulse data.
    return ["REX", "ORION", "HYPERION", "GPT"]


def _run_rex_pager(args: list[str], timeout_s: int = 45) -> dict:
    if not REX_PAGER_PATH.exists():
        return {
            "ok": False,
            "returncode": 127,
            "stdout_tail": "",
            "stderr_tail": f"rex_pager not found: {REX_PAGER_PATH}",
            "timed_out": False,
        }
    cmd = ["python3", str(REX_PAGER_PATH), *args]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(_PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout_tail": stdout[-1600:],
            "stderr_tail": stderr[-1000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "ok": False,
            "returncode": 124,
            "stdout_tail": out[-1600:],
            "stderr_tail": err[-1000:] or f"timeout after {timeout_s}s",
            "timed_out": True,
        }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    bridge = get_bridge()
    status = bridge.models_status()
    summary = status.get("summary", {})
    return {
        "status": "ok",
        "providers_available": summary.get("available_providers", 0),
        "providers_total": summary.get("total_providers", 0),
        "total_models": summary.get("total_models", 0),
        "execution_profile": summary.get("execution_profile", "safe_cheap"),
        "analyzer_version": "v2-ice-council",
        "profile_mode": profile_manager.get_active_mode(),
    }


@app.get("/models")
async def models():
    bridge = get_bridge()
    return bridge.models_status()


@app.get("/settings/execution-profile")
async def get_execution_profile():
    bridge = get_bridge()
    return bridge.get_execution_profile()


@app.post("/settings/execution-profile", dependencies=[Depends(verify_api_key)])
async def set_execution_profile(req: ExecutionProfileRequest):
    bridge = get_bridge()
    try:
        return bridge.set_execution_profile(req.profile, source="api")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/usage/agents")
async def usage_agents(window_hours: int = 24):
    """
    Aggregate bridge token usage by agent from logs/bridge_calls.jsonl.
    Window defaults to 24h (daily live view).
    """
    window_hours = max(1, min(window_hours, 72))
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=window_hours)

    if not BRIDGE_CALL_LOG.exists():
        return {
            "window_hours": window_hours,
            "since": since.isoformat().replace("+00:00", "Z"),
            "until": now.isoformat().replace("+00:00", "Z"),
            "total_calls": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "agents": [],
            "hourly_total_tokens": [],
        }

    agents: dict[str, dict] = {}
    hourly_total: dict[str, int] = {}
    total_calls = 0
    total_tokens = 0
    total_cost = 0.0

    with open(BRIDGE_CALL_LOG, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue

            ts = _parse_ts(str(rec.get("timestamp", "")))
            if not ts or ts < since:
                continue

            agent_id = str(rec.get("agent_id") or rec.get("agent") or "unknown")
            agent_name = str(rec.get("agent_name") or "")
            tokens = int(rec.get("total_tokens") or 0)
            cost = float(rec.get("cost_usd") or 0.0)
            status = str(rec.get("status") or "")
            provider = str(rec.get("provider") or "")
            model = str(rec.get("model") or "")

            row = agents.setdefault(
                agent_id,
                {
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "calls": 0,
                    "ok_calls": 0,
                    "tokens": 0,
                    "cost_usd": 0.0,
                    "providers": {},
                    "models": {},
                    "hourly_tokens": {},
                },
            )
            if agent_name and not row["agent_name"]:
                row["agent_name"] = agent_name

            row["calls"] += 1
            if status == "ok":
                row["ok_calls"] += 1
            row["tokens"] += tokens
            row["cost_usd"] += cost
            row["providers"][provider] = row["providers"].get(provider, 0) + 1
            row["models"][model] = row["models"].get(model, 0) + 1

            hour_key = _hour_iso(ts)
            row["hourly_tokens"][hour_key] = row["hourly_tokens"].get(hour_key, 0) + tokens
            hourly_total[hour_key] = hourly_total.get(hour_key, 0) + tokens

            total_calls += 1
            total_tokens += tokens
            total_cost += cost

    agent_rows = list(agents.values())
    for row in agent_rows:
        row["cost_usd"] = round(float(row["cost_usd"]), 8)
        row["providers"] = dict(sorted(row["providers"].items(), key=lambda x: x[1], reverse=True))
        row["models"] = dict(sorted(row["models"].items(), key=lambda x: x[1], reverse=True))
        row["hourly_tokens"] = dict(sorted(row["hourly_tokens"].items()))

    agent_rows.sort(key=lambda r: (r["tokens"], r["calls"]), reverse=True)

    return {
        "window_hours": window_hours,
        "since": since.isoformat().replace("+00:00", "Z"),
        "until": now.isoformat().replace("+00:00", "Z"),
        "total_calls": total_calls,
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 8),
        "agents": agent_rows,
        "hourly_total_tokens": [
            {"hour": k, "tokens": v} for k, v in sorted(hourly_total.items())
        ],
    }


@app.get("/office/pulse", dependencies=[Depends(verify_api_key)])
async def office_pulse():
    """Live office pulse: stuck desks, pending requests, lease/snapshot health."""
    return _summarize_office_state()


@app.post("/office/action", dependencies=[Depends(verify_api_key)])
async def office_action(req: OfficeActionRequest):
    """Execute office controls via rex_pager (wake/boot/drain/lease/ping)."""
    action = (req.action or "").strip().lower()
    if action not in {"wake", "boot", "drain", "lease", "ping"}:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {req.action}")

    pulse = _summarize_office_state()
    targets = _resolve_action_targets(req.target, pulse.get("agents", []))
    if not targets:
        raise HTTPException(status_code=400, detail="No targets resolved for action")

    source = (req.source or "ORION").strip().upper()
    priority = (req.priority or "P1").strip().upper()
    message = (req.message or "UI pulse check-in").strip() or "UI pulse check-in"

    results = []
    for target in targets:
        if action == "wake":
            args = ["wake", target]
            timeout_s = 70
        elif action == "boot":
            args = ["boot", target]
            timeout_s = 70
        elif action == "drain":
            args = ["drain", target]
            timeout_s = 35
        elif action == "lease":
            args = ["lease", target, "--acquire"]
            timeout_s = 20
        else:  # ping
            args = ["send", source, target, message, "--priority", priority, "--ttl", str(req.ttl_s)]
            timeout_s = 20

        run = _run_rex_pager(args, timeout_s=timeout_s)
        run["target"] = target
        run["action"] = action
        run["args"] = args
        results.append(run)

    ok_count = sum(1 for r in results if r.get("ok"))
    return {
        "status": "ok" if ok_count == len(results) else "partial",
        "action": action,
        "targets": targets,
        "ok_count": ok_count,
        "error_count": len(results) - ok_count,
        "results": results,
    }

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

    # Broadcast tribunal result to Radio
    _broadcast_event({
        "id": f"tribunal-{int(time.time())}",
        "type": "tribunal",
        "sender": "tribunal",
        "receiver": "all",
        "text": f"[{req.mode}] {req.prompt[:100]} → confidence={tribunal_response.confidence:.0%} agreement={tribunal_response.agreement_score:.0%} ({tribunal_response.models_responded}/{tribunal_response.models_queried} models, {elapsed:.1f}s)",
        "ts": datetime.now(timezone.utc).isoformat(),
    })

    # Append to session history for rewind support
    _session_history.append({
        "step": len(_session_history),
        "endpoint": "/tribunal",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request": req.dict(),
        "ontology": _active_ontology,
        "response": tribunal_response.dict(),
    })

    # ── Aletheia capture: persist as proof/hypothesis ──
    try:
        aletheia.capture(
            tribunal_response=tribunal_response.dict(),
            consensus_report=report,
            raw_responses=[r.dict() for r in response_models],
            request_meta={
                "prompt": req.prompt, "k": req.k, "mode": req.mode,
                "ontology": _active_ontology, "session_id": None,
            },
        )
    except Exception as e:
        print(f"[aletheia] capture error: {e}")

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

    ice_response = TribunalICEResponse(
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

    # ── Aletheia capture: ICE results ──
    try:
        aletheia.capture(
            tribunal_response=ice_response.dict(),
            consensus_report=rd,
            raw_responses=rd.get("round_history", [{}])[-1].get("responses", []) if rd.get("round_history") else [],
            request_meta={
                "prompt": req.prompt, "k": req.k, "mode": "ice",
                "ontology": _active_ontology, "session_id": None,
            },
        )
    except Exception as e:
        print(f"[aletheia] ICE capture error: {e}")

    return ice_response


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

    # ── Aletheia capture: sceptic results ──
    try:
        aletheia.capture(
            tribunal_response=sceptic_response.dict(),
            consensus_report=report,
            raw_responses=[r.dict() for r in response_models],
            request_meta={
                "prompt": req.prompt, "k": req.k, "mode": "sceptic",
                "ontology": _active_ontology, "session_id": None,
            },
        )
    except Exception as e:
        print(f"[aletheia] sceptic capture error: {e}")

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


# NOTE: Aletheia READ endpoints live in aletheia_api.py (mounted by rhead.py at :8000/aletheia/).
# tribunal_api.py only handles CAPTURE (hooks above). No duplicate read endpoints here.

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
# Office Communicator — H₂O bonded (Sonnet gate on every message)
# ---------------------------------------------------------------------------

from office import Office
_office: Optional[Office] = None

def get_office() -> Office:
    global _office
    if _office is None:
        _office = Office(bridge=get_bridge())
    return _office


class ChatMessage(BaseModel):
    sender: str          # "human" | "rex" | "orion" | "gemini"
    text: str
    ts: str = ""
    id: str = ""


@app.post("/chat")
async def post_chat(msg: ChatMessage):
    """Post to shared chat via Office communicator."""
    record = get_office().post_chat(sender=msg.sender, text=msg.text)
    return record


@app.get("/chat")
async def get_chat(after: str = "", limit: int = 50):
    """Get recent chat messages."""
    messages = get_office().get_chat(after=after, limit=limit)
    return {"messages": messages}


class OfficeMsg(BaseModel):
    sender: str
    receiver: str
    text: str
    reply_to: Optional[str] = None


@app.post("/office/send")
async def office_send(msg: OfficeMsg):
    """Send agent→agent message. Sonnet-gated both directions (H₂O bond)."""
    result = get_office().send(
        sender=msg.sender,
        receiver=msg.receiver,
        text=msg.text,
        reply_to=msg.reply_to,
    )
    _broadcast_event({"id": result.id, "type": "office", "sender": result.sender,
                       "receiver": result.receiver, "text": result.compressed or msg.text,
                       "ts": result.ts})
    return {
        "id": result.id,
        "sender": result.sender,
        "receiver": result.receiver,
        "compressed": result.compressed,
        "response": result.response,
        "gate_tokens": result.gate_tokens,
        "relay_tokens": result.relay_tokens,
        "cost_usd": result.cost_usd,
        "ts": result.ts,
    }


@app.post("/office/broadcast")
async def office_broadcast(msg: ChatMessage):
    """Broadcast to all agents. Each message Sonnet-gated."""
    results = get_office().broadcast(sender=msg.sender, text=msg.text)
    for r in results:
        _broadcast_event({"id": r.id if hasattr(r, "id") else "", "type": "broadcast",
                          "sender": msg.sender, "receiver": r.receiver,
                          "text": msg.text[:200], "ts": r.ts if hasattr(r, "ts") else datetime.now(timezone.utc).isoformat()})
    return {"sent": len(results), "messages": [
        {"receiver": r.receiver, "response": r.response, "cost_usd": r.cost_usd}
        for r in results
    ]}


@app.get("/office/history")
async def office_history(agent: Optional[str] = None, limit: int = 30):
    """Full office communication log. iOS app uses this for log visibility."""
    return {"messages": get_office().history(agent=agent, limit=limit)}


# ---------------------------------------------------------------------------
# Log Visibility — same level as Rex sees
# ---------------------------------------------------------------------------

BRIDGE_LOG = _PROJECT_ROOT / "logs" / "bridge_calls.jsonl"
TRIBUNAL_LOG = _PROJECT_ROOT / "logs" / "tribunal_api_calls.jsonl"


@app.get("/logs/bridge")
async def get_bridge_logs(limit: int = 50, agent: Optional[str] = None):
    """Bridge call log — every LLM API call with cost, latency, status."""
    return _read_jsonl_tail(BRIDGE_LOG, limit, agent_filter=agent)


@app.get("/logs/tribunal")
async def get_tribunal_logs(limit: int = 30):
    """Tribunal invocation log — every consensus query."""
    return _read_jsonl_tail(TRIBUNAL_LOG, limit)


@app.get("/logs/burn")
async def get_burn_summary():
    """Token burn summary per agent — aggregated from bridge log."""
    if not BRIDGE_LOG.exists():
        return {"agents": {}, "total_cost": 0}
    agent_map = {
        "openai": "ORION", "gemini": "GEMINI", "deepseek": "GEMINI",
        "anthropic": "REX", "azure": "ORION",
        "openrouter": "SHARED", "huggingface": "SHARED",
    }
    agents: dict = {}
    with open(BRIDGE_LOG) as f:
        for line in f:
            try:
                rec = json.loads(line.strip())
                agent = rec.get("agent_name") or agent_map.get(rec.get("provider", ""), "SHARED")
                if agent not in agents:
                    agents[agent] = {"calls": 0, "tokens": 0, "cost_usd": 0.0, "errors": 0}
                agents[agent]["calls"] += 1
                agents[agent]["tokens"] += rec.get("total_tokens", 0)
                agents[agent]["cost_usd"] += rec.get("cost_usd", 0.0)
                if rec.get("status") not in ("ok", None):
                    agents[agent]["errors"] += 1
            except (json.JSONDecodeError, KeyError):
                continue
    total = sum(a["cost_usd"] for a in agents.values())
    return {"agents": agents, "total_cost": round(total, 4)}


@app.get("/logs/outbox")
async def get_outbox(agent: Optional[str] = None, limit: int = 20):
    """Agent outbox messages — markdown files from virtual office."""
    outbox_dir = _PROJECT_ROOT / "opera" / "ops" / "virtual-office" / "outbox"
    if not outbox_dir.exists():
        return {"messages": []}
    files = sorted(outbox_dir.glob("*.md"), key=lambda f: f.name, reverse=True)
    if agent:
        files = [f for f in files if f.name.upper().startswith(agent.upper())]
    results = []
    for f in files[:limit]:
        try:
            content = f.read_text()[:500]  # first 500 chars preview
            results.append({"file": f.name, "preview": content})
        except Exception:
            continue
    return {"messages": results}


# ---------------------------------------------------------------------------
# Token Governor
# ---------------------------------------------------------------------------

from token_governor import Governor, all_governors
from task_queue import TaskQueue

@app.get("/governor")
async def governor_all():
    """Dual-rail token governor — all agents."""
    return all_governors()

@app.get("/governor/{agent}")
async def governor_agent(agent: str):
    """Dual-rail token governor — single agent check + enforce."""
    gov = Governor(agent)
    return gov.enforce()

# ---------------------------------------------------------------------------
# Task Queue
# ---------------------------------------------------------------------------

@app.get("/tasks")
async def tasks_list(status: Optional[str] = None, agent: Optional[str] = None):
    """List tasks with optional filters."""
    q = TaskQueue()
    return {"tasks": q.list_tasks(status=status, agent=agent)}

@app.get("/tasks/summary")
async def tasks_summary():
    """Task queue health for dashboard."""
    q = TaskQueue()
    return q.summary()

@app.post("/tasks")
async def tasks_add(title: str, priority: str = "P1", agent: str = "any",
                    tags: str = ""):
    """Add a task to the queue."""
    q = TaskQueue()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    return q.add(title, priority=priority, agent=agent, tags=tag_list)

@app.post("/tasks/{task_id}/claim")
async def tasks_claim(task_id: str, agent: str = "rex"):
    """Claim a specific task or next available (task_id='next')."""
    q = TaskQueue()
    if task_id == "next":
        task = q.claim(agent)
    else:
        t = q.tasks.get(task_id)
        if t and t["status"] == "open":
            t["status"] = "claimed"
            t["claimed_by"] = agent
            from datetime import datetime, timezone
            t["updated"] = datetime.now(timezone.utc).isoformat()
            q._append_log("claim", {"id": task_id, "agent": agent})
            q._save_state()
            task = t
        else:
            task = None
    if not task:
        raise HTTPException(status_code=404, detail="No available task")
    return task

@app.post("/tasks/{task_id}/complete")
async def tasks_complete(task_id: str, result: str = ""):
    """Mark task as done."""
    q = TaskQueue()
    task = q.complete(task_id, result)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/tasks/{task_id}/block")
async def tasks_block(task_id: str, reason: str = ""):
    """Block a task."""
    q = TaskQueue()
    task = q.block(task_id, reason)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def _read_jsonl_tail(path: Path, limit: int, agent_filter: Optional[str] = None) -> dict:
    """Read last N records from a JSONL file."""
    if not path.exists():
        return {"records": [], "total": 0}
    records = []
    with open(path) as f:
        for line in f:
            try:
                rec = json.loads(line.strip())
                if agent_filter:
                    provider = rec.get("provider", "")
                    agent_name = rec.get("agent_name", "")
                    if agent_filter.lower() not in (provider, agent_name.lower()):
                        continue
                records.append(rec)
            except (json.JSONDecodeError, KeyError):
                continue
    tail = records[-limit:]
    return {"records": tail, "total": len(records)}


# ---------------------------------------------------------------------------
# Unified Feed — broadcast-first team chat for iOS
# ---------------------------------------------------------------------------

@app.get("/feed")
async def unified_feed(limit: int = 50, since: Optional[str] = None):
    """Unified chronological feed: office messages + outbox + inbox relays.
    Returns newest-first. iOS TeamChat view polls this."""
    items = []

    # 1. Office history (agent↔agent messages)
    try:
        for msg in get_office().history(limit=200):
            items.append({
                "id": msg.get("id", ""),
                "type": "office",
                "sender": msg.get("sender", "?"),
                "receiver": msg.get("receiver", "all"),
                "text": msg.get("compressed") or msg.get("text", ""),
                "ts": msg.get("ts", ""),
            })
    except Exception:
        pass

    # 2. Outbox files (agent dispatches)
    outbox_dir = _PROJECT_ROOT / "opera" / "ops" / "virtual-office" / "outbox"
    if outbox_dir.exists():
        for f in sorted(outbox_dir.glob("*.md"), key=lambda p: p.name, reverse=True)[:50]:
            parts = f.stem.split("_")
            sender = parts[0] if parts else "?"
            try:
                preview = f.read_text()[:300]
            except Exception:
                preview = ""
            items.append({
                "id": f.stem,
                "type": "outbox",
                "sender": sender.lower(),
                "receiver": "team",
                "text": preview,
                "ts": _ts_from_filename(f.name),
            })

    # 3. Inbox relays
    inbox_dir = _PROJECT_ROOT / "opera" / "ops" / "virtual-office" / "inbox"
    if inbox_dir.exists():
        for f in sorted(inbox_dir.glob("RELAY_*.md"), key=lambda p: p.name, reverse=True)[:30]:
            parts = f.stem.split("_")
            sender = "relay"
            receiver = "team"
            for i, p in enumerate(parts):
                if p == "to" and i + 1 < len(parts):
                    receiver = parts[i + 1].lower()
                if i > 2 and p not in ("to", "RELAY") and not p.isdigit():
                    sender = p.lower()
                    break
            try:
                preview = f.read_text()[:300]
            except Exception:
                preview = ""
            items.append({
                "id": f.stem,
                "type": "relay",
                "sender": sender,
                "receiver": receiver,
                "text": preview,
                "ts": _ts_from_filename(f.name),
            })

    # Sort by ts descending, dedup by id
    seen = set()
    unique = []
    for item in sorted(items, key=lambda x: x.get("ts", ""), reverse=True):
        if item["id"] not in seen:
            seen.add(item["id"])
            unique.append(item)

    # Apply since filter
    if since:
        unique = [i for i in unique if i.get("ts", "") > since]

    return {"items": unique[:limit], "total": len(unique)}


def _ts_from_filename(name: str) -> str:
    """Extract ISO timestamp from filename like ORION_20260227_145947_..."""
    import re
    m = re.search(r"(\d{8})_(\d{6})", name)
    if m:
        d, t = m.group(1), m.group(2)
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}T{t[:2]}:{t[2:4]}:{t[4:6]}+00:00"
    m2 = re.search(r"(\d{8})", name)
    if m2:
        d = m2.group(1)
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}T00:00:00+00:00"
    return ""


# ---------------------------------------------------------------------------
# SSE Live Stream — radio frequency
# ---------------------------------------------------------------------------

@app.get("/feed/stream")
async def feed_stream():
    """SSE stream. Every event on the bus is pushed to all listeners.
    iOS app connects once and keeps listening — like a radio frequency."""
    q: asyncio.Queue = asyncio.Queue(maxsize=200)
    _SUBSCRIBERS.append(q)

    async def event_generator():
        try:
            # Send initial heartbeat
            yield f"data: {json.dumps({'type': 'connected', 'ts': datetime.now(timezone.utc).isoformat()})}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Keepalive ping every 15s
                    yield f"data: {json.dumps({'type': 'ping', 'ts': datetime.now(timezone.utc).isoformat()})}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if q in _SUBSCRIBERS:
                _SUBSCRIBERS.remove(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


class FeedPushMsg(BaseModel):
    sender: str
    text: str
    type: str = "broadcast"
    receiver: str = "all"

@app.post("/feed/push")
async def feed_push(msg: FeedPushMsg):
    """Push a message onto the radio frequency. All listeners get it instantly."""
    event = {
        "id": secrets.token_hex(6),
        "type": msg.type,
        "sender": msg.sender,
        "receiver": msg.receiver,
        "text": msg.text,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    _broadcast_event(event)
    return event


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
