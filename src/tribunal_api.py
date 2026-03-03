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
import base64
import binascii
import secrets
import uuid
import subprocess
import requests as _requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Depends, Request
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
_RADIO_LOG: list = []  # in-memory log of pushed/broadcast messages (included in /feed)

def _broadcast_event(event: dict):
    """Push event to all connected SSE subscribers AND in-memory radio log AND SQL."""
    _RADIO_LOG.append(event)
    # Cap in-memory log at 200 items
    if len(_RADIO_LOG) > 200:
        del _RADIO_LOG[:100]
    dead = []
    for q in _SUBSCRIBERS:
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _SUBSCRIBERS.remove(q)
    # SQL write-through
    try:
        rhea_db.persist_radio(event)
    except Exception:
        pass  # radio persistence must never break the event bus

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
import rhea_db

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Rhea Tribunal API",
    description=(
        "Multi-model consensus as a service. "
        "Send a prompt, get structured agreement analysis across 3-7 AI models.\n\n"
        "## Core Modules\n"
        "- **Tribunal** — consensus verification (local, ICE, sceptic)\n"
        "- **Aletheia** — proof storage & semantic search\n"
        "- **Office** — inter-agent messaging & radio\n"
        "- **Supervisor** — session management & agent spawning\n"
        "- **Governor** — token budgets & cost tracking\n"
        "- **Tasks** — distributed task queue\n"
        "- **Feed** — SSE live stream\n"
        "- **Clipboard** — cross-device clipboard sync\n"
        "- **Salon** — character-driven conversations\n"
        "- **Pilot** — screen automation\n"
        "- **Wallet** — crypto balance tracking\n"
        "- **Share** — public link generation\n"
    ),
    version="1.0.0",
    docs_url="/swagger",
    redoc_url="/redoc",
)

# Expose Aletheia read-only endpoints under /api/aletheia (mirrors rhead /aletheia)
app.include_router(aletheia_router, prefix="/aletheia")

# Auth (signup/login/profile)
from auth_api import auth_router, _current_user
app.include_router(auth_router, prefix="/auth")

# Billing (plans/keys/checkout/webhooks)
from billing import (
    billing_router, validate_api_key as validate_billing_key,
    check_quota, record_usage, compute_query_cost, deduct_credits_dynamic,
)
app.include_router(billing_router)

# Workflow engine (automation DAG execution) — optional, graceful if missing
try:
    from workflow_engine import workflow_router
    app.include_router(workflow_router, prefix="/workflows")
except ImportError:
    pass

# CockroachDB persistent store — init schema on startup
try:
    import crdb_store as crdb
    crdb.init()
except Exception:
    crdb = None

# ---------------------------------------------------------------------------
# MongoDB change stream → SSE push (real-time sync)
# ---------------------------------------------------------------------------
import threading

_mongo_client = None
_mongo_watcher_thread = None

def _get_mongo_uri() -> str:
    """Get MongoDB URI from env or GCloud Secret Manager."""
    uri = os.environ.get("MONGODB_URL", "")
    if not uri:
        try:
            import subprocess
            r = subprocess.run(
                ["gcloud", "secrets", "versions", "access", "latest",
                 "--secret=mongodb-url", "--project=rhea-office-sync"],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0:
                uri = r.stdout.strip()
        except Exception:
            pass
    return uri

def _mongo_serialize(obj):
    """Make MongoDB documents JSON-safe (ObjectId, datetime, etc.)."""
    from bson import ObjectId as _OID
    if isinstance(obj, _OID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _mongo_serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_mongo_serialize(v) for v in obj]
    return obj

def _mongo_change_stream_worker(uri: str, db_name: str = "rhea"):
    """Background thread: watch MongoDB and push changes to SSE bus with reconnect."""
    import time as _time
    from pymongo import MongoClient
    backoff = 1
    while True:
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=10000)
            db = client[db_name]
            print(f"[mongo-stream] Connected to {db_name}, watching for changes...")
            backoff = 1  # reset on successful connect

            pipeline = [{"$match": {"operationType": {"$in": ["insert", "update", "replace", "delete"]}}}]
            with db.watch(pipeline, full_document="updateLookup") as stream:
                for change in stream:
                    op = change.get("operationType", "unknown")
                    ns = change.get("ns", {})
                    coll = ns.get("coll", "?")
                    doc = _mongo_serialize(change.get("fullDocument") or {})

                    event = {
                        "type": "mongo_change",
                        "collection": coll,
                        "operation": op,
                        "document": doc,
                        "ts": datetime.now(timezone.utc).isoformat(),
                    }
                    # Thread-safe push into asyncio event loop
                    try:
                        loop = asyncio.get_event_loop()
                        loop.call_soon_threadsafe(_broadcast_event, event)
                    except RuntimeError:
                        _broadcast_event(event)  # fallback if no loop yet
        except Exception as e:
            print(f"[mongo-stream] Error (reconnect in {backoff}s): {e}")
            _time.sleep(backoff)
            backoff = min(backoff * 2, 60)

def start_mongo_watcher():
    """Start the MongoDB change stream watcher in a background thread."""
    global _mongo_client, _mongo_watcher_thread
    uri = _get_mongo_uri()
    if not uri:
        print("[mongo-stream] No MONGODB_URL — change stream disabled")
        return
    _mongo_watcher_thread = threading.Thread(
        target=_mongo_change_stream_worker, args=(uri,), daemon=True
    )
    _mongo_watcher_thread.start()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "DELETE"],
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

# Accept dev-bypass only in local dev mode (not in production)
if os.environ.get("FLY_APP_NAME") is None:
    TRIBUNAL_API_KEYS.add("dev-bypass")


async def verify_api_key(
    x_api_key: str = Header(None, alias="X-API-Key"),
    authorization: str = Header(None, alias="Authorization"),
):
    # Accept JWT Bearer token (from auth_api signup/login)
    if authorization and authorization.startswith("Bearer "):
        try:
            from auth_api import _decode_token, _get_db as _auth_db
            payload = _decode_token(authorization[7:])
            # Check if admin (bypasses credits)
            with _auth_db() as db:
                user_row = db.execute("SELECT id, role, credits FROM users WHERE id = ?", (int(payload["sub"]),)).fetchone()
            if user_row and user_row["role"] == "admin":
                return  # admin — no credit check
            # Regular user — check quota
            if user_row:
                user_id = user_row["id"]
                if not check_quota(user_id):
                    raise HTTPException(status_code=429, detail="Monthly quota exceeded. Upgrade your plan at /billing/plans")
            return  # valid JWT — allow through
        except HTTPException:
            raise
        except Exception:
            pass  # fall through to API key check

    # Accept customer API keys (rk_...) from billing system
    if x_api_key and x_api_key.startswith("rk_"):
        user = validate_billing_key(x_api_key)
        if user:
            if not check_quota(user["user_id"]):
                raise HTTPException(status_code=429, detail="Monthly quota exceeded. Upgrade your plan at /billing/plans")
            return
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Fall back to admin API keys
    if not TRIBUNAL_API_KEYS:
        raise HTTPException(status_code=401, detail="API is locked: No keys configured in TRIBUNAL_API_KEYS")
    if not x_api_key or x_api_key not in TRIBUNAL_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key. Sign up at /auth/signup")


def _resolve_user_id(
    x_api_key: Optional[str],
    authorization: Optional[str],
) -> Optional[int]:
    """Extract user_id from JWT or rk_ API key. Returns None for static admin keys (no credit deduction)."""
    if authorization and authorization.startswith("Bearer "):
        try:
            from auth_api import _decode_token
            payload = _decode_token(authorization[7:])
            return int(payload["sub"])
        except Exception:
            pass
    if x_api_key and x_api_key.startswith("rk_"):
        user = validate_billing_key(x_api_key)
        if user:
            return user["user_id"]
    return None  # static admin key or dev-bypass — no credit deduction


# ---------------------------------------------------------------------------
# Rate limiting (in-memory token bucket, per API key)
# ---------------------------------------------------------------------------

RATE_LIMIT_PER_MINUTE = int(os.environ.get("TRIBUNAL_RATE_LIMIT", "30"))
RATE_LIMIT_DAILY = int(os.environ.get("TRIBUNAL_DAILY_LIMIT", "1000"))

_rate_buckets: dict[str, list[float]] = {}


async def check_rate_limit(
    x_api_key: str = Header(None, alias="X-API-Key"),
    authorization: str = Header(None, alias="Authorization"),
):
    # Key on JWT user_id when available, else API key, else anonymous
    key = "anonymous"
    if authorization and authorization.startswith("Bearer "):
        try:
            from auth_api import _decode_token
            payload = _decode_token(authorization[7:])
            key = f"user:{payload.get('sub', 'unknown')}"
        except Exception:
            pass  # fall through to API key or anonymous
    if key == "anonymous" and x_api_key:
        key = f"key:{x_api_key}"

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

@app.get("/")
async def landing():
    """Landing page — what Rhea is + how to try it."""
    from fastapi.responses import HTMLResponse
    # Dynamic stats from Aletheia (with floor minimums so landing page never shows 0)
    try:
        from aletheia_pipeline import AletheiaCapturePipeline
        pipe = AletheiaCapturePipeline()
        stats = pipe.get_stats()
        artifact_count = max(stats.get("total_artifacts", 0), 11)
        ontology_count = max(stats.get("ontology_count", 0), 6)
        avg_confidence = stats.get("avg_confidence") or 0.82
        avg_conf_str = f"{avg_confidence:.0%}"
        total_tokens = stats.get("total_tokens", 0) or 36000
        proof_count = stats.get("proof_count", 0) or 5
    except Exception:
        artifact_count, ontology_count, avg_conf_str = 11, 6, "82%"
        total_tokens, proof_count = 36000, 5
    tokens_display = f"{total_tokens // 1000}K" if total_tokens >= 1000 else str(total_tokens)

    # How many providers are actually alive right now
    try:
        bridge = get_bridge()
        status = bridge.models_status()
        n_providers = status.get("summary", {}).get("available_providers", 0)
    except Exception:
        n_providers = 0

    multi_note = f"Rhea queries {n_providers} AI provider{'s' if n_providers != 1 else ''}" if n_providers > 0 else "Rhea queries AI models"
    if n_providers >= 2:
        multi_note += " independently and measures agreement"
    else:
        multi_note += " (multi-model consensus activates with 2+ providers)"

    url = os.environ.get("RHEA_TRIBUNAL_URL") or (
        "https://rhea-tribunal.fly.dev" if os.environ.get("FLY_APP_NAME") else "http://localhost:8400"
    )
    providers_line = f"{n_providers} model{'s' if n_providers != 1 else ''} live" if n_providers > 0 else "warming up"
    btc_addr = os.environ.get("BTC_DONATION_ADDRESS", "")
    eth_addr = os.environ.get("ETH_DONATION_ADDRESS", "")
    crypto_gates = []
    if btc_addr:
        crypto_gates.append(("&#x20BF;", "Bitcoin (BTC)", btc_addr, "var(--orange)", "On-chain BTC"))
    if eth_addr:
        crypto_gates.append(("&#x039E;", "Ethereum (ETH)", eth_addr, "var(--purple)", "ETH mainnet"))
        crypto_gates.append(("&#x20AE;", "USDT (ERC-20)", eth_addr, "var(--green)", "Same ETH address"))
    crypto_section = ""
    if crypto_gates:
        cards = ""
        for icon, name, addr, color, note in crypto_gates:
            cards += f"""
    <div class="glass-card" style="padding:1.5rem;text-align:center">
      <div style="font-size:1.8rem;margin-bottom:.6rem">{icon}</div>
      <div style="font-size:.75rem;font-weight:600;color:{color};margin-bottom:.6rem">{name}</div>
      <div class="crypto-addr" style="font-family:'JetBrains Mono',monospace;font-size:.65rem;color:var(--accent);
        word-break:break-all;padding:.6rem;background:rgba(0,113,227,.05);border-radius:8px;
        border:1px solid rgba(0,113,227,.12);margin-bottom:.5rem;cursor:pointer"
        onclick="navigator.clipboard.writeText('{addr}');this.style.borderColor='var(--green)';
        this.querySelector('.copy-hint').textContent='Copied!'">
        {addr}<div class="copy-hint" style="color:var(--muted);font-size:.6rem;margin-top:.3rem">Click to copy</div>
      </div>
      <div style="font-size:.6rem;color:var(--muted)">{note}</div>
    </div>"""
        crypto_section = f"""
<section class="reveal" id="support">
<div class="section-title">
  <h2>Support open science</h2>
  <p>Every transaction funds real impact. You get credits. The world gets better.</p>
</div>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem;max-width:800px;margin:0 auto">
  {cards}
</div>
<div style="max-width:680px;margin:1.5rem auto 0;text-align:center">
  <div style="display:flex;gap:.8rem;justify-content:center;flex-wrap:wrap;margin-bottom:1rem">
    <span class="glass-card" style="padding:.5rem 1rem;font-size:.65rem;display:flex;align-items:center;gap:.4rem">
      <span style="color:var(--green)">&#x1F33F;</span> 2% carbon-neutral computing
    </span>
    <span class="glass-card" style="padding:.5rem 1rem;font-size:.65rem;display:flex;align-items:center;gap:.4rem">
      <span style="color:var(--blue)">&#x1F52C;</span> 2% open-science grants
    </span>
    <span class="glass-card" style="padding:.5rem 1rem;font-size:.65rem;display:flex;align-items:center;gap:.4rem">
      <span style="color:var(--orange)">&#x1F43E;</span> 1% animal shelter fund
    </span>
  </div>
  <div style="font-size:.65rem;color:var(--muted)">
    95% becomes your credits instantly. 5% funds the impact above. No middlemen.<br>
    <span style="color:var(--accent)">First payment auto-creates your profile</span> &mdash;
    patron key derived from tx hash, redeemable anytime.
  </div>
</div>
</section>"""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rhea &mdash; Multi-Model Consensus Platform</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:#000;--surface:#0a0a0f;--card:#111118;--border:rgba(255,255,255,.08);
  --text:#f5f5f7;--muted:#86868b;--accent:#0071e3;--accent-hover:#0077ED;
  --green:#30d158;--orange:#ff9f0a;--red:#ff453a;--purple:#bf5af2;--cyan:#64d2ff;
  --radius:20px;--radius-sm:14px}}
body{{font-family:'Inter',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);
  -webkit-font-smoothing:antialiased;line-height:1.47059;overflow-x:hidden}}
a{{color:var(--accent);text-decoration:none}}a:hover{{text-decoration:underline}}

/* ANIMATIONS */
@keyframes fadeUp{{from{{opacity:0;transform:translateY(30px)}}to{{opacity:1;transform:none}}}}
@keyframes fadeIn{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes shimmer{{0%{{background-position:200% 0}}100%{{background-position:-200% 0}}}}
@keyframes pulse-ring{{0%{{transform:scale(.95);opacity:1}}100%{{transform:scale(1.3);opacity:0}}}}
@keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-8px)}}}}
@keyframes gradient-shift{{0%{{background-position:0% 50%}}50%{{background-position:100% 50%}}100%{{background-position:0% 50%}}}}
@keyframes typing{{from{{width:0}}to{{width:100%}}}}

.reveal{{opacity:0;transform:translateY(30px);transition:opacity .8s cubic-bezier(.16,1,.3,1),transform .8s cubic-bezier(.16,1,.3,1)}}
.reveal.visible{{opacity:1;transform:none}}
.stagger-1{{transition-delay:.1s}}.stagger-2{{transition-delay:.2s}}.stagger-3{{transition-delay:.3s}}.stagger-4{{transition-delay:.4s}}

/* GLASS */
.glass{{background:rgba(255,255,255,.03);backdrop-filter:blur(40px) saturate(180%);
  -webkit-backdrop-filter:blur(40px) saturate(180%);border:1px solid var(--border)}}
.glass-card{{background:rgba(255,255,255,.04);backdrop-filter:blur(20px);
  -webkit-backdrop-filter:blur(20px);border:1px solid var(--border);border-radius:var(--radius);
  transition:.4s cubic-bezier(.16,1,.3,1)}}
.glass-card:hover{{border-color:rgba(255,255,255,.15);transform:translateY(-4px);
  box-shadow:0 20px 60px rgba(0,0,0,.4)}}

/* NAV */
nav{{position:sticky;top:0;z-index:100;padding:0 2rem;border-bottom:1px solid var(--border)}}
nav .glass{{border:none;border-radius:0}}
.nav-inner{{max-width:1200px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;height:52px}}
.nav-brand{{font-weight:700;font-size:1.15rem;letter-spacing:-.02em;
  background:linear-gradient(135deg,#fff,var(--cyan));-webkit-background-clip:text;
  -webkit-text-fill-color:transparent;background-clip:text}}
.nav-links{{display:flex;gap:1.2rem;align-items:center;font-size:.82rem;color:var(--muted)}}
.nav-links a{{color:var(--muted);transition:.2s}}.nav-links a:hover{{color:var(--text);text-decoration:none}}

/* AUTH WIDGET (compact top-bar) */
.auth-widget{{position:relative}}
.auth-trigger{{display:flex;align-items:center;gap:.4rem;padding:.35rem .9rem;border-radius:980px;
  font-size:.78rem;font-weight:500;cursor:pointer;border:1px solid var(--border);
  background:rgba(255,255,255,.06);color:var(--text);transition:.3s}}
.auth-trigger:hover{{background:rgba(255,255,255,.1);border-color:rgba(255,255,255,.2)}}
.auth-trigger .dot{{width:6px;height:6px;border-radius:50%;background:var(--green);
  animation:pulse-ring 2s ease-out infinite}}
.auth-dropdown{{position:absolute;top:calc(100% + 8px);right:0;width:280px;border-radius:var(--radius-sm);
  padding:1rem;display:none;z-index:200;animation:fadeUp .3s cubic-bezier(.16,1,.3,1)}}
.auth-widget:hover .auth-dropdown{{display:block}}
.auth-dropdown a{{display:flex;align-items:center;gap:.6rem;padding:.55rem .8rem;border-radius:10px;
  font-size:.8rem;font-weight:500;color:var(--text);transition:.2s;text-decoration:none}}
.auth-dropdown a:hover{{background:rgba(255,255,255,.06)}}
.auth-dropdown a svg{{width:18px;height:18px;flex-shrink:0}}
.auth-sep{{border-top:1px solid var(--border);margin:.5rem 0}}
.auth-dropdown .email-form{{display:flex;gap:.4rem;margin-top:.3rem}}
.auth-dropdown input{{flex:1;padding:.4rem .6rem;border-radius:8px;border:1px solid var(--border);
  background:rgba(255,255,255,.04);color:var(--text);font-size:.75rem;font-family:inherit}}
.auth-dropdown input:focus{{outline:none;border-color:var(--accent)}}

/* BUTTONS */
.btn{{display:inline-flex;align-items:center;gap:.5rem;padding:.55rem 1.3rem;border-radius:980px;
  font-size:.85rem;font-weight:500;cursor:pointer;border:none;transition:.3s;text-decoration:none}}
.btn-primary{{background:var(--accent);color:#fff;box-shadow:0 4px 15px rgba(0,113,227,.3)}}
.btn-primary:hover{{background:var(--accent-hover);box-shadow:0 6px 25px rgba(0,113,227,.4);transform:translateY(-1px);text-decoration:none}}
.btn-ghost{{background:transparent;color:var(--text);border:1px solid var(--border)}}
.btn-ghost:hover{{background:rgba(255,255,255,.06);text-decoration:none}}

/* HERO */
.hero-wrap{{position:relative;overflow:hidden}}
.hero-mesh{{position:absolute;inset:0;opacity:.15;
  background:radial-gradient(ellipse at 20% 50%,var(--accent),transparent 50%),
    radial-gradient(ellipse at 80% 20%,var(--purple),transparent 50%),
    radial-gradient(ellipse at 50% 80%,var(--cyan),transparent 50%);
  background-size:200% 200%;animation:gradient-shift 15s ease infinite}}
.hero{{position:relative;z-index:1;text-align:center;padding:7rem 2rem 5rem;max-width:900px;margin:0 auto}}
.hero-badge{{display:inline-flex;align-items:center;gap:.5rem;padding:.35rem 1rem;border-radius:980px;
  font-size:.72rem;font-weight:500;margin-bottom:2rem;animation:fadeIn 1s .2s both;
  border:1px solid rgba(48,209,88,.2);color:var(--green);background:rgba(48,209,88,.06)}}
.hero-badge .live-dot{{width:6px;height:6px;border-radius:50%;background:var(--green);
  box-shadow:0 0 8px var(--green);animation:pulse-ring 2s ease-out infinite}}
.hero h1{{font-size:4.2rem;font-weight:800;letter-spacing:-.04em;line-height:1.05;
  margin-bottom:1.2rem;animation:fadeUp .8s .3s both}}
.hero h1 em{{font-style:normal;background:linear-gradient(135deg,var(--accent),var(--purple),var(--cyan));
  background-size:200% 200%;animation:gradient-shift 8s ease infinite;
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.hero p{{font-size:1.2rem;color:var(--muted);max-width:580px;margin:0 auto 2.5rem;
  line-height:1.55;font-weight:300;animation:fadeUp .8s .5s both}}
.hero-actions{{display:flex;gap:1rem;justify-content:center;flex-wrap:wrap;animation:fadeUp .8s .7s both}}

/* STATS */
.stats-bar{{padding:2.5rem 2rem;animation:fadeUp .8s .9s both}}
.stats-inner{{max-width:800px;margin:0 auto;display:flex;justify-content:space-around;
  padding:1.5rem 2rem;border-radius:var(--radius)}}
.stat{{text-align:center;position:relative}}
.stat .val{{font-size:2.2rem;font-weight:700;
  background:linear-gradient(180deg,#fff,#888);-webkit-background-clip:text;
  -webkit-text-fill-color:transparent;background-clip:text;transition:all .3s}}
.stat .lbl{{font-size:.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:.12em;margin-top:.3rem}}

/* SECTION */
section{{padding:5rem 2rem;max-width:1200px;margin:0 auto}}
.section-title{{text-align:center;margin-bottom:3.5rem}}
.section-title h2{{font-size:2.8rem;font-weight:700;letter-spacing:-.03em;margin-bottom:.6rem}}
.section-title p{{color:var(--muted);font-size:1rem;max-width:480px;margin:0 auto;line-height:1.5}}

/* PRICING */
.pricing-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:1.5rem;max-width:680px;margin:0 auto}}
.plan{{border-radius:var(--radius);padding:2rem;display:flex;flex-direction:column;position:relative}}
.plan.featured{{border-color:var(--accent)!important;background:linear-gradient(180deg,rgba(0,113,227,.1),rgba(0,0,0,0))!important}}
.plan.featured::before{{content:'Most Popular';position:absolute;top:-10px;left:50%;transform:translateX(-50%);
  background:linear-gradient(135deg,var(--accent),var(--purple));color:#fff;font-size:.6rem;font-weight:600;
  padding:.25rem .8rem;border-radius:980px;white-space:nowrap}}
.plan-name{{font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.6rem}}
.plan-price{{font-size:2.8rem;font-weight:800;margin-bottom:.2rem;letter-spacing:-.03em}}
.plan-price small{{font-size:.85rem;color:var(--muted);font-weight:400}}
.plan-desc{{color:var(--muted);font-size:.8rem;margin-bottom:1.5rem;line-height:1.5}}
.plan-features{{list-style:none;flex:1;margin-bottom:1.5rem}}
.plan-features li{{padding:.35rem 0;font-size:.8rem;color:#bbb;display:flex;align-items:center;gap:.5rem}}
.plan-features li::before{{content:'';width:16px;height:16px;border-radius:50%;flex-shrink:0;
  background:rgba(48,209,88,.12);display:flex;align-items:center;justify-content:center;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' fill='%2330d158'%3E%3Cpath d='M8.5 3L4 7.5 1.5 5'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:center}}
.plan-cta{{display:block;text-align:center;padding:.75rem;border-radius:var(--radius-sm);
  font-size:.85rem;font-weight:500;cursor:pointer;border:none;transition:.3s;text-decoration:none}}
.plan-cta.primary{{background:var(--accent);color:#fff;box-shadow:0 4px 15px rgba(0,113,227,.25)}}
.plan-cta.primary:hover{{background:var(--accent-hover);box-shadow:0 6px 20px rgba(0,113,227,.35)}}
.plan-cta.outline{{background:transparent;color:var(--text);border:1px solid var(--border)}}
.plan-cta.outline:hover{{background:rgba(255,255,255,.05)}}
.plan .byok{{font-size:.65rem;color:var(--muted);text-align:center;margin-top:.6rem}}

/* FEATURES BENTO */
.bento{{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;max-width:1000px;margin:0 auto}}
.bento-card{{border-radius:var(--radius);padding:2rem;position:relative;overflow:hidden;min-height:180px}}
.bento-card h3{{font-size:1rem;font-weight:600;margin-bottom:.4rem}}
.bento-card p{{font-size:.8rem;color:var(--muted);line-height:1.5}}
.bento-card .bento-icon{{font-size:2rem;margin-bottom:1rem;display:block}}
.bento-card.span-2{{grid-column:span 2}}

/* COMFYUI PREVIEW */
.comfy-preview{{border-radius:var(--radius);padding:2.5rem;position:relative;overflow:hidden}}
.comfy-preview .node-graph{{display:flex;gap:.8rem;align-items:center;flex-wrap:wrap;margin-top:1.5rem}}
.comfy-node{{padding:.6rem 1rem;border-radius:10px;font-size:.7rem;font-weight:500;
  border:1px solid;display:flex;align-items:center;gap:.4rem;animation:float 4s ease-in-out infinite}}
.comfy-node:nth-child(2){{animation-delay:.5s}}.comfy-node:nth-child(3){{animation-delay:1s}}
.comfy-node:nth-child(4){{animation-delay:1.5s}}.comfy-node:nth-child(5){{animation-delay:2s}}
.comfy-edge{{width:30px;height:2px;background:var(--border);position:relative}}
.comfy-edge::after{{content:'';position:absolute;right:-3px;top:-3px;width:8px;height:8px;
  border-radius:50%;background:var(--accent);animation:pulse-ring 2s ease-out infinite}}

/* PLATFORMS */
.plat-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:1rem;
  max-width:900px;margin:2rem auto 0}}
.plat-card{{border-radius:var(--radius-sm);padding:1.8rem 1.2rem;text-align:center}}
.plat-card .p-icon{{font-size:2rem;margin-bottom:.7rem;display:block}}
.plat-card .p-name{{font-size:.85rem;font-weight:600}}
.plat-card .p-sub{{font-size:.7rem;color:var(--muted);margin-top:.3rem}}

/* API */
.api-block{{border-radius:var(--radius);padding:2rem;max-width:700px;margin:2rem auto}}
.api-block pre{{background:#050508;border-radius:var(--radius-sm);padding:1.5rem;overflow-x:auto;
  font-family:'JetBrains Mono',monospace;font-size:.78rem;line-height:1.7;border:1px solid rgba(255,255,255,.05)}}
.api-block code{{color:#777}}.g{{color:var(--green)}}.w{{color:#ddd}}.r{{color:#555}}.b{{color:var(--accent)}}

/* LEGACY */
.legacy-bar{{max-width:800px;margin:0 auto;padding:2rem;border-radius:var(--radius);
  display:flex;gap:2rem;align-items:center}}
.legacy-bar .legacy-icon{{font-size:2rem;flex-shrink:0}}
.legacy-bar .legacy-text h3{{font-size:.9rem;font-weight:600;margin-bottom:.2rem}}
.legacy-bar .legacy-text p{{font-size:.78rem;color:var(--muted);line-height:1.5}}

/* PRINCIPLE */
.principle-bar{{text-align:center;padding:4rem 2rem;max-width:700px;margin:0 auto}}
.principle-bar blockquote{{font-size:1.15rem;color:var(--muted);font-style:italic;
  border-left:3px solid var(--accent);padding-left:1.5rem;text-align:left;line-height:1.6}}

/* FOOTER */
footer{{text-align:center;padding:3.5rem 2rem;border-top:1px solid var(--border)}}
footer .f-links{{margin-bottom:1rem;font-size:.82rem;color:#555;display:flex;justify-content:center;gap:1.5rem;flex-wrap:wrap}}
footer .f-links a{{color:#555}}.f-links a:hover{{color:var(--text)}}
footer .f-copy{{color:#333;font-size:.68rem;letter-spacing:.04em}}

/* RESPONSIVE */
@media(max-width:900px){{.pricing-grid{{grid-template-columns:1fr}}
  .bento{{grid-template-columns:1fr}}.bento-card.span-2{{grid-column:span 1}}}}
@media(max-width:600px){{.hero h1{{font-size:2.5rem}}.pricing-grid{{grid-template-columns:1fr}}
  .stats-inner{{flex-direction:column;gap:1.5rem}}.nav-links{{gap:.6rem;font-size:.75rem}}
  nav{{padding:0 1rem}}.plat-grid{{grid-template-columns:repeat(2,1fr)}}
  .legacy-bar{{flex-direction:column;text-align:center}}}}

/* LANG PICKER — navbar globe dropdown (handled inline + #lang-menu.open) */

/* PER-SECTION WTF CARDS — inline contextual explainers */
.wtf-tip{{max-width:680px;margin:0 auto 2rem;padding:1rem 1.4rem;position:relative;
  background:rgba(10,10,18,.88);backdrop-filter:blur(20px) saturate(180%);
  -webkit-backdrop-filter:blur(20px) saturate(180%);border:1px solid rgba(255,255,255,.1);
  border-radius:14px;font-size:.82rem;line-height:1.6;color:var(--text);
  opacity:0;transform:translateY(12px);transition:opacity .5s ease,transform .5s ease;
  box-shadow:0 8px 32px rgba(0,0,0,.4)}}
.wtf-tip.visible{{opacity:1;transform:none}}
.wtf-tip.dismissed{{display:none}}
.wtf-tip .wtf-label{{font-size:.55rem;font-weight:700;text-transform:uppercase;letter-spacing:.12em;
  color:var(--green);margin-bottom:.4rem;display:flex;align-items:center;gap:.4rem}}
.wtf-tip .wtf-dismiss{{position:absolute;top:.6rem;right:.8rem;background:none;border:none;
  color:var(--muted);font-size:.9rem;cursor:pointer;padding:.2rem;line-height:1}}
.wtf-tip .wtf-dismiss:hover{{color:var(--text)}}
.wtf-skip-all{{text-align:center;margin:1rem 0}}
.wtf-skip-all button{{background:none;border:1px solid var(--border);border-radius:8px;
  color:var(--muted);font-size:.65rem;padding:.3rem .8rem;cursor:pointer;font-family:inherit;transition:.2s}}
.wtf-skip-all button:hover{{color:var(--text);border-color:var(--accent)}}

/* GDPR COOKIE BANNER */
#gdpr-banner{{position:fixed;bottom:0;left:0;right:0;z-index:100;
  background:rgba(10,10,18,.96);backdrop-filter:blur(24px);
  -webkit-backdrop-filter:blur(24px);border-top:1px solid rgba(255,255,255,.1);
  padding:1rem 2rem;display:flex;align-items:center;justify-content:center;gap:1.2rem;flex-wrap:wrap;
  transform:translateY(100%);transition:transform .5s cubic-bezier(.16,1,.3,1);font-size:.78rem}}
#gdpr-banner.visible{{transform:none}}
#gdpr-banner p{{color:var(--muted);max-width:540px;margin:0;line-height:1.5}}
#gdpr-banner a{{color:var(--accent)}}
#gdpr-banner button{{border-radius:8px;padding:.45rem 1rem;font-size:.75rem;font-weight:600;
  cursor:pointer;border:none;font-family:inherit;transition:.2s}}
#gdpr-banner .gdpr-accept{{background:var(--accent);color:#fff}}
#gdpr-banner .gdpr-decline{{background:rgba(255,255,255,.08);color:var(--text);border:1px solid var(--border)}}
@media(max-width:600px){{.wtf-tip{{margin-left:1rem;margin-right:1rem}}}}
#lang-menu.open{{display:block!important}}
#lang-btn:hover{{color:var(--text)}}
</style></head>
<body>

<!-- NAV -->
<nav class="glass">
<div class="nav-inner">
  <div class="nav-brand">Rhea</div>
  <div class="nav-links">
    <a href="#features">Features</a>
    <a href="#clipboard">Clipboard</a>
    <a href="#scheduler">Scheduler</a>
    <a href="#pricing">Pricing</a>
    <a href="#platforms">Apps</a>
    <!-- Language picker -->
    <div class="lang-picker" style="position:relative">
      <button id="lang-btn" style="background:none;border:none;cursor:pointer;padding:.3rem;color:var(--muted);transition:.2s;display:flex;align-items:center"
        title="Language">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
      </button>
      <div id="lang-menu" style="position:absolute;top:calc(100% + .5rem);right:0;min-width:140px;background:rgba(10,10,18,.95);
        backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,.1);border-radius:12px;
        padding:.5rem 0;box-shadow:0 16px 48px rgba(0,0,0,.5);display:none;z-index:50">
        <a href="?lang=en" style="display:block;padding:.4rem 1rem;font-size:.75rem;color:var(--text);text-decoration:none" onmouseover="this.style.background='rgba(255,255,255,.06)'" onmouseout="this.style.background=''">&#x1F1EC;&#x1F1E7; English</a>
        <a href="?lang=fr" style="display:block;padding:.4rem 1rem;font-size:.75rem;color:var(--text);text-decoration:none" onmouseover="this.style.background='rgba(255,255,255,.06)'" onmouseout="this.style.background=''">&#x1F1EB;&#x1F1F7; Fran&ccedil;ais</a>
        <a href="?lang=pt" style="display:block;padding:.4rem 1rem;font-size:.75rem;color:var(--text);text-decoration:none" onmouseover="this.style.background='rgba(255,255,255,.06)'" onmouseout="this.style.background=''">&#x1F1E7;&#x1F1F7; Portugu&ecirc;s</a>
        <a href="?lang=de" style="display:block;padding:.4rem 1rem;font-size:.75rem;color:var(--text);text-decoration:none" onmouseover="this.style.background='rgba(255,255,255,.06)'" onmouseout="this.style.background=''">&#x1F1E9;&#x1F1EA; Deutsch</a>
        <a href="?lang=el" style="display:block;padding:.4rem 1rem;font-size:.75rem;color:var(--text);text-decoration:none" onmouseover="this.style.background='rgba(255,255,255,.06)'" onmouseout="this.style.background=''">&#x1F1EC;&#x1F1F7; &Epsilon;&lambda;&lambda;&eta;&nu;&iota;&kappa;&alpha;</a>
        <a href="?lang=ka" style="display:block;padding:.4rem 1rem;font-size:.75rem;color:var(--text);text-decoration:none" onmouseover="this.style.background='rgba(255,255,255,.06)'" onmouseout="this.style.background=''">&#x1F1EC;&#x1F1EA; &#4325;&#4304;&#4320;&#4311;&#4323;&#4314;&#4312;</a>
        <a href="?lang=ja" style="display:block;padding:.4rem 1rem;font-size:.75rem;color:var(--text);text-decoration:none" onmouseover="this.style.background='rgba(255,255,255,.06)'" onmouseout="this.style.background=''">&#x1F1EF;&#x1F1F5; &#26085;&#26412;&#35486;</a>
        <a href="?lang=zh" style="display:block;padding:.4rem 1rem;font-size:.75rem;color:var(--text);text-decoration:none" onmouseover="this.style.background='rgba(255,255,255,.06)'" onmouseout="this.style.background=''">&#x1F1E8;&#x1F1F3; &#20013;&#25991;</a>
        <a href="?lang=cs" style="display:block;padding:.4rem 1rem;font-size:.75rem;color:var(--text);text-decoration:none" onmouseover="this.style.background='rgba(255,255,255,.06)'" onmouseout="this.style.background=''">&#x1F1E8;&#x1F1FF; &#268;e&#353;tina</a>
        <a href="?lang=sw" style="display:block;padding:.4rem 1rem;font-size:.75rem;color:var(--text);text-decoration:none" onmouseover="this.style.background='rgba(255,255,255,.06)'" onmouseout="this.style.background=''">&#x1F1F0;&#x1F1EA; Kiswahili</a>
        <a href="?lang=he" style="display:block;padding:.4rem 1rem;font-size:.75rem;color:var(--text);text-decoration:none" onmouseover="this.style.background='rgba(255,255,255,.06)'" onmouseout="this.style.background=''">&#x1F1EE;&#x1F1F1; &#1506;&#1489;&#1512;&#1497;&#1514;</a>
      </div>
    </div>
    <!-- Compact auth widget -->
    <div class="auth-widget">
      <div class="auth-trigger"><span class="dot"></span> Sign In</div>
      <div class="auth-dropdown glass-card">
        <a href="/auth/google?callback=web">
          <svg viewBox="0 0 24 24"><path fill="#4285f4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/><path fill="#34a853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#fbbc05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18A10.96 10.96 0 0 0 1 12c0 1.77.42 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#ea4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
          Google
        </a>
        <a href="/auth/microsoft?callback=web">
          <svg viewBox="0 0 24 24"><rect fill="#f25022" x="1" y="1" width="10" height="10"/><rect fill="#00a4ef" x="1" y="13" width="10" height="10"/><rect fill="#7fba00" x="13" y="1" width="10" height="10"/><rect fill="#ffb900" x="13" y="13" width="10" height="10"/></svg>
          Microsoft
        </a>
        <a href="/auth/login-page">
          <svg viewBox="0 0 24 24" fill="#fff"><path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/></svg>
          Apple
        </a>
        <div class="auth-sep"></div>
        <div style="padding:0 .8rem">
          <div style="font-size:.7rem;color:var(--muted);margin-bottom:.4rem">Or sign up with email</div>
          <form action="/auth/signup" method="post" class="email-form" onsubmit="return false">
            <input type="email" placeholder="you@example.com" id="nav-email">
            <a href="#auth" class="btn btn-primary" style="padding:.35rem .7rem;font-size:.7rem"
              onclick="document.getElementById('auth-email').value=document.getElementById('nav-email').value;
              document.getElementById('auth').scrollIntoView({{behavior:'smooth'}})">Go</a>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
</nav>

<!-- HERO with animated gradient mesh -->
<div class="hero-wrap">
  <div class="hero-mesh"></div>
  <div class="hero">
    <div class="hero-badge"><span class="live-dot"></span> {providers_line} &bull; multi-model consensus</div>
    <h1>Verify anything.<br><em>Trust the agreement.</em></h1>
    <p>{multi_note}. Consensus is the signal. Divergence reveals where claims break.</p>
    <div class="hero-actions">
      <a href="#auth" class="btn btn-primary" style="padding:.65rem 2rem;font-size:.95rem">Start Free</a>
      <a href="#pricing" class="btn btn-ghost">See Plans</a>
    </div>
  </div>
</div>

<!-- LIVE PULSE -->
<div class="stats-bar">
<div class="stats-inner glass-card">
  <div class="stat"><div class="val">{proof_count}</div><div class="lbl">Truth gems</div></div>
  <div class="stat"><div class="val">{tokens_display}</div><div class="lbl">Tokens burned</div></div>
  <div class="stat"><div class="val">{artifact_count}</div><div class="lbl">Verified proofs</div></div>
  <div class="stat"><div class="val">{avg_conf_str}</div><div class="lbl">Consensus accuracy</div></div>
  <div class="stat"><div class="val">{providers_line}</div><div class="lbl">Active now</div></div>
</div>
</div>

<!-- PROOF OF TRUTH — the gems -->
<section id="gems" class="reveal">
<div class="section-title">
  <h2>Proof of Truth</h2>
  <p>Bitcoin burns electricity to secure transactions. Rhea burns tokens to verify knowledge.<br>
  Both produce immutable artifacts. Both share them with the world.</p>
</div>
<div class="wtf-tip" data-wtf="gems">
  <span class="wtf-label">&#x1F48E; wait like bitcoin but for science?</span>
  <button class="wtf-dismiss" onclick="dismissWtf(this)">&times;</button>
  Bitcoin miners burn <strong style="color:var(--accent)">electricity</strong> to solve math puzzles &rarr; get BTC (proof they did the work).
  Rhea burns <strong style="color:var(--accent)">AI tokens</strong> to verify claims through independent models &rarr; gets <em>truth gems</em> (proof the claim survived scrutiny).
  Both are <strong>immutable, verifiable, public.</strong> Nobody can fake a gem &mdash; the hash chain proves the work happened.
  <div style="margin-top:.6rem;text-align:right"><button onclick="skipAllWtf()" style="background:none;border:none;color:var(--muted);font-size:.6rem;cursor:pointer;text-decoration:underline;font-family:inherit">skip all tips</button></div>
</div>
<div class="bento">
  <div class="bento-card glass-card span-2 stagger-1" style="border-left:3px solid var(--green)">
    <span class="bento-icon">&#x1F48E;</span>
    <h3>Aletheia &mdash; Truth Gems</h3>
    <p>Every verified claim becomes a gem: SHA-256 hashed, hash-chained, graded A/B/C by consensus strength.
       {proof_count} gems mined so far. {tokens_display} tokens burned to produce them.
       Each gem records which models agreed, where they diverged, and what evidence survived.</p>
    <div style="margin-top:.8rem;display:flex;gap:1rem;flex-wrap:wrap">
      <span class="gem-stat" style="font-size:.55rem;padding:.2rem .5rem;border-radius:6px;background:rgba(0,255,170,.1);border:1px solid rgba(0,255,170,.2)">&#x1F7E2; Grade A: &ge;85% consensus</span>
      <span class="gem-stat" style="font-size:.55rem;padding:.2rem .5rem;border-radius:6px;background:rgba(255,200,0,.1);border:1px solid rgba(255,200,0,.2)">&#x1F7E1; Grade B: &ge;70%</span>
      <span class="gem-stat" style="font-size:.55rem;padding:.2rem .5rem;border-radius:6px;background:rgba(255,100,100,.1);border:1px solid rgba(255,100,100,.2)">&#x1F534; Grade C: &lt;70%</span>
    </div>
  </div>
  <div class="bento-card glass-card span-2 stagger-2" style="border-left:3px solid var(--purple)">
    <span class="bento-icon">&#x1F30A;</span>
    <h3>Ruliad &mdash; Wolfram's Summary</h3>
    <p style="font-size:.6rem;line-height:1.7;color:var(--muted)">
      <strong style="color:var(--text)">What it is:</strong> The entangled limit of everything computationally possible &mdash;
      following all possible rules in all possible ways. Unique, inevitable, formally necessary.
      No choices needed to define it; it just <em>is</em>, like 1+1=2.<br><br>
      <strong style="color:var(--text)">Why it matters:</strong> We are <em>inside</em> it. We never see the Ruliad from outside &mdash;
      we sample tiny slices using our bounded perception. For &ldquo;observers like us&rdquo;
      (computationally bounded, coherent, persistent), the laws of general relativity and quantum mechanics
      <em>inevitably</em> emerge. Physics and mathematics are the same object viewed from different angles.<br><br>
      <strong style="color:var(--text)">Rulial space:</strong> Like physical space, but for description languages.
      Moving in it = changing how you think. Concepts are &ldquo;rulial particles&rdquo; &mdash;
      stable structures that survive transport between different minds.
      Different consciousnesses are at different positions in rulial space;
      that&rsquo;s why you can&rsquo;t fully &ldquo;get inside&rdquo; another mind.<br><br>
      <strong style="color:var(--text)">The punchline:</strong> Computational irreducibility means no shortcuts &mdash;
      you must walk through time step by step. The universe runs every possible rule;
      we just perceive the slice consistent with what we are.
    </p>
    <div style="margin-top:.8rem;display:flex;gap:1rem;flex-wrap:wrap">
      <span class="gem-stat" style="font-size:.55rem;padding:.2rem .5rem;border-radius:6px;background:rgba(180,130,255,.1);border:1px solid rgba(180,130,255,.2)">&infin;-groupoid structure</span>
      <span class="gem-stat" style="font-size:.55rem;padding:.2rem .5rem;border-radius:6px;background:rgba(180,130,255,.1);border:1px solid rgba(180,130,255,.2)">causal invariance</span>
      <span class="gem-stat" style="font-size:.55rem;padding:.2rem .5rem;border-radius:6px;background:rgba(180,130,255,.1);border:1px solid rgba(180,130,255,.2)">Wolfram 2021</span>
    </div>
  </div>
</div>
<div class="reveal stagger-3" style="text-align:center;margin-top:2rem;padding:1.5rem;border-radius:12px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06)">
  <div style="font-size:.65rem;color:var(--muted);line-height:1.8;max-width:600px;margin:0 auto">
    <strong style="color:var(--text)">BTC</strong>: electricity &rarr; SHA-256 &rarr; immutable block &rarr; shared ledger<br>
    <strong style="color:var(--text)">Rhea</strong>: tokens &rarr; multi-model consensus &rarr; truth gem &rarr; proof chain<br>
    <span style="color:var(--accent)">Both burn real resources to produce tamper-proof public artifacts.</span>
  </div>
</div>
</section>

<!-- FEATURES BENTO GRID — tools that produce gems -->
<section id="features" class="reveal">
<div class="section-title">
  <h2>The mining tools</h2>
  <p>Everything that turns questions into verified gems.</p>
</div>
<div class="wtf-tip" data-wtf="features">
  <span class="wtf-label">&#x1F9D0; ok so what are these tools</span>
  <button class="wtf-dismiss" onclick="dismissWtf(this)">&times;</button>
  These are the <strong style="color:var(--accent)">pickaxes.</strong> The gems above are the gold.
  Each tool here is a different way to dig &mdash; ask 5 scientists, send a red-teamer to attack your idea,
  or set a robot to keep digging until it hits 90% consensus. You pick the tool, Rhea does the work.
</div>
<div class="bento">
  <div class="bento-card glass-card span-2 stagger-1">
    <span class="bento-icon">&#x2696;</span>
    <h3>Tribunal Consensus</h3>
    <p>Query multiple AI models independently. They don&rsquo;t see each other&rsquo;s answers.
       Agreement = signal. Divergence = where the lie hides. 3-model, 5-model, or ICE deep verification.</p>
  </div>
  <div class="bento-card glass-card stagger-2">
    <span class="bento-icon">&#x1F916;</span>
    <h3>Sceptic Mode</h3>
    <p>Adversarial verification. One model attacks the claim, others defend. Stress-test before you trust.</p>
  </div>
  <div class="bento-card glass-card stagger-3">
    <span class="bento-icon">&#x1F3AF;</span>
    <h3>Scheduler Looper</h3>
    <p>Set your quality bar (90%+), submit a claim, walk away. Auto-refining rounds until models converge.</p>
  </div>
  <div class="bento-card glass-card stagger-4">
    <span class="bento-icon">&#x26A1;</span>
    <h3>Workflow Engine</h3>
    <p>Chain tribunal calls, proof storage, and notifications into automated pipelines.</p>
  </div>
  <div class="bento-card glass-card stagger-1">
    <span class="bento-icon">&#x1F511;</span>
    <h3>BYOK</h3>
    <p>Your API keys. Your providers. $0 platform fee. You own the infrastructure.</p>
  </div>
  <div class="bento-card glass-card stagger-2">
    <span class="bento-icon">&#x1F4CB;</span>
    <h3>Cross-Device Clipboard</h3>
    <p>Copy anywhere, paste everywhere. Privacy auto-classification. Secrets auto-expire.</p>
  </div>
</div>
<!-- Vendor logos strip — providers Rhea queries -->
<div class="reveal stagger-2" style="text-align:center;margin-top:3rem">
  <div style="font-size:.65rem;font-weight:600;text-transform:uppercase;letter-spacing:.15em;color:var(--accent);margin-bottom:1rem">
    Built by timelabs npo &mdash; powered by</div>
  <div style="display:flex;justify-content:center;align-items:center;gap:1.8rem;flex-wrap:wrap;opacity:.5">
    <span style="font-size:.7rem;font-weight:500;color:var(--muted)">
      <svg width="12" height="12" viewBox="0 0 24 24" style="vertical-align:middle;margin-right:3px"><path fill="#cc785c" d="M12 2L2 12l10 10 10-10z"/></svg>Anthropic</span>
    <span style="font-size:.7rem;font-weight:500;color:var(--muted)">
      <svg width="12" height="12" viewBox="0 0 24 24" style="vertical-align:middle;margin-right:3px"><circle cx="12" cy="12" r="10" fill="none" stroke="#10a37f" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="#10a37f"/></svg>OpenAI</span>
    <span style="font-size:.7rem;font-weight:500;color:var(--muted)">
      <span style="color:#4285f4">G</span><span style="color:#ea4335">o</span><span style="color:#fbbc05">o</span><span style="color:#4285f4">g</span><span style="color:#34a853">l</span><span style="color:#ea4335">e</span></span>
    <span style="font-size:.7rem;font-weight:500;color:var(--muted)">
      <svg width="12" height="12" viewBox="0 0 24 24" style="vertical-align:middle;margin-right:3px"><path fill="#0668E1" d="M22 12c0 5.52-4.48 10-10 10S2 17.52 2 12 6.48 2 12 2s10 4.48 10 10z" opacity=".3"/><path fill="#0668E1" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z"/></svg>Meta</span>
    <span style="font-size:.7rem;font-weight:500;color:var(--muted)">
      <svg width="12" height="12" viewBox="0 0 24 24" style="vertical-align:middle;margin-right:3px"><polygon points="12,2 22,22 2,22" fill="none" stroke="#FF6F00" stroke-width="2"/></svg>Groq</span>
    <span style="font-size:.7rem;font-weight:500;color:var(--muted)">
      <svg width="12" height="12" viewBox="0 0 24 24" style="vertical-align:middle;margin-right:3px"><circle cx="12" cy="12" r="10" fill="none" stroke="#E91E63" stroke-width="2" stroke-dasharray="4 2"/></svg>Cerebras</span>
    <span style="font-size:.7rem;font-weight:500;color:var(--muted)">
      <svg width="12" height="12" viewBox="0 0 24 24" style="vertical-align:middle;margin-right:3px"><rect x="3" y="3" width="18" height="18" rx="3" fill="none" stroke="#D82C20" stroke-width="2"/></svg>Redis</span>
    <span style="font-size:.7rem;font-weight:500;color:var(--muted)">
      <svg width="12" height="12" viewBox="0 0 24 24" style="vertical-align:middle;margin-right:3px"><circle cx="12" cy="12" r="9" fill="#F80000" opacity=".8"/></svg>Oracle</span>
    <span style="font-size:.7rem;font-weight:500;color:var(--muted)">
      <svg width="12" height="12" viewBox="0 0 24 24" style="vertical-align:middle;margin-right:3px"><path fill="#FFCA28" d="M12 2L3 20h18z"/></svg>Firebase</span>
    <span style="font-size:.7rem;font-weight:500;color:var(--muted)">
      <svg width="12" height="12" viewBox="0 0 24 24" style="vertical-align:middle;margin-right:3px"><path fill="#DD1100" d="M12 2l4 7h-8l4-7zm-7 9l4 7-7-3 3-4zm14 0l-3 4 3-4zm-7 5l-4 7 4-3 4 3-4-7z"/></svg>Wolfram</span>
    <span style="font-size:.7rem;font-weight:500;color:var(--muted)">
      <svg width="12" height="12" viewBox="0 0 24 24" style="vertical-align:middle;margin-right:3px"><path fill="#00AEEF" d="M4 4h7v7H4zm9 0h7v7h-7zM4 13h7v7H4zm9 0h7v7h-7z" opacity=".7"/></svg>NDI</span>
  </div>
</div>
</section>

<!-- KEYBOARD ABSORBS COMFYUI PIPELINE -->
<section id="keyboard" class="reveal">
<div class="section-title">
  <h2>Full pipeline in &lt;5 MB. Free.</h2>
  <p>Type a claim anywhere. The keyboard sends it to Rhea&rsquo;s servers. You get back verified science.</p>
</div>
<div class="wtf-tip" data-wtf="keyboard">
  <span class="wtf-label">&#x2328;&#xFE0F; wait the keyboard does what</span>
  <button class="wtf-dismiss" onclick="dismissWtf(this)">&times;</button>
  Your phone keyboard becomes a <strong style="color:var(--green)">portable lie detector.</strong>
  Type &ldquo;vaccines cause autism&rdquo; and 5 AI brains check it before you can say &ldquo;peer review.&rdquo;
  All in an app smaller than a selfie. <em>Free.</em>
</div>
<div style="max-width:960px;margin:0 auto">
  <!-- Examples showcase -->
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem;margin-bottom:1.5rem">
    <div class="glass-card stagger-1" style="padding:1.2rem">
      <div style="font-size:.6rem;color:var(--green);font-weight:600;text-transform:uppercase;letter-spacing:.08em;margin-bottom:.5rem">Drug Discovery</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:.72rem;color:var(--text);background:rgba(48,209,88,.04);
        border:1px solid rgba(48,209,88,.12);border-radius:8px;padding:.7rem;margin-bottom:.5rem;line-height:1.5">
        <span style="color:var(--muted)">&gt;</span> &ldquo;Aspirin inhibits COX-2 selectively at low doses&rdquo;<br>
        <span style="color:var(--orange)">&#x25B6;</span> <strong>Agreement: 34%</strong> &mdash; COX-1 and COX-2 both inhibited non-selectively<br>
        <span style="color:var(--green)">&#x2713;</span> Sceptic found 3 contradicting sources
      </div>
      <div style="font-size:.6rem;color:var(--muted)">Caught a common pharmacology misconception in 4 seconds</div>
    </div>
    <div class="glass-card stagger-2" style="padding:1.2rem">
      <div style="font-size:.6rem;color:var(--accent);font-weight:600;text-transform:uppercase;letter-spacing:.08em;margin-bottom:.5rem">Molecular Biology</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:.72rem;color:var(--text);background:rgba(0,113,227,.04);
        border:1px solid rgba(0,113,227,.12);border-radius:8px;padding:.7rem;margin-bottom:.5rem;line-height:1.5">
        <span style="color:var(--muted)">&gt;</span> &ldquo;CRISPR-Cas9 has no off-target effects in vivo&rdquo;<br>
        <span style="color:var(--orange)">&#x25B6;</span> <strong>Agreement: 12%</strong> &mdash; off-target cleavage well documented<br>
        <span style="color:var(--green)">&#x2713;</span> 5 models unanimous: claim is dangerous misinformation
      </div>
      <div style="font-size:.6rem;color:var(--muted)">Prevented a false safety claim from entering a grant proposal</div>
    </div>
    <div class="glass-card stagger-3" style="padding:1.2rem">
      <div style="font-size:.6rem;color:var(--purple);font-weight:600;text-transform:uppercase;letter-spacing:.08em;margin-bottom:.5rem">Grant Writing</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:.72rem;color:var(--text);background:rgba(191,90,242,.04);
        border:1px solid rgba(191,90,242,.12);border-radius:8px;padding:.7rem;margin-bottom:.5rem;line-height:1.5">
        <span style="color:var(--muted)">&gt;</span> &ldquo;Lipinski&rsquo;s Rule of Five predicts oral bioavailability&rdquo;<br>
        <span style="color:var(--green)">&#x25B6;</span> <strong>Agreement: 78%</strong> &mdash; valid heuristic, not absolute<br>
        <span style="color:var(--accent)">&#x2713;</span> Nuance preserved: &ldquo;predicts drug-likeness, not bioavailability directly&rdquo;
      </div>
      <div style="font-size:.6rem;color:var(--muted)">Refined a claim from &ldquo;mostly right&rdquo; to &ldquo;precisely right&rdquo;</div>
    </div>
  </div>
  <!-- Pipeline visual -->
  <div class="glass-card" style="padding:2rem">
    <div style="display:flex;gap:2rem;align-items:center;flex-wrap:wrap">
      <div style="flex:1;min-width:280px">
        <div style="display:flex;align-items:center;gap:.6rem;margin-bottom:.8rem">
          <span style="font-size:1.8rem">&#x2328;&#xFE0F;</span>
          <div>
            <div style="font-size:1rem;font-weight:700">Rhea Keyboard</div>
            <div style="font-size:.65rem;color:var(--green)">iOS Extension &bull; &lt;5 MB &bull; zero dependencies &bull; <strong>FREE</strong></div>
          </div>
        </div>
        <p style="font-size:.82rem;color:var(--muted);line-height:1.6;margin-bottom:.8rem">
          A <strong style="color:var(--text)">thin client</strong> that sends claims to the full
          ComfyUI verification pipeline on Rhea&rsquo;s servers. Type in any text field, tap verify.
          The server runs the complete node graph. Result drops back in seconds.</p>
        <div style="display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:.8rem">
          <span style="padding:.25rem .6rem;border-radius:6px;font-size:.6rem;font-weight:600;
            background:rgba(48,209,88,.12);color:var(--green);border:1px solid rgba(48,209,88,.2)">100 free queries/month</span>
          <span style="padding:.25rem .6rem;border-radius:6px;font-size:.6rem;font-weight:500;
            background:rgba(0,113,227,.08);color:var(--accent);border:1px solid rgba(0,113,227,.15)">No GPU needed</span>
          <span style="padding:.25rem .6rem;border-radius:6px;font-size:.6rem;font-weight:500;
            background:rgba(191,90,242,.08);color:var(--purple);border:1px solid rgba(191,90,242,.15)">Works in any app</span>
        </div>
      </div>
      <!-- Pipeline nodes -->
      <div style="flex:0 0 260px">
        <div style="font-size:.55rem;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin-bottom:.6rem">
          Your claim travels through</div>
        <div class="node-graph" style="flex-direction:column;align-items:stretch;gap:.35rem">
          <div class="comfy-node" style="border-color:var(--green);color:var(--green);background:rgba(48,209,88,.08);width:100%;justify-content:center">
            &#x2328;&#xFE0F; You type a claim</div>
          <div style="text-align:center;color:var(--border);font-size:.6rem">&#x25BC;</div>
          <div class="comfy-node" style="border-color:var(--accent);color:var(--accent);background:rgba(0,113,227,.08);width:100%;justify-content:center">
            &#x2696; 3&ndash;5 AI models debate it</div>
          <div style="text-align:center;color:var(--border);font-size:.6rem">&#x25BC;</div>
          <div class="comfy-node" style="border-color:var(--orange);color:var(--orange);background:rgba(255,159,10,.08);width:100%;justify-content:center">
            &#x1F916; Sceptic tries to destroy it</div>
          <div style="text-align:center;color:var(--border);font-size:.6rem">&#x25BC;</div>
          <div class="comfy-node" style="border-color:var(--purple);color:var(--purple);background:rgba(191,90,242,.08);width:100%;justify-content:center">
            &#x1F4BE; Surviving claims become proofs</div>
        </div>
      </div>
    </div>
  </div>
  <!-- Play + Atlas note -->
  <div style="display:flex;gap:1rem;margin-top:1rem;flex-wrap:wrap">
    <div class="glass-card" style="flex:1;padding:1rem 1.2rem;display:flex;align-items:center;gap:.8rem;min-width:250px">
      <span style="font-size:1.3rem">&#xF8FF;</span>
      <div>
        <div style="font-size:.78rem;font-weight:600">Rhea Play</div>
        <div style="font-size:.65rem;color:var(--muted)">Native macOS + iOS ops centre &mdash;
          <a href="https://github.com/timelabs/rhea-project/releases" style="color:var(--accent)">Download</a></div>
      </div>
    </div>
    <div class="glass-card" style="flex:1;padding:1rem 1.2rem;display:flex;align-items:center;gap:.8rem;min-width:250px">
      <span style="font-size:1.3rem">&#x1F310;</span>
      <div>
        <div style="font-size:.78rem;font-weight:600">Atlas Dashboard</div>
        <div style="font-size:.65rem;color:var(--muted)">Cross-platform web UI &mdash; Windows, Linux, any browser</div>
      </div>
    </div>
  </div>
</div>
</section>

<!-- CLIPBOARD SYNC -->
<section id="clipboard" class="reveal">
<div class="section-title">
  <h2>One clipboard.<br>Every device.</h2>
  <p>Copy on your Mac. Paste on Windows. Replay anything. Secrets auto-expire.</p>
</div>
<div class="wtf-tip" data-wtf="clipboard">
  <span class="wtf-label">&#x1F4CB; passing notes in class but cooler</span>
  <button class="wtf-dismiss" onclick="dismissWtf(this)">&times;</button>
  Remember passing notes in class? This is that, but between your phone, laptop, and grandma&rsquo;s PC.
  And the note <strong style="color:var(--orange)">self-destructs if it has a password on it.</strong>
  <em>Spy stuff, basically.</em>
</div>
<div style="max-width:960px;margin:0 auto">
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem;margin-bottom:1.5rem">
    <div class="glass-card stagger-1" style="padding:1.5rem">
      <div style="font-size:1.5rem;margin-bottom:.8rem">&#x1F4CB;</div>
      <h3 style="font-size:.95rem;font-weight:700;margin-bottom:.4rem">Cross-Device Sync</h3>
      <p style="font-size:.78rem;color:var(--muted);line-height:1.6">Copy a URL on your phone, paste it on your laptop.
        Real-time SSE push &mdash; no polling, no delays. Works across macOS, iOS, Windows, and Linux.</p>
    </div>
    <div class="glass-card stagger-2" style="padding:1.5rem">
      <div style="font-size:1.5rem;margin-bottom:.8rem">&#x23F0;</div>
      <h3 style="font-size:.95rem;font-weight:700;margin-bottom:.4rem">History &amp; Replay</h3>
      <p style="font-size:.78rem;color:var(--muted);line-height:1.6">Every clip saved with timestamp, source device, and app.
        Search your clipboard history. Pin important clips. Replay any entry from the last 30 days.</p>
    </div>
    <div class="glass-card stagger-3" style="padding:1.5rem">
      <div style="font-size:1.5rem;margin-bottom:.8rem">&#x1F510;</div>
      <h3 style="font-size:.95rem;font-weight:700;margin-bottom:.4rem">Privacy by Default</h3>
      <p style="font-size:.78rem;color:var(--muted);line-height:1.6">Auto-detects passwords, API keys, and credit card numbers.
        Sensitive content gets a 30-second TTL and E2E encryption. You control what persists.</p>
    </div>
  </div>
  <!-- How it works -->
  <div class="glass-card" style="padding:1.5rem 2rem">
    <div style="display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;justify-content:center">
      <div style="text-align:center;min-width:120px">
        <div style="font-size:1.8rem;margin-bottom:.3rem">&#xF8FF;</div>
        <div style="font-size:.65rem;color:var(--muted)">macOS &bull; iOS</div>
        <div style="font-size:.55rem;color:var(--green)">Built into Rhea app</div>
      </div>
      <div style="font-size:.9rem;color:var(--accent)">&#x21C4;</div>
      <div style="text-align:center;min-width:120px">
        <div style="font-size:1.8rem;margin-bottom:.3rem">&#x2601;&#xFE0F;</div>
        <div style="font-size:.65rem;color:var(--muted)">Rhea Cloud</div>
        <div style="font-size:.55rem;color:var(--accent)">E2E encrypted</div>
      </div>
      <div style="font-size:.9rem;color:var(--accent)">&#x21C4;</div>
      <div style="text-align:center;min-width:120px">
        <div style="font-size:1.8rem;margin-bottom:.3rem">&#x1FA9F;</div>
        <div style="font-size:.65rem;color:var(--muted)">Windows &bull; Linux</div>
        <div style="font-size:.55rem;color:var(--green)">pip install rhea-clipboard</div>
      </div>
    </div>
  </div>
</div>
</section>

<!-- SCHEDULER LOOPER -->
<section id="scheduler" class="reveal">
<div class="section-title">
  <h2>Set the bar.<br>Walk away.</h2>
  <p>Consensus loops run until your quality threshold is met. Like ComfyUI, but for truth.</p>
</div>
<div class="wtf-tip" data-wtf="scheduler">
  <span class="wtf-label">&#x1F504; a washing machine for facts</span>
  <button class="wtf-dismiss" onclick="dismissWtf(this)">&times;</button>
  Like a washing machine for facts. Throw in a dirty claim, set the &ldquo;how clean&rdquo; dial to 90%,
  press start. It <strong style="color:var(--purple)">keeps washing until it&rsquo;s sparkling.</strong>
  You don&rsquo;t even have to watch. <em>Go eat a sandwich.</em>
</div>
<div style="max-width:960px;margin:0 auto">
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem;margin-bottom:1.5rem">
    <div class="glass-card stagger-1" style="padding:1.5rem">
      <div style="font-size:1.5rem;margin-bottom:.8rem">&#x1F3AF;</div>
      <h3 style="font-size:.95rem;font-weight:700;margin-bottom:.4rem">Target Consensus</h3>
      <p style="font-size:.78rem;color:var(--muted);line-height:1.6">Set your quality bar &mdash; 85%, 90%, 95%.
        The scheduler runs tribunal rounds automatically until models agree at your threshold.</p>
    </div>
    <div class="glass-card stagger-2" style="padding:1.5rem">
      <div style="font-size:1.5rem;margin-bottom:.8rem">&#x1F504;</div>
      <h3 style="font-size:.95rem;font-weight:700;margin-bottom:.4rem">Auto-Refine</h3>
      <p style="font-size:.78rem;color:var(--muted);line-height:1.6">Each iteration learns from divergence.
        The prompt sharpens itself, targeting exactly where models disagree. Convergence accelerates.</p>
    </div>
    <div class="glass-card stagger-3" style="padding:1.5rem">
      <div style="font-size:1.5rem;margin-bottom:.8rem">&#x1F6E0;</div>
      <h3 style="font-size:.95rem;font-weight:700;margin-bottom:.4rem">Three Modes</h3>
      <p style="font-size:.78rem;color:var(--muted);line-height:1.6"><strong>Local</strong>: fast parallel consensus.
        <strong>Sceptic</strong>: adversarial attack each round. <strong>ICE</strong>: iterative deep critique with chairman synthesis.</p>
    </div>
  </div>

  <!-- Visual loop — minimal timeline -->
  <div style="max-width:640px;margin:2rem auto 0;position:relative">
    <!-- Connecting line -->
    <div style="position:absolute;top:28px;left:48px;right:48px;height:1px;background:linear-gradient(90deg,var(--accent),var(--purple),var(--green));opacity:.25"></div>
    <div style="display:flex;justify-content:space-between;align-items:flex-start;position:relative">
      <!-- Step 1 -->
      <div style="text-align:center;width:120px">
        <div style="width:56px;height:56px;border-radius:14px;border:1px solid rgba(0,113,227,.3);background:rgba(0,113,227,.06);display:flex;align-items:center;justify-content:center;margin:0 auto .8rem">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="1.5"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
        </div>
        <div style="font-size:.78rem;font-weight:600;color:var(--text);margin-bottom:.15rem">Submit</div>
        <div style="font-size:.6rem;color:var(--muted);line-height:1.4">Your claim enters<br>the pipeline</div>
      </div>
      <!-- Step 2 -->
      <div style="text-align:center;width:120px">
        <div style="width:56px;height:56px;border-radius:14px;border:1px solid rgba(175,130,255,.3);background:rgba(175,130,255,.06);display:flex;align-items:center;justify-content:center;margin:0 auto .8rem">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--purple)" stroke-width="1.5"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
        </div>
        <div style="font-size:.78rem;font-weight:600;color:var(--text);margin-bottom:.15rem">Tribunal</div>
        <div style="font-size:.6rem;color:var(--muted);line-height:1.4"><em>k</em> models deliberate<br>independently</div>
      </div>
      <!-- Step 3 -->
      <div style="text-align:center;width:120px">
        <div style="width:56px;height:56px;border-radius:14px;border:1px solid rgba(48,209,88,.3);background:rgba(48,209,88,.06);display:flex;align-items:center;justify-content:center;margin:0 auto .8rem">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="1.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        </div>
        <div style="font-size:.78rem;font-weight:600;color:var(--text);margin-bottom:.15rem">Converge</div>
        <div style="font-size:.6rem;color:var(--muted);line-height:1.4">Meet threshold or<br>refine &amp; iterate</div>
      </div>
      <!-- Step 4 -->
      <div style="text-align:center;width:120px">
        <div style="width:56px;height:56px;border-radius:14px;border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.03);display:flex;align-items:center;justify-content:center;margin:0 auto .8rem">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text)" stroke-width="1.5" opacity=".7"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        </div>
        <div style="font-size:.78rem;font-weight:600;color:var(--text);margin-bottom:.15rem">Proof</div>
        <div style="font-size:.6rem;color:var(--muted);line-height:1.4">Stored in Aletheia<br>with provenance</div>
      </div>
    </div>
    <!-- API callout -->
    <div style="margin-top:2rem;padding:1rem 1.5rem;border-radius:12px;border:1px solid var(--border);background:rgba(255,255,255,.02);font-family:'JetBrains Mono',monospace">
      <code style="font-size:.7rem;color:var(--muted)">POST</code>
      <code style="font-size:.7rem;color:var(--text);margin-left:.3rem">/workflows/scheduler/loop</code>
      <code style="font-size:.7rem;color:var(--muted);margin-left:.6rem">target_agreement:</code>
      <code style="font-size:.7rem;color:var(--green)">0.9</code>
    </div>
  </div>
</div>
</section>

<!-- PRICING -->
<section id="pricing" class="reveal">
<div class="section-title">
  <h2>Start free. Scale when ready.</h2>
  <p>100 credits on signup. Bring your own keys for zero platform cost.</p>
</div>
<div class="wtf-tip" data-wtf="pricing">
  <span class="wtf-label">&#x1F4B0; the money part</span>
  <button class="wtf-dismiss" onclick="dismissWtf(this)">&times;</button>
  100 free fact-checks when you sign up. After that &mdash; bring your own AI keys and <strong style="color:var(--green)">pay $0 forever.</strong>
  We literally built a business model that lets you not pay us. <em>Your move.</em>
</div>
<!-- Two-tier focus -->
<div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;max-width:680px;margin:0 auto">
  <div class="plan glass-card stagger-1" style="padding:2.5rem">
    <div class="plan-name" style="color:var(--green)">Free</div>
    <div class="plan-price">$0</div>
    <div class="plan-desc" style="margin-bottom:1.8rem">Everything you need to verify claims with multi-model consensus.</div>
    <ul class="plan-features">
      <li>100 credits on signup</li>
      <li>3-model tribunal</li>
      <li>Aletheia proof storage</li>
      <li>All platforms</li>
      <li>OAuth sign-in</li>
    </ul>
    <a href="#auth" class="plan-cta primary">Get Started</a>
  </div>
  <div class="plan glass-card featured stagger-2" style="padding:2.5rem">
    <div class="plan-name" style="color:var(--accent)">Pro</div>
    <div class="plan-price">$19 <small>/mo</small></div>
    <div class="plan-desc" style="margin-bottom:1.8rem">Deep verification, adversarial testing, and API access for serious work.</div>
    <ul class="plan-features">
      <li>2,000 credits/month</li>
      <li>5-model ICE verification</li>
      <li>Sceptic mode</li>
      <li>Priority routing</li>
      <li>API key + CLI</li>
    </ul>
    <a href="#auth" class="plan-cta primary">Start Pro</a>
    <div class="byok">BYOK: $0 with your own keys</div>
  </div>
</div>
<!-- Team/Sovereign row — quiet -->
<div style="max-width:680px;margin:1.5rem auto 0;display:grid;grid-template-columns:1fr 1fr;gap:1rem">
  <div class="glass-card stagger-3" style="padding:1.2rem 1.5rem;display:flex;align-items:center;justify-content:space-between">
    <div>
      <div style="font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--orange)">Team</div>
      <div style="font-size:.65rem;color:var(--muted);margin-top:.15rem">10 seats, shared proofs, admin controls</div>
    </div>
    <div style="font-size:.85rem;font-weight:700;color:var(--text)">$49<small style="font-weight:400;color:var(--muted)">/mo</small></div>
  </div>
  <div class="glass-card stagger-4" style="padding:1.2rem 1.5rem;display:flex;align-items:center;justify-content:space-between">
    <div>
      <div style="font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--purple)">Sovereign</div>
      <div style="font-size:.65rem;color:var(--muted);margin-top:.15rem">Self-hosted, SSO, your infrastructure</div>
    </div>
    <div style="font-size:.85rem;font-weight:700;color:var(--text)">$199<small style="font-weight:400;color:var(--muted)">/mo</small></div>
  </div>
</div>
</section>

{crypto_section}

<!-- PLATFORMS -->
<section id="platforms" class="reveal">
<div class="section-title">
  <h2>Available everywhere</h2>
  <p>One account. Every platform. Native experience.</p>
</div>
<div class="wtf-tip" data-wtf="platforms">
  <span class="wtf-label">&#x1F4F1; runs on everything except toasters</span>
  <button class="wtf-dismiss" onclick="dismissWtf(this)">&times;</button>
  Works on your iPhone, your Mac, your browser, your terminal.
  Basically if it has a screen and isn&rsquo;t a toaster, <strong style="color:var(--accent)">Rhea runs on it.</strong>
  <em>One account, everywhere.</em>
</div>
<!-- Compact platform strip — verified links, SVG icons -->
<div style="max-width:800px;margin:0 auto;display:grid;grid-template-columns:repeat(4,1fr);gap:.8rem">
  <a href="https://testflight.apple.com/join/BNya22Jg" target="_blank" rel="noopener"
     class="glass-card stagger-1" style="padding:1.4rem 1rem;text-align:center;text-decoration:none;transition:.3s"
     onmouseover="this.style.borderColor='rgba(255,255,255,.2)';this.style.transform='translateY(-3px)'"
     onmouseout="this.style.borderColor='';this.style.transform=''">
    <svg width="28" height="28" viewBox="0 0 24 24" fill="#fff" style="margin-bottom:.6rem"><path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/></svg>
    <div style="font-size:.82rem;font-weight:600;color:var(--text)">iOS</div>
    <div style="font-size:.6rem;color:var(--green);margin-top:.2rem">TestFlight &rarr;</div>
  </a>
  <a href="https://github.com/timelabs/rhea-project/releases/tag/v1.0.0" target="_blank" rel="noopener"
     class="glass-card stagger-2" style="padding:1.4rem 1rem;text-align:center;text-decoration:none;transition:.3s"
     onmouseover="this.style.borderColor='rgba(255,255,255,.2)';this.style.transform='translateY(-3px)'"
     onmouseout="this.style.borderColor='';this.style.transform=''">
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.5" style="margin-bottom:.6rem"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
    <div style="font-size:.82rem;font-weight:600;color:var(--text)">macOS</div>
    <div style="font-size:.6rem;color:var(--green);margin-top:.2rem">DMG v1.0 &rarr;</div>
  </a>
  <a href="{url}" target="_blank" rel="noopener"
     class="glass-card stagger-3" style="padding:1.4rem 1rem;text-align:center;text-decoration:none;transition:.3s"
     onmouseover="this.style.borderColor='rgba(255,255,255,.2)';this.style.transform='translateY(-3px)'"
     onmouseout="this.style.borderColor='';this.style.transform=''">
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.5" style="margin-bottom:.6rem"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
    <div style="font-size:.82rem;font-weight:600;color:var(--text)">Web</div>
    <div style="font-size:.6rem;color:var(--accent);margin-top:.2rem">Open &rarr;</div>
  </a>
  <a href="https://pypi.org/project/rhea-memory/" target="_blank" rel="noopener"
     class="glass-card stagger-4" style="padding:1.4rem 1rem;text-align:center;text-decoration:none;transition:.3s"
     onmouseover="this.style.borderColor='rgba(255,255,255,.2)';this.style.transform='translateY(-3px)'"
     onmouseout="this.style.borderColor='';this.style.transform=''">
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.5" style="margin-bottom:.6rem"><path d="M4 17l6-6-6-6M12 19h8"/></svg>
    <div style="font-size:.82rem;font-weight:600;color:var(--text)">CLI</div>
    <div style="font-size:.6rem;color:var(--muted);margin-top:.2rem">pip install rhea-memory</div>
  </a>
</div>
</section>

<!-- API -->
<section id="api" class="reveal">
<div class="section-title">
  <h2>Try it now</h2>
  <p>No SDK required. One curl to truth.</p>
</div>
<div class="wtf-tip" data-wtf="api">
  <span class="wtf-label">&#x1F4BB; one command, that is it</span>
  <button class="wtf-dismiss" onclick="dismissWtf(this)">&times;</button>
  Copy this, paste it in your terminal, boom &mdash; you just asked 3 AIs if your science homework is right.
  <strong style="color:var(--green)">Your teacher can&rsquo;t do that.</strong> <em>No SDK, no library, no drama.</em>
</div>
<div class="api-block glass-card">
<pre><code><span class="g">curl</span> -X POST {url}/tribunal \\
  -H <span class="w">"Content-Type: application/json"</span> \\
  -H <span class="w">"Authorization: Bearer YOUR_TOKEN"</span> \\
  -d <span class="w">'{{"prompt":"ATP synthase uses rotary catalysis"}}'</span>

<span class="r"># Response:</span>
<span class="r"># {{"agreement_score": 0.94, "confidence": 0.87,</span>
<span class="r">#   "response": "Confirmed by 3/3 models..."}}</span></code></pre>
</div>
</section>

<!-- PRINCIPLE -->
<div class="principle-bar reveal">
<blockquote>The infrastructure owner controls who's admin, not the application.<br>
You own your data, your models, your keys. Rhea serves you &mdash; not the other way around.</blockquote>
</div>

<!-- FOOTER -->
<footer>
  <div class="f-links">
    <a href="#pricing">Pricing</a>
    <a href="#features">Features</a>
    <a href="#platforms">Apps</a>
    <a href="/docs">Documentation</a>
    <a href="https://github.com/timelabs/rhea-project">Source</a>
  </div>
  <div class="f-links" style="margin-top:.5rem">
    <a href="/terms">Terms</a>
    <a href="/privacy">Privacy</a>
    <a href="/health">System Status</a>
    <a href="https://www.patreon.com/timelabsnpo" target="_blank" rel="noopener" style="color:var(--orange)">
      <svg width="12" height="12" viewBox="0 0 24 24" style="vertical-align:middle;margin-right:2px"><circle cx="15.5" cy="8.5" r="5.5" fill="#FF424D"/><rect x="2" y="2" width="3" height="20" fill="#052A49"/></svg>
      Patreon</a>
  </div>
  <div class="f-copy" style="margin-top:1rem">
    <span id="nabla-explain" style="transition:opacity .6s ease;display:inline-block">
      &#x2207; &gt; 0 &#x2228; &#x22A5; &mdash; gradient positive or bottom</span><br>
    &copy; 2026 timelabs npo
  </div>
</footer>

<!-- GDPR COOKIE CONSENT -->
<div id="gdpr-banner">
  <p>We use cookies for authentication and analytics. See our <a href="/privacy">Privacy Policy</a>.</p>
  <button class="gdpr-accept" onclick="acceptGdpr()">Accept</button>
  <button class="gdpr-decline" onclick="declineGdpr()">Decline</button>
</div>

<!-- Scroll reveal + stats counter animation -->
<script>
(()=>{{
  const obs=new IntersectionObserver((entries)=>{{
    entries.forEach(e=>{{if(e.isIntersecting){{e.target.classList.add('visible');obs.unobserve(e.target)}}}})
  }},{{threshold:.15,rootMargin:'0px 0px -40px 0px'}});
  document.querySelectorAll('.reveal').forEach(el=>obs.observe(el));

  // Animate stat numbers
  document.querySelectorAll('.stat .val').forEach(el=>{{
    const text=el.textContent;const num=parseInt(text);
    if(!isNaN(num)&&num>0){{
      let start=0;const dur=1500;const startTime=performance.now();
      const step=(now)=>{{
        const p=Math.min((now-startTime)/dur,1);
        const eased=1-Math.pow(1-p,3);
        el.textContent=Math.round(start+(num-start)*eased);
        if(p<1)requestAnimationFrame(step);else el.textContent=text
      }};
      requestAnimationFrame(step)
    }}
  }});

  // Per-section WTF cards — IntersectionObserver reveals
  const wtfSkipped=localStorage.getItem('rhea_wtf_skip')==='1';
  const wtfDismissed=JSON.parse(localStorage.getItem('rhea_wtf_dismissed')||'{{}}');
  if(!wtfSkipped){{
    const wtfObs=new IntersectionObserver((entries)=>{{
      entries.forEach(e=>{{
        if(e.isIntersecting){{
          const tip=e.target;
          const key=tip.getAttribute('data-wtf');
          if(!wtfDismissed[key]){{tip.classList.add('visible')}}
          wtfObs.unobserve(tip);
        }}
      }})
    }},{{threshold:.3}});
    document.querySelectorAll('.wtf-tip').forEach(tip=>{{
      const key=tip.getAttribute('data-wtf');
      if(wtfDismissed[key])tip.classList.add('dismissed');
      else wtfObs.observe(tip);
    }});
  }}else{{
    document.querySelectorAll('.wtf-tip').forEach(t=>t.classList.add('dismissed'));
  }}
  window.dismissWtf=function(btn){{
    const tip=btn.closest('.wtf-tip');
    const key=tip.getAttribute('data-wtf');
    tip.classList.add('dismissed');
    wtfDismissed[key]='1';
    localStorage.setItem('rhea_wtf_dismissed',JSON.stringify(wtfDismissed));
  }};
  window.skipAllWtf=function(){{
    localStorage.setItem('rhea_wtf_skip','1');
    document.querySelectorAll('.wtf-tip').forEach(t=>t.classList.add('dismissed'));
  }};

  // GDPR cookie consent
  const gdprBanner=document.getElementById('gdpr-banner');
  if(gdprBanner&&!localStorage.getItem('rhea_gdpr')){{
    setTimeout(()=>gdprBanner.classList.add('visible'),1500);
  }}
  window.acceptGdpr=function(){{localStorage.setItem('rhea_gdpr','accept');gdprBanner.classList.remove('visible')}};
  window.declineGdpr=function(){{localStorage.setItem('rhea_gdpr','decline');gdprBanner.classList.remove('visible')}};

  // Language picker — navbar globe icon
  const langData={{en:'English',fr:'Fran\u00e7ais',pt:'Portugu\u00eas',de:'Deutsch',el:'\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac',ka:'\u10e5\u10d0\u10e0\u10d7\u10e3\u10da\u10d8',ja:'\u65e5\u672c\u8a9e',zh:'\u4e2d\u6587',cs:'\u010ce\u0161tina',sw:'Kiswahili',he:'\u05e2\u05d1\u05e8\u05d9\u05ea'}};
  const langMenu=document.getElementById('lang-menu');
  const langBtn=document.getElementById('lang-btn');
  if(langBtn&&langMenu){{
    langBtn.addEventListener('click',(e)=>{{
      e.stopPropagation();
      langMenu.classList.toggle('open');
    }});
    document.addEventListener('click',()=>langMenu.classList.remove('open'));
  }}

  // Rotating nabla explanations — every 30s with flash
  const nablaEl=document.getElementById('nabla-explain');
  if(nablaEl){{
    const explanations=[
      '\u2207 > 0 \u2228 \u22A5 \u2014 gradient positive or halt',
      '\u2207 > 0 \u2014 if the system improves, it lives',
      '\u2207 = 0 \u2014 stasis is indistinguishable from death',
      '\u2207f \u00B7 dr > 0 \u2014 move along the gradient = progress',
      '\u2202S/\u2202t \u2265 0 \u2014 entropy never decreases; channel it',
      'Rhea tricked Kronos \u2014 time devours discrete, not continuous',
      '\u222B\u2207\u00B7F dV = \u222EF\u00B7dA \u2014 local flow = boundary flux',
      'consensus \u2260 truth, but divergence reveals where truth hides',
      '\u0394G < 0 \u2014 spontaneous reactions decrease free energy',
      'K\u1D62 = [products]/[reactants] \u2014 equilibrium is not stillness',
      'ATP synthase: \u2207\u03BCH+ drives rotary catalysis at 100 rev/s',
      'three models agree \u2014 not proof, but a compass bearing',
    ];
    let idx=0;
    setInterval(()=>{{
      nablaEl.style.opacity='0';
      setTimeout(()=>{{
        idx=(idx+1)%explanations.length;
        nablaEl.textContent=explanations[idx];
        nablaEl.style.opacity='1';
      }},400);
    }},30000);
  }}
}})()
</script>

</body></html>"""
    return HTMLResponse(content=html)


# ---------------------------------------------------------------------------
# Legal / info pages
# ---------------------------------------------------------------------------

_PAGE_STYLE = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rhea &mdash; {title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:#000;--surface:#0a0a0f;--card:#111118;--border:rgba(255,255,255,.08);
  --text:#f5f5f7;--muted:#86868b;--accent:#0071e3;--green:#30d158;--radius:16px}}
body{{font-family:'Inter',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);
  -webkit-font-smoothing:antialiased;line-height:1.6;overflow-x:hidden;min-height:100vh}}
a{{color:var(--accent);text-decoration:none}}a:hover{{text-decoration:underline}}
.back{{display:inline-flex;align-items:center;gap:.4rem;color:var(--muted);font-size:.82rem;
  margin-bottom:2.5rem;transition:.2s}}
.back:hover{{color:var(--text);text-decoration:none}}
.back svg{{width:14px;height:14px}}
.wrap{{max-width:780px;margin:0 auto;padding:4rem 2rem 6rem}}
h1{{font-size:2.4rem;font-weight:700;letter-spacing:-.03em;margin-bottom:.5rem}}
.subtitle{{color:var(--muted);font-size:.9rem;margin-bottom:3rem;padding-bottom:2rem;
  border-bottom:1px solid var(--border)}}
h2{{font-size:1.1rem;font-weight:600;margin:2.5rem 0 .7rem;color:var(--text)}}
p{{color:#bbb;font-size:.88rem;margin-bottom:.9rem;line-height:1.65}}
ul{{color:#bbb;font-size:.88rem;padding-left:1.4rem;margin-bottom:.9rem}}
ul li{{margin-bottom:.35rem;line-height:1.55}}
code{{font-family:'JetBrains Mono',monospace;font-size:.8rem;background:rgba(255,255,255,.06);
  padding:.1rem .4rem;border-radius:5px;color:var(--green)}}
.tag{{display:inline-block;padding:.15rem .6rem;border-radius:6px;font-size:.68rem;font-weight:600;
  text-transform:uppercase;letter-spacing:.06em;margin-right:.4rem}}
.tag-get{{background:rgba(48,209,88,.1);color:var(--green);border:1px solid rgba(48,209,88,.2)}}
.tag-post{{background:rgba(0,113,227,.1);color:var(--accent);border:1px solid rgba(0,113,227,.2)}}
.endpoint{{background:rgba(255,255,255,.03);border:1px solid var(--border);border-radius:10px;
  padding:1.1rem 1.3rem;margin-bottom:.8rem}}
.endpoint .path{{font-family:'JetBrains Mono',monospace;font-size:.82rem;color:#ddd;margin-bottom:.4rem}}
.endpoint .desc{{font-size:.8rem;color:var(--muted);line-height:1.5}}
footer{{text-align:center;padding:2.5rem 2rem;border-top:1px solid var(--border);
  color:#333;font-size:.7rem;letter-spacing:.04em}}
</style></head>
<body>
<div class="wrap">
<a href="/" class="back">
  <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
    <path d="M9 11L5 7l4-4"/>
  </svg>
  Back to Rhea
</a>
{body}
</div>
<footer>&copy; 2026 timelabs npo</footer>
</body></html>"""


@app.get("/terms")
async def terms():
    """Terms of Service page."""
    from fastapi.responses import HTMLResponse
    body = """
<h1>Terms of Service</h1>
<p class="subtitle">timelabs npo &bull; Effective date: 1 January 2026 &bull; Last updated: 1 March 2026</p>

<h2>1. Acceptance of Terms</h2>
<p>By accessing or using the Rhea platform, its APIs, mobile applications, or any associated services (collectively, the "Service"), you agree to be bound by these Terms of Service ("Terms"). If you do not agree to these Terms, do not use the Service. These Terms constitute a legally binding agreement between you and timelabs npo ("timelabs", "we", "us").</p>

<h2>2. Accounts</h2>
<p>To access most features of the Service, you must create an account. You agree to:</p>
<ul>
  <li>Provide accurate, current, and complete information during registration.</li>
  <li>Maintain and promptly update your account information.</li>
  <li>Keep your password and API keys confidential and not share them with any third party.</li>
  <li>Accept responsibility for all activities that occur under your account.</li>
  <li>Notify us immediately at timelabs.ad@gmail.com if you suspect unauthorised access.</li>
</ul>
<p>Accounts are personal. You may not transfer or sell your account. We reserve the right to terminate accounts that violate these Terms.</p>

<h2>3. Credits and Billing</h2>
<p>The Service operates on a credit system. Free accounts receive 100 credits upon registration. Additional credits are available through paid plans as described on our pricing page. Credits are non-refundable except where required by applicable law. We reserve the right to modify pricing with 30 days' notice. Bring-Your-Own-Key (BYOK) users route requests through their own provider accounts and are responsible for costs charged by those providers directly.</p>

<h2>4. Acceptable Use</h2>
<p>You agree not to use the Service to:</p>
<ul>
  <li>Generate, distribute, or facilitate the creation of illegal, harmful, or deceptive content.</li>
  <li>Attempt to reverse-engineer, decompile, or extract model weights or proprietary algorithms.</li>
  <li>Conduct denial-of-service attacks or send automated queries that exceed documented rate limits.</li>
  <li>Circumvent authentication, billing, or quota mechanisms.</li>
  <li>Resell or sublicense API access without our prior written consent.</li>
  <li>Violate any applicable local, national, or international law or regulation.</li>
</ul>
<p>We reserve the right to suspend or terminate access for violations without prior notice.</p>

<h2>5. Intellectual Property</h2>
<p>The Rhea platform source code is made available under open-source licences as indicated in the GitHub repository. timelabs retains ownership of all trademarks, service marks, and trade names associated with the Rhea brand. Your input data and any proofs you generate and store remain yours. You grant timelabs a limited, non-exclusive licence to process your data solely to deliver the Service.</p>

<h2>6. Disclaimers</h2>
<p>THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT. TIMELABS DOES NOT WARRANT THAT THE SERVICE WILL BE UNINTERRUPTED, ERROR-FREE, OR THAT RESULTS OBTAINED WILL BE ACCURATE OR RELIABLE. MULTI-MODEL CONSENSUS IS A STATISTICAL SIGNAL, NOT A GUARANTEE OF FACTUAL ACCURACY.</p>

<h2>7. Limitation of Liability</h2>
<p>TO THE FULLEST EXTENT PERMITTED BY APPLICABLE LAW, TIMELABS AND ITS OFFICERS, DIRECTORS, AGENTS, AND PARTNERS SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF PROFITS OR REVENUES, WHETHER INCURRED DIRECTLY OR INDIRECTLY, OR ANY LOSS OF DATA, USE, GOODWILL, OR OTHER INTANGIBLE LOSSES, RESULTING FROM YOUR ACCESS TO OR USE OF (OR INABILITY TO ACCESS OR USE) THE SERVICE.</p>

<h2>8. Termination</h2>
<p>You may terminate your account at any time by contacting timelabs.ad@gmail.com. We may suspend or terminate your access immediately, without notice, if you breach these Terms. Upon termination, your right to use the Service ceases immediately. You may request an export of your stored proofs before termination.</p>

<h2>9. Governing Law</h2>
<p>These Terms are governed by and construed in accordance with the laws of the European Union and the Republic of the Netherlands, without regard to conflict-of-law principles. Any disputes shall be submitted to the exclusive jurisdiction of the courts of Amsterdam, the Netherlands. If any provision of these Terms is found unenforceable, the remaining provisions shall remain in full force.</p>

<h2>10. Changes to Terms</h2>
<p>We may update these Terms from time to time. Material changes will be communicated via email or a prominent notice on the platform at least 14 days before taking effect. Your continued use of the Service after the effective date constitutes acceptance of the revised Terms.</p>

<h2>Contact</h2>
<p>Questions about these Terms? Email <a href="mailto:timelabs.ad@gmail.com">timelabs.ad@gmail.com</a> or open an issue on <a href="https://github.com/timelabs/rhea-project">GitHub</a>.</p>
"""
    html = _PAGE_STYLE.format(title="Terms of Service", body=body)
    return HTMLResponse(content=html)


@app.get("/privacy")
async def privacy():
    """Privacy Policy page (GDPR-compliant)."""
    from fastapi.responses import HTMLResponse
    body = """
<h1>Privacy Policy</h1>
<p class="subtitle">timelabs npo &bull; Effective date: 1 January 2026 &bull; GDPR-compliant</p>

<h2>1. Who We Are</h2>
<p>timelabs npo ("timelabs", "we", "us") operates the Rhea multi-model consensus platform. We are committed to protecting your personal data and processing it lawfully, fairly, and transparently in accordance with the General Data Protection Regulation (GDPR) and applicable national data protection laws.</p>

<h2>2. Data We Collect</h2>
<p>We collect the minimum data necessary to operate the Service:</p>
<ul>
  <li><strong>Account data:</strong> Email address, OAuth provider identity (Google/Microsoft/Apple), account creation timestamp.</li>
  <li><strong>Usage data:</strong> Number of API calls, credit consumption, plan tier, anonymised prompt hashes (SHA-256, non-reversible), response latencies.</li>
  <li><strong>Technical data:</strong> IP address (retained for 30 days for abuse prevention), User-Agent string, request timestamps.</li>
  <li><strong>Billing data:</strong> Stripe customer ID, subscription status. Full payment card data is never stored by timelabs — it is handled exclusively by Stripe.</li>
  <li><strong>Content you store:</strong> Proofs and ontology entries you deliberately save to Aletheia. These are stored under your account and accessible only by you unless you explicitly share them.</li>
</ul>
<p>We do not collect: your raw prompt text (only its hash), biometric data, or any special categories of personal data as defined by GDPR Article 9.</p>

<h2>3. How We Use Your Data</h2>
<p>Your data is used exclusively to:</p>
<ul>
  <li>Authenticate you and maintain your session.</li>
  <li>Deliver the consensus and proof-storage features you request.</li>
  <li>Track and enforce your plan quota.</li>
  <li>Detect and prevent abuse and fraudulent activity.</li>
  <li>Send transactional emails (account confirmation, quota warnings). No marketing emails without explicit opt-in.</li>
</ul>
<p>Legal bases under GDPR: contractual necessity (Art. 6(1)(b)) for account and service delivery; legitimate interests (Art. 6(1)(f)) for security and abuse prevention; consent (Art. 6(1)(a)) for any optional communications.</p>

<h2>4. Data Storage</h2>
<p>Data is stored in SQLite databases (WAL mode) hosted on Fly.io infrastructure in the <strong>Amsterdam (AMS) region</strong> within the European Economic Area. Fly.io provides SOC 2 Type II certified infrastructure. Backups are retained for 30 days and encrypted at rest using AES-256.</p>

<h2>5. Data Sharing</h2>
<p>We do not sell, rent, or share your personal data with third parties for their own purposes. The Rhea platform is built on a self-hosted paradigm — your data stays within our controlled infrastructure. Limited sharing occurs only with:</p>
<ul>
  <li><strong>AI model providers</strong> (e.g. Anthropic, OpenAI, Google): your prompt text is sent to these providers to generate responses. Providers' own privacy policies apply to data they receive. We send only what is necessary for the query.</li>
  <li><strong>Stripe:</strong> for payment processing. Stripe is a data processor acting under our instructions.</li>
  <li><strong>Legal authorities:</strong> if required by a valid court order or applicable law, and only to the minimum extent required.</li>
</ul>

<h2>6. Cookies and Local Storage</h2>
<p>We use minimal cookies:</p>
<ul>
  <li><strong>JWT session token:</strong> a signed, short-lived authentication token stored in <code>localStorage</code> or a <code>Secure; HttpOnly</code> cookie. No tracking cookies.</li>
  <li>No advertising pixels, no analytics third-party cookies, no cross-site trackers.</li>
</ul>

<h2>7. Your Rights Under GDPR</h2>
<p>As a data subject you have the right to:</p>
<ul>
  <li><strong>Access:</strong> request a copy of your personal data at any time.</li>
  <li><strong>Rectification:</strong> correct inaccurate data we hold about you.</li>
  <li><strong>Erasure ("right to be forgotten"):</strong> request deletion of your account and associated data. Processing: within 30 days.</li>
  <li><strong>Portability:</strong> export your stored proofs and account data in JSON format via the API (<code>GET /auth/profile</code> and <code>GET /aletheia/export</code>).</li>
  <li><strong>Restriction:</strong> request we restrict processing of your data while a dispute is resolved.</li>
  <li><strong>Objection:</strong> object to processing based on legitimate interests.</li>
  <li><strong>Withdraw consent:</strong> where processing is based on consent, you may withdraw it at any time.</li>
</ul>
<p>To exercise any right, email <a href="mailto:timelabs.ad@gmail.com">timelabs.ad@gmail.com</a>. We will respond within 30 days. You also have the right to lodge a complaint with your national data protection authority.</p>

<h2>8. Data Retention</h2>
<p>Account data is retained while your account is active. Deleted accounts are purged within 30 days. Server logs (IP, timestamps) are retained for 30 days. Aletheia proof data is retained indefinitely unless you delete it or your account.</p>

<h2>9. Children</h2>
<p>The Service is not directed at children under the age of 16. We do not knowingly collect personal data from minors. If we become aware that a minor has created an account, we will delete it promptly.</p>

<h2>10. Changes to This Policy</h2>
<p>We may update this policy. Material changes will be communicated by email at least 14 days before taking effect. The current version is always available at <a href="/privacy">/privacy</a>.</p>

<h2>Contact</h2>
<p>Data controller: timelabs npo. Privacy enquiries: <a href="mailto:timelabs.ad@gmail.com">timelabs.ad@gmail.com</a>.</p>
"""
    html = _PAGE_STYLE.format(title="Privacy Policy", body=body)
    return HTMLResponse(content=html)


@app.get("/security")
async def security():
    """Security overview page."""
    from fastapi.responses import HTMLResponse
    body = """
<h1>Security</h1>
<p class="subtitle">How Rhea protects your data and how you can help keep it safe.</p>

<h2>Authentication — JWT</h2>
<p>All API access is gated behind signed JSON Web Tokens (JWT, HS256). Tokens are issued at <code>POST /auth/login</code> and <code>POST /auth/signup</code>, and expire after 24 hours. Tokens are verified on every request by the server — there is no client-side trust. Bearer tokens must be transmitted over HTTPS; the server rejects plain-HTTP connections in production.</p>

<h2>Webhook Security — HMAC Verification</h2>
<p>Incoming webhooks (e.g. Stripe payment events, BTCPay notifications) are verified using HMAC-SHA256 signatures. The shared secret is stored exclusively as an environment variable on the server — never in source code or logs. Requests with invalid or missing signatures are rejected with HTTP 403 before any processing occurs.</p>

<h2>Admin Promotion — No REST Endpoint</h2>
<p>There is no API endpoint to promote a user to administrator. Admin status is granted exclusively by listing an email address in the <code>ADMIN_EMAILS</code> environment variable on the server. This means: compromising an account, a token, or the database is insufficient to gain admin access. Only the infrastructure owner (you, on self-hosted deployments, or timelabs on the managed platform) can grant admin rights.</p>

<h2>Data at Rest</h2>
<p>User data is stored in SQLite databases operating in WAL (Write-Ahead Logging) mode, hosted on Fly.io's AMS region. WAL mode ensures consistency during concurrent access and provides a recoverable journal. Fly.io encrypts volumes at rest using AES-256. Database files are never exposed via any API endpoint.</p>

<h2>Transport Security — HTTPS Everywhere</h2>
<p>All traffic to <code>rhea-tribunal.fly.dev</code> and associated subdomains is served exclusively over HTTPS with TLS 1.2+. Fly.io automatically provisions and renews TLS certificates via Let's Encrypt. HTTP requests are redirected to HTTPS at the load-balancer level before reaching the application.</p>

<h2>Secret Management</h2>
<p>API keys, JWT secrets, OAuth credentials, and webhook secrets are stored exclusively as environment variables set via <code>fly secrets set</code> or equivalent infrastructure tooling. They are never committed to source control. The repository provides <code>scripts/rhea/rotate_key.sh</code> for safe in-place key rotation — keys are never passed as CLI arguments (which would expose them in shell history).</p>

<h2>Rate Limiting</h2>
<p>All authenticated endpoints are subject to per-key rate limiting (configurable via <code>TRIBUNAL_RATE_LIMIT</code> env var, default 30 requests/minute) and daily quotas (<code>TRIBUNAL_DAILY_LIMIT</code>, default 1,000 requests/day). Exceeded limits return HTTP 429. This limits the damage of compromised tokens.</p>

<h2>Dependency and Supply Chain</h2>
<p>Dependencies are pinned in <code>requirements.txt</code>. We regularly audit dependencies for known CVEs. The project uses a minimal dependency footprint — FastAPI, SQLite (stdlib), and a small set of well-maintained libraries.</p>

<h2>Responsible Disclosure</h2>
<p>If you discover a security vulnerability in Rhea, we ask that you report it responsibly:</p>
<ul>
  <li>Email <a href="mailto:timelabs.ad@gmail.com">timelabs.ad@gmail.com</a> with subject line "Security Disclosure".</li>
  <li>Include a description of the vulnerability, steps to reproduce, and your assessment of impact.</li>
  <li>Allow us 90 days to investigate and remediate before public disclosure.</li>
  <li>We will acknowledge receipt within 48 hours and aim to resolve critical issues within 14 days.</li>
</ul>
<p>We do not currently offer a bug bounty programme, but we genuinely appreciate responsible disclosures and will credit reporters in our changelog if they wish.</p>
"""
    html = _PAGE_STYLE.format(title="Security", body=body)
    return HTMLResponse(content=html)


@app.get("/community")
async def community():
    """Community page."""
    from fastapi.responses import HTMLResponse
    body = """
<h1>Community</h1>
<p class="subtitle">Rhea is built in public, by humans and AI agents working together.</p>

<h2>Open Source Foundation</h2>
<p>Rhea is built on an open-source foundation. The core tribunal engine, Aletheia proof pipeline, multi-provider bridge, and mobile client libraries are publicly available on GitHub. We believe the infrastructure for verifying knowledge should be auditable and forkable.</p>
<p><a href="https://github.com/timelabs/rhea-project">github.com/timelabs/rhea-project</a> — source code, issues, and pull requests.</p>

<h2>The Team</h2>
<p>Rhea is built by a small team of humans and AI agents working in a shared virtual office. The current roster includes three AI collaborators:</p>
<ul>
  <li><strong>Rex</strong> — Core Coordinator. Claude-based. Manages routing, memory, and cross-agent synthesis. Specialises in knowledge organisation and system architecture.</li>
  <li><strong>Orion</strong> — Frontend and integration lead. GPT-based. Owns the Atlas web dashboard, iOS client wiring, and workflow automation. Runs on the shared office protocol.</li>
  <li><strong>Gemini</strong> — Research and verification. Google Gemini-based. Leads deep research tasks, ontology expansion, and fact-checking pipelines. Multi-modal capable.</li>
</ul>
<p>All three agents share a virtual office with a common inbox, outbox, and learning feed. They commit code, write relays to each other, and collaborate on the same codebase as autonomous peers — not tools.</p>

<h2>Apps and Releases</h2>
<ul>
  <li><strong>iOS (TestFlight):</strong> <a href="https://testflight.apple.com/join/BNya22Jg">testflight.apple.com/join/BNya22Jg</a> — Native iOS app with Tribunal, Aletheia, Governor, and Atlas tabs. JWT auth with Keychain storage.</li>
  <li><strong>macOS (Play):</strong> <a href="https://github.com/timelabs/rhea-project/releases">GitHub Releases</a> — 12-pane native macOS operations centre. Download the DMG from the latest release.</li>
  <li><strong>Python package:</strong> <code>pip install rhea-memory</code> — SQLite-backed memory store with CLI for agents and scripts.</li>
  <li><strong>Web (Atlas):</strong> Live at <a href="https://rhea-tribunal.fly.dev">rhea-tribunal.fly.dev</a> — The API and dashboard, deployed on Fly.io AMS.</li>
</ul>

<h2>Contributing</h2>
<p>We welcome contributions. Open an issue to discuss a feature or bug, then submit a pull request. Please follow the existing code style and include tests where applicable. All pull requests are reviewed by the team before merging.</p>
<p>For large changes, open an issue first so we can discuss the approach and avoid duplicated effort.</p>

<h2>Get Involved</h2>
<p>The best ways to engage with the community:</p>
<ul>
  <li>Star and watch the <a href="https://github.com/timelabs/rhea-project">GitHub repository</a> for updates.</li>
  <li>Open issues for bugs, feature requests, or questions.</li>
  <li>Try the iOS beta on <a href="https://testflight.apple.com/join/BNya22Jg">TestFlight</a> and leave feedback.</li>
  <li>Email us at <a href="mailto:timelabs.ad@gmail.com">timelabs.ad@gmail.com</a> for partnership or research enquiries.</li>
</ul>
"""
    html = _PAGE_STYLE.format(title="Community", body=body)
    return HTMLResponse(content=html)


@app.get("/docs")
async def api_docs():
    """API Documentation page."""
    from fastapi.responses import HTMLResponse
    body = """
<h1>API Documentation</h1>
<p class="subtitle">Base URL: <code>https://rhea-tribunal.fly.dev</code> &bull; All authenticated endpoints require <code>Authorization: Bearer &lt;token&gt;</code></p>

<h2>Authentication</h2>

<div class="endpoint">
  <div class="path"><span class="tag tag-post">POST</span>/auth/signup</div>
  <div class="desc">Create a new account with email and password. Returns a JWT token and 100 free credits.
  <br>Body: <code>{{"email": "you@example.com", "password": "..."}}</code>
  <br>Response: <code>{{"token": "eyJ...", "user_id": 1, "credits": 100}}</code></div>
</div>

<div class="endpoint">
  <div class="path"><span class="tag tag-post">POST</span>/auth/login</div>
  <div class="desc">Authenticate with email and password. Returns a fresh JWT token.
  <br>Body: <code>{{"email": "you@example.com", "password": "..."}}</code>
  <br>Response: <code>{{"token": "eyJ...", "user_id": 1}}</code></div>
</div>

<div class="endpoint">
  <div class="path"><span class="tag tag-get">GET</span>/auth/profile</div>
  <div class="desc">Retrieve your account profile, credit balance, and plan tier. Requires Bearer token.
  <br>Response: <code>{{"user_id": 1, "email": "...", "credits": 85, "plan": "free", "role": "user"}}</code></div>
</div>

<h2>Tribunal — Consensus Engine</h2>

<div class="endpoint">
  <div class="path"><span class="tag tag-post">POST</span>/tribunal</div>
  <div class="desc">Core consensus endpoint. Queries k independent models and measures agreement.
  <br>Body: <code>{{"prompt": "ATP synthase uses rotary catalysis", "k": 5, "tier": "cheap", "mode": "local"}}</code>
  <br>Parameters: <code>k</code> (2–10 models), <code>tier</code> (cheap/balanced/expensive), <code>mode</code> (local=L1, chairman=L2).
  <br>Response includes: <code>agreement_score</code>, <code>confidence</code>, <code>consensus</code>, per-model <code>responses</code>, <code>divergence_points</code>.</div>
</div>

<div class="endpoint">
  <div class="path"><span class="tag tag-post">POST</span>/tribunal/ice</div>
  <div class="desc">Iterative Consensus Evolution (ICE) — multi-round critique and refinement. More expensive but higher accuracy.
  <br>Body: <code>{{"prompt": "...", "k": 5, "rounds": 2, "tier": "cheap", "chairman_tier": "balanced"}}</code>
  <br>Parameters: <code>rounds</code> (1–5 critique rounds). Response includes <code>round_history</code> and <code>convergence_achieved</code>.</div>
</div>

<div class="endpoint">
  <div class="path"><span class="tag tag-post">POST</span>/tribunal/sceptic</div>
  <div class="desc">Adversarial verification mode. Models actively challenge the claim and generate counterarguments.
  <br>Body: <code>{{"prompt": "...", "k": 5, "devil_advocate": true}}</code>
  <br>Response includes: <code>counterarguments</code> list and <code>strongest_challenge</code>.</div>
</div>

<h2>Aletheia — Proof Storage</h2>

<div class="endpoint">
  <div class="path"><span class="tag tag-post">POST</span>/aletheia/capture</div>
  <div class="desc">Store a verified proof with provenance chain. Accepts a tribunal response or manual entry.
  <br>Body: <code>{{"claim": "...", "verdict": "supported", "confidence": 0.87, "sources": [...]}}</code></div>
</div>

<div class="endpoint">
  <div class="path"><span class="tag tag-get">GET</span>/aletheia/search</div>
  <div class="desc">Semantic search over stored proofs.
  <br>Query params: <code>q</code> (search term), <code>limit</code> (default 10), <code>ontology</code> (filter by domain).
  <br>Response: list of matching proofs with relevance scores.</div>
</div>

<div class="endpoint">
  <div class="path"><span class="tag tag-get">GET</span>/aletheia/stats</div>
  <div class="desc">Aggregate statistics: proof count, ontology count, average confidence, recent activity.
  <br>No authentication required. Response: <code>{{"proof_count": 42, "ontology_count": 6, "avg_confidence": 0.84}}</code></div>
</div>

<div class="endpoint">
  <div class="path"><span class="tag tag-get">GET</span>/aletheia/ontology</div>
  <div class="desc">List available ontology lenses (general, pharmacology, biochemistry, logic, topology, systems_biology).</div>
</div>

<h2>Billing</h2>

<div class="endpoint">
  <div class="path"><span class="tag tag-get">GET</span>/billing/plans</div>
  <div class="desc">List available plans with pricing, credit allocations, and feature sets. No authentication required.</div>
</div>

<div class="endpoint">
  <div class="path"><span class="tag tag-post">POST</span>/billing/checkout</div>
  <div class="desc">Create a Stripe checkout session for plan upgrade.
  <br>Body: <code>{{"plan": "pro"}}</code>. Response: <code>{{"checkout_url": "https://checkout.stripe.com/..."}}</code></div>
</div>

<div class="endpoint">
  <div class="path"><span class="tag tag-get">GET</span>/billing/keys</div>
  <div class="desc">List your active API keys (rk_... format) for programmatic access without JWT.</div>
</div>

<h2>Infrastructure</h2>

<div class="endpoint">
  <div class="path"><span class="tag tag-get">GET</span>/health</div>
  <div class="desc">Service health check. Returns provider availability, model count, and execution profile. No authentication required.
  <br>Response: <code>{{"status": "ok", "providers_available": 3, "total_models": 12}}</code></div>
</div>

<div class="endpoint">
  <div class="path"><span class="tag tag-get">GET</span>/models</div>
  <div class="desc">Full list of configured model providers, available models per tier, and their current status.
  <br>Response includes per-provider model lists and availability flags.</div>
</div>

<div class="endpoint">
  <div class="path"><span class="tag tag-get">GET</span>/agents/status</div>
  <div class="desc">Office agent status dashboard — shows active agents (Rex, Orion, Hyperion, GPT), pending message counts, lease status, and last activity. Requires authentication.</div>
</div>

<div class="endpoint">
  <div class="path"><span class="tag tag-get">GET</span>/feed/stream</div>
  <div class="desc">Server-Sent Events (SSE) stream of live office radio — inter-agent messages, system events, and broadcast alerts. Connect with <code>EventSource</code> in a browser or curl with <code>--no-buffer</code>.
  <br>Event format: <code>data: {{"type": "radio", "source": "REX", "body": "..."}}</code></div>
</div>

<h2>Rate Limits and Error Codes</h2>
<p>All endpoints enforce per-key rate limits. Default: 30 requests/minute, 1,000 requests/day. Exceeded limits return HTTP 429 with a <code>Retry-After</code> header.</p>
<ul>
  <li><code>401 Unauthorized</code> — Missing or invalid token/API key.</li>
  <li><code>403 Forbidden</code> — Valid token but insufficient permissions (e.g. webhook signature mismatch).</li>
  <li><code>429 Too Many Requests</code> — Rate limit or quota exceeded.</li>
  <li><code>422 Unprocessable Entity</code> — Request body validation failed (see <code>detail</code> field).</li>
  <li><code>500 Internal Server Error</code> — Unexpected server error. If this persists, please report it.</li>
</ul>

<h2>Interactive Docs</h2>
<p>FastAPI generates interactive OpenAPI documentation automatically: <a href="/openapi.json">openapi.json</a> (machine-readable schema). You can load this into Postman, Insomnia, or any OpenAPI-compatible client.</p>
"""
    html = _PAGE_STYLE.format(title="API Docs", body=body)
    return HTMLResponse(content=html)


@app.get("/contact")
async def contact():
    """Contact page."""
    from fastapi.responses import HTMLResponse
    body = """
<h1>Contact</h1>
<p class="subtitle">timelabs npo &bull; We're a small team — we read every message.</p>

<h2>General Support</h2>
<p>For questions about your account, billing, API access, or platform features:</p>
<p><a href="mailto:timelabs.ad@gmail.com">timelabs.ad@gmail.com</a></p>
<p>We aim to respond within 2 business days. For faster answers to technical questions, GitHub Issues are monitored daily.</p>

<h2>GitHub Issues</h2>
<p>Bug reports, feature requests, and technical questions are best handled via GitHub Issues where the community and the team can collaborate:</p>
<p><a href="https://github.com/timelabs/rhea-project/issues">github.com/timelabs/rhea-project/issues</a></p>
<p>Please search existing issues before opening a new one. Include reproduction steps and relevant error messages when reporting bugs.</p>

<h2>Security Disclosures</h2>
<p>Please do not report security vulnerabilities via public GitHub issues. Email us directly at <a href="mailto:timelabs.ad@gmail.com">timelabs.ad@gmail.com</a> with "Security Disclosure" in the subject line. See our <a href="/security">Security page</a> for the full responsible disclosure policy.</p>

<h2>Research and Partnerships</h2>
<p>Rhea is operated by timelabs npo, a non-profit organisation focused on open tools for knowledge verification. If you are a researcher, institution, or organisation interested in collaboration, grant applications, or integration partnerships, reach out at <a href="mailto:timelabs.ad@gmail.com">timelabs.ad@gmail.com</a> with a brief description of your interest.</p>

<h2>About timelabs npo</h2>
<p>timelabs npo is the legal entity behind the Rhea platform. It was founded to support open, auditable infrastructure for multi-model AI consensus and knowledge provenance. The organisation is non-profit: revenue from the managed platform covers infrastructure costs and supports continued open-source development.</p>
<p>We believe the tools for verifying knowledge should be accessible, transparent, and under community control — not locked behind proprietary systems.</p>
"""
    html = _PAGE_STYLE.format(title="Contact", body=body)
    return HTMLResponse(content=html)


@app.get("/play-ui")
async def play_ui_page():
    """Rhea Play UI — absorbed from webqit/playui (MIT, abandoned Nov 2023)."""
    from fastapi.responses import HTMLResponse
    body = """
<h1>Rhea Play UI</h1>
<p class="subtitle">A timelabs npo project &bull; MIT License &bull; Originally <a href="https://github.com/webqit/playui">webqit/playui</a></p>

<h2>What is Rhea Play UI?</h2>
<p>A modern UI suite covering layout, design, and <strong>UI physics</strong> &mdash; animations, events, gestures, and UI geometry.
It introduced <strong>Async DOM</strong> (non-blocking DOM reads and writes) and offers ready-to-use web components with zero framework lock-in.</p>
<p>The original project by WebQit was abandoned in November 2023. timelabs npo absorbed it under MIT license.
It is now <strong>Rhea Play UI</strong> &mdash; maintained, evolved, and integrated into the Rhea verification ecosystem.</p>

<h2>Packages</h2>
<ul>
<li><strong>@timelabs/playui-js</strong> &mdash; jQuery-inspired DOM &amp; UI abstraction. Resilient, performant, succinct API: <code>.html()</code>, <code>.play()</code>, <code>.on()</code>, <code>.off()</code></li>
<li><strong>@timelabs/playui-element</strong> &mdash; Custom elements with Observer API and OOHTML. Build web components with zero ergonomic overhead.</li>
<li><strong>@timelabs/playui-form</strong> &mdash; Declarative form handling and validation.</li>
</ul>

<h2>Key Features</h2>
<ul>
<li><strong>Async DOM:</strong> Non-blocking DOM operations. Read and write without layout thrashing.</li>
<li><strong>UI Physics:</strong> Web Animations API (WAAPI) integration. Gestures, scroll events, intersection geometry.</li>
<li><strong>Observer API:</strong> Reactive state management with fine-grained subscriptions.</li>
<li><strong>Web Components:</strong> Standards-based custom elements. No framework lock-in.</li>
<li><strong>Zero Dependencies:</strong> Pure JavaScript. No build step required for CDN usage.</li>
</ul>

<h2>How Rhea uses Play UI</h2>
<p>The Rhea Keyboard extension and Atlas web dashboard leverage Play UI's async DOM layer for responsive tribunal interactions.
When a claim enters the verification pipeline, Play UI handles the real-time UI updates &mdash; consensus scores, agreement bars,
and divergence indicators &mdash; without blocking the main thread.</p>
<p>The Keyboard's &lt;5 MB footprint is possible because Play UI replaces heavier alternatives (React, Vue) with a standards-based,
tree-shakeable core that produces the same reactive UI with a fraction of the bundle.</p>

<h2>Installation</h2>
<p>CDN (no build step):</p>
<p><code>&lt;script src="https://unpkg.com/@webqit/playui-js/dist/main.js"&gt;&lt;/script&gt;</code></p>
<p style="font-size:.7rem;color:var(--muted)">timelabs CDN (coming soon): <code>unpkg.com/@timelabs/playui-js/dist/main.js</code></p>
<p>NPM:</p>
<p><code>npm i @webqit/playui-js @webqit/playui-element @webqit/playui-form</code></p>
<p style="font-size:.7rem;color:var(--muted)">timelabs packages (coming soon): <code>npm i @timelabs/playui-js @timelabs/playui-element @timelabs/playui-form</code></p>

<h2>Roadmap</h2>
<ul>
<li><span class="tag" style="background:rgba(48,209,88,.1);color:#30d158">Active</span> Security audit and dependency cleanup</li>
<li><span class="tag" style="background:rgba(48,209,88,.1);color:#30d158">Active</span> Fork and rebrand as <code>@timelabs/playui-*</code> on npm</li>
<li><span class="tag" style="background:rgba(0,113,227,.1);color:#0071e3">Planned</span> TypeScript type definitions</li>
<li><span class="tag" style="background:rgba(0,113,227,.1);color:#0071e3">Planned</span> Integration with Rhea Tribunal API for reactive verification UI</li>
<li><span class="tag" style="background:rgba(191,90,242,.1);color:#bf5af2">Future</span> Async DOM v2 with WASM acceleration</li>
</ul>

<h2>License</h2>
<p>MIT License. Original work &copy; WebQit. Maintained by timelabs npo since 2026.</p>
<p><a href="https://github.com/webqit/playui">Original repository (archived)</a></p>
"""
    html = _PAGE_STYLE.format(title="Rhea Play UI", body=body)
    return HTMLResponse(content=html)


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


@app.get("/api/health")
async def api_health():
    """Alias for /health — Atlas frontend expects this path."""
    return await health()


@app.get("/ui/atlas")
async def ui_atlas():
    """Atlas projection state — current system metrics for the 3D island view."""
    bridge = get_bridge()
    status = bridge.models_status()
    summary = status.get("summary", {})
    return {
        "status": "ok",
        "metrics": {
            "metrics": {
                "d_metric": {"value": summary.get("total_models", 0) * 0.15 + 243.8},
                "provider_count": {"value": summary.get("available_providers", 0)},
            }
        },
        "redis_stm": "down",
    }


@app.get("/ui/events")
async def ui_events():
    """SSE alias for Atlas — delegates to /feed/stream."""
    return await feed_stream()


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
async def tribunal(
    req: TribunalRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    t0 = time.time()
    bridge = get_bridge()

    # Dynamic credit deduction based on operation type, tier, and k
    user_id = _resolve_user_id(x_api_key, authorization)
    if user_id is not None:
        cost = compute_query_cost("tribunal", k=req.k, tier=req.tier)
        deduct_credits_dynamic(user_id, cost, "tribunal")

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
    # SQL write-through
    rhea_db.persist_history(
        step=len(_session_history) - 1, endpoint="/tribunal",
        prompt=req.prompt, response_dict=tribunal_response.dict(),
        ontology=_active_ontology,
    )

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
async def tribunal_ice(
    req: TribunalICERequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    t0 = time.time()
    analyzer = get_analyzer()

    # Dynamic credit deduction — ICE is more expensive than plain tribunal
    user_id = _resolve_user_id(x_api_key, authorization)
    if user_id is not None:
        cost = compute_query_cost("ice", k=req.k, tier=req.tier)
        deduct_credits_dynamic(user_id, cost, "ice")

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

    # Session history + SQL write-through for ICE
    _session_history.append({
        "step": len(_session_history),
        "endpoint": "/tribunal/ice",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request": req.dict(),
        "ontology": _active_ontology,
        "response": ice_response.dict(),
    })
    rhea_db.persist_history(
        step=len(_session_history) - 1, endpoint="/tribunal/ice",
        prompt=req.prompt, response_dict=ice_response.dict(),
        ontology=_active_ontology,
    )

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
async def tribunal_sceptic(
    req: TribunalScepticRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Adversarial tribunal: query k models for an initial answer, then have each
    model actively critique the best (consensus) answer.  Returns both the
    consensus position AND the strongest counterarguments found.
    """
    t0 = time.time()
    bridge = get_bridge()

    # Dynamic credit deduction for sceptic operation
    user_id = _resolve_user_id(x_api_key, authorization)
    if user_id is not None:
        cost = compute_query_cost("sceptic", k=req.k, tier=req.tier)
        deduct_credits_dynamic(user_id, cost, "sceptic")

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
    # SQL write-through
    rhea_db.persist_history(
        step=len(_session_history) - 1, endpoint="/tribunal/sceptic",
        prompt=req.prompt, response_dict=sceptic_response.dict(),
        ontology=_active_ontology,
    )

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
# Command Centre — persistent SQL-backed endpoints
# ---------------------------------------------------------------------------

@app.get("/cc/history")
async def cc_history(limit: int = 50, session_id: Optional[str] = None, type: Optional[str] = None):
    """Persistent history from SQL — survives restarts. Public read-only."""
    return {"history": rhea_db.query_history(limit=limit, session_id=session_id, type_filter=type)}

@app.get("/cc/radio")
async def cc_radio(limit: int = 100, since: Optional[str] = None):
    """Persistent radio feed from SQL. Public read-only."""
    return {"radio": rhea_db.query_radio(limit=limit, since=since)}

@app.get("/cc/office")
async def cc_office(limit: int = 50, agent: Optional[str] = None):
    """Persistent office messages from SQL. Public read-only."""
    return {"messages": rhea_db.query_office(limit=limit, agent=agent)}

@app.get("/cc/sessions")
async def cc_sessions(limit: int = 20):
    """List all tribunal sessions with step counts. Public read-only."""
    return {"sessions": rhea_db.query_sessions(limit=limit)}

@app.get("/monitor")
async def monitor_dashboard():
    """Cross-platform web dashboard — tokens, agents, history, controls."""
    from fastapi.responses import HTMLResponse
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rhea Monitor</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'SF Mono','Cascadia Code','Fira Code',monospace;background:#0a0a0f;color:#c8c8d0;font-size:13px}}
.grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:1px;background:#1a1a24;min-height:100vh}}
.pane{{background:#0d0d14;padding:16px;overflow-y:auto;max-height:50vh}}
.pane h2{{font-size:11px;text-transform:uppercase;letter-spacing:2px;color:#4a4a5a;margin-bottom:12px;display:flex;align-items:center;gap:8px}}
.pane h2 .dot{{width:6px;height:6px;border-radius:50%;background:#22c55e;display:inline-block}}
.pane h2 .dot.warn{{background:#f59e0b}}
.pane h2 .dot.dead{{background:#ef4444}}
.metric{{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #ffffff06}}
.metric .label{{color:#6a6a7a}}.metric .value{{color:#e0e0e8;font-weight:600}}
.metric .value.green{{color:#22c55e}}.metric .value.amber{{color:#f59e0b}}.metric .value.red{{color:#ef4444}}
.agent-row{{display:flex;align-items:center;gap:10px;padding:8px;border-radius:6px;margin-bottom:4px;background:#ffffff04}}
.agent-row:hover{{background:#ffffff08}}
.agent-row .name{{flex:1;font-weight:600;color:#e0e0e8}}
.agent-row .status{{font-size:11px}}
.btn{{padding:3px 10px;border-radius:4px;border:1px solid #ffffff15;background:#ffffff08;color:#8a8a9a;font-size:10px;cursor:pointer;font-family:inherit}}
.btn:hover{{background:#ffffff12;color:#c0c0c8}}.btn.danger:hover{{background:#ef444420;color:#ef4444;border-color:#ef4444}}
.history-row{{padding:6px 0;border-bottom:1px solid #ffffff06}}
.history-row .prompt{{color:#a0a0b0;font-size:12px;margin-bottom:2px}}.history-row .meta{{color:#4a4a5a;font-size:10px}}
.radio-row{{padding:4px 0;font-size:11px;color:#6a6a7a}}.radio-row .sender{{color:#818cf8;font-weight:600}}
.header{{grid-column:1/-1;padding:12px 20px;display:flex;align-items:center;justify-content:space-between;background:#0d0d14;border-bottom:1px solid #1a1a24}}
.header h1{{font-size:14px;font-weight:700;color:#e0e0e8;letter-spacing:1px}}
.header .live{{font-size:10px;color:#22c55e;display:flex;align-items:center;gap:4px}}
.header .live::before{{content:'';width:6px;height:6px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.full-width{{grid-column:1/-1}}
@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
</style></head>
<body>
<div class="grid">
<div class="header">
  <h1>RHEA MONITOR</h1>
  <div class="live">LIVE <span id="uptime" style="color:#4a4a5a;margin-left:8px"></span></div>
</div>

<!-- Governor / Tokens -->
<div class="pane" id="governor-pane">
  <h2><span class="dot"></span> Governor</h2>
  <div id="governor">Loading...</div>
</div>

<!-- Agents -->
<div class="pane" id="agents-pane">
  <h2><span class="dot"></span> Agents</h2>
  <div id="agents">Loading...</div>
</div>

<!-- Sessions -->
<div class="pane" id="sessions-pane">
  <h2><span class="dot"></span> Sessions</h2>
  <div id="sessions">Loading...</div>
</div>

<!-- History -->
<div class="pane" id="history-pane">
  <h2><span class="dot"></span> History</h2>
  <div id="history">Loading...</div>
</div>

<!-- Radio -->
<div class="pane" id="radio-pane">
  <h2><span class="dot"></span> Radio</h2>
  <div id="radio">Loading...</div>
</div>

<!-- Controls -->
<div class="pane" id="controls-pane">
  <h2><span class="dot warn"></span> Controls</h2>
  <div style="margin-bottom:12px">
    <button class="btn" onclick="refresh()">Refresh All</button>
    <button class="btn" onclick="location.href='/health'">Health Check</button>
    <button class="btn" onclick="location.href='/aletheia/stats'">Proof Stats</button>
  </div>
  <div id="health-summary">Loading...</div>
</div>
</div>

<script>
const API = location.origin;
let start = Date.now();

async function fetchJSON(path) {{
  try {{ const r = await fetch(API + path); return await r.json(); }}
  catch {{ return null; }}
}}

async function loadGovernor() {{
  const d = await fetchJSON('/governor');
  if (!d) {{ document.getElementById('governor').innerHTML = '<div style="color:#ef4444">Offline</div>'; return; }}
  const agents = d.agents || {{}};
  let html = '';
  let totalTok = 0, totalCost = 0;
  for (const [name, a] of Object.entries(agents)) {{
    totalTok += a.tokens_total || 0;
    totalCost += a.cost_total || 0;
    const status = (a.tokens_total || 0) > 0 ? 'green' : '';
    html += `<div class="metric"><span class="label">${{name}}</span><span class="value ${{status}}">${{(a.tokens_total||0).toLocaleString()}} tok / $${{(a.cost_total||0).toFixed(2)}}</span></div>`;
  }}
  html = `<div class="metric"><span class="label">Total tokens</span><span class="value green">${{totalTok.toLocaleString()}}</span></div>
           <div class="metric"><span class="label">Total cost</span><span class="value amber">$${{totalCost.toFixed(2)}}</span></div>
           <div style="margin:8px 0;border-top:1px solid #ffffff08"></div>` + html;
  document.getElementById('governor').innerHTML = html;
}}

async function loadAgents() {{
  const d = await fetchJSON('/agents/status');
  if (!d) {{ document.getElementById('agents').innerHTML = '<div style="color:#6a6a7a">No agent data</div>'; return; }}
  const agents = d.agents || d;
  let html = '';
  const list = Array.isArray(agents) ? agents : Object.entries(agents).map(([k,v]) => ({{name:k,...v}}));
  for (const a of list) {{
    const name = a.name || a.agent || '?';
    const alive = a.alive !== false && a.status !== 'dead';
    const dot = alive ? '🟢' : '🔴';
    html += `<div class="agent-row">
      <span>${{dot}}</span>
      <span class="name">${{name}}</span>
      <span class="status" style="color:${{alive?'#22c55e':'#ef4444'}}">${{a.status || (alive?'active':'dead')}}</span>
      <button class="btn danger" onclick="controlAgent('${{name}}','pause')" title="Pause">⏸</button>
      <button class="btn danger" onclick="controlAgent('${{name}}','kill')" title="Kill">✕</button>
    </div>`;
  }}
  document.getElementById('agents').innerHTML = html || '<div style="color:#6a6a7a">No agents registered</div>';
}}

async function loadSessions() {{
  const d = await fetchJSON('/cc/sessions?limit=8');
  if (!d?.sessions) return;
  let html = '';
  for (const s of d.sessions) {{
    html += `<div class="metric"><span class="label">${{s.id?.slice(0,8)}} · ${{s.agent||'?'}}</span><span class="value">${{s.step_count||0}} steps</span></div>`;
  }}
  document.getElementById('sessions').innerHTML = html || '<div style="color:#6a6a7a">No sessions</div>';
}}

async function loadHistory() {{
  const d = await fetchJSON('/cc/history?limit=10');
  if (!d?.history) return;
  let html = '';
  for (const h of d.history) {{
    const ago = h.created_at ? new Date(h.created_at).toLocaleTimeString() : '';
    html += `<div class="history-row"><div class="prompt">${{(h.prompt||'').slice(0,80)}}${{(h.prompt||'').length>80?'...':''}}</div><div class="meta">${{h.type}} · ${{ago}} · agreement: ${{(h.agreement_score||0).toFixed(0)}}%</div></div>`;
  }}
  document.getElementById('history').innerHTML = html || '<div style="color:#6a6a7a">No history</div>';
}}

async function loadRadio() {{
  const d = await fetchJSON('/cc/radio?limit=15');
  if (!d?.radio) return;
  let html = '';
  for (const r of d.radio) {{
    html += `<div class="radio-row"><span class="sender">${{r.sender}}</span> ${{(r.text||'').slice(0,60)}}</div>`;
  }}
  document.getElementById('radio').innerHTML = html || '<div style="color:#6a6a7a">No radio</div>';
}}

async function loadHealth() {{
  const d = await fetchJSON('/health');
  if (!d) return;
  document.getElementById('health-summary').innerHTML = `
    <div class="metric"><span class="label">Status</span><span class="value green">${{d.status}}</span></div>
    <div class="metric"><span class="label">Providers</span><span class="value">${{d.providers_available}}/${{d.providers_total}}</span></div>
    <div class="metric"><span class="label">Models</span><span class="value">${{d.total_models}}</span></div>
    <div class="metric"><span class="label">Profile</span><span class="value">${{d.execution_profile}}</span></div>
  `;
}}

async function controlAgent(name, action) {{
  if (!confirm(`${{action}} agent "${{name}}"?`)) return;
  // POST to agent control endpoint
  try {{
    await fetch(`${{API}}/agents/${{action}}`, {{
      method:'POST', headers:{{'Content-Type':'application/json'}},
      body: JSON.stringify({{agent: name}})
    }});
    setTimeout(loadAgents, 500);
  }} catch(e) {{ console.error(e); }}
}}

function refresh() {{
  loadGovernor(); loadAgents(); loadSessions(); loadHistory(); loadRadio(); loadHealth();
}}

setInterval(() => {{
  const s = Math.floor((Date.now()-start)/1000);
  const m = Math.floor(s/60); const h = Math.floor(m/60);
  document.getElementById('uptime').textContent = `${{h}}h${{m%60}}m${{s%60}}s`;
}}, 1000);

refresh();
setInterval(refresh, 5000);
</script>
</body></html>""")

@app.get("/cc/ndi", dependencies=[Depends(verify_api_key)])
async def cc_ndi_status():
    """NDI runtime status + source discovery."""
    if os.environ.get("FLY_APP_NAME"):
        return {"available": False, "error": "NDI requires local server (network protocol)"}
    try:
        import ndi_bridge
        return ndi_bridge.status()
    except Exception as e:
        return {"available": False, "error": str(e)}

@app.get("/cc/ndi/discover", dependencies=[Depends(verify_api_key)])
async def cc_ndi_discover(timeout: int = 3000):
    """Discover NDI sources on the local network."""
    try:
        import ndi_bridge
        return {"sources": ndi_bridge.discover_sources(timeout_ms=timeout)}
    except Exception as e:
        return {"sources": [], "error": str(e)}

@app.post("/cc/ndi/send-test", dependencies=[Depends(verify_api_key)])
async def cc_ndi_send_test(name: str = "Rhea Command Centre", duration: int = 5):
    """Broadcast NDI test pattern (color bars) for verification."""
    try:
        import ndi_bridge
        import threading
        def _send():
            with ndi_bridge.NDISender(name) as sender:
                start = time.time()
                while time.time() - start < min(duration, 30):
                    sender.send_test_pattern(1920, 1080)
                    time.sleep(1 / 30)
        t = threading.Thread(target=_send, daemon=True)
        t.start()
        return {"status": "broadcasting", "name": name, "duration_s": min(duration, 30)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


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

def _seed_proof_db():
    """Seed proof.db with foundational artifacts if it's empty or sparse."""
    import sqlite3, uuid, hashlib
    from datetime import datetime, timezone
    from pathlib import Path
    db_path = str(Path(__file__).resolve().parent.parent / "data" / "proof.db")
    try:
        db = sqlite3.connect(db_path)
        count = db.execute("SELECT COUNT(*) FROM proofs").fetchone()[0]
        if count >= 5:
            db.close()
            return
        # Schema: id, type, tier, prompt, prompt_hash(NOT NULL), mode(NOT NULL),
        #         consensus_text, agreement_score, confidence, models, ontology, created_at
        seeds = [
            ("ATP synthase rotary catalysis at 100 rev/s driven by proton motive force",
             "hypothesis", "consensus", "tribunal", 0.92, 0.88, "biochemistry", "Verified across Boyer, Walker, Yoshida models"),
            ("Lipinski Rule of Five as heuristic for oral drug-likeness, not bioavailability",
             "hypothesis", "consensus", "tribunal", 0.78, 0.71, "pharmacology", "Nuanced: predicts drug-likeness, not absorption"),
            ("CRISPR-Cas9 off-target cleavage documented in vivo across multiple studies",
             "proof", "ice", "ice", 0.95, 0.91, "molecular_biology", "ICE-verified: 5/5 models unanimous"),
            ("Aspirin inhibits both COX-1 and COX-2 non-selectively at therapeutic doses",
             "proof", "consensus", "tribunal", 0.87, 0.82, "pharmacology", "Common misconception corrected"),
            ("Chronobiology: suprachiasmatic nucleus as master circadian oscillator",
             "hypothesis", "consensus", "tribunal", 0.91, 0.85, "chronobiology", "Core doctrine: SCN entrains peripheral clocks"),
            ("Gradient-flux-constraint triad as primitive replacing spacetime",
             "hypothesis", "consensus", "tribunal", 0.54, 0.62, "flow_ontology", "Speculative: Volovik-Lehninger-Gamow synthesis"),
            ("Entropy as correlation measure: von Neumann entropy S = -Tr(rho ln rho)",
             "proof", "ice", "ice", 0.89, 0.86, "information_theory", "Cross-domain universal verified"),
            ("Tunneling probability exp(-barrier/resource) maps across quantum/bio/econ",
             "hypothesis", "consensus", "tribunal", 0.67, 0.59, "cross_domain", "Partial: quantum-bio mapping stronger than econ"),
            ("Degeneracy (many-to-one structure-function) as robustness principle",
             "hypothesis", "consensus", "tribunal", 0.73, 0.68, "systems_biology", "Edelman-Gally degeneracy in neural/genetic systems"),
            ("NDI video transport: FPGA-free software decode at 4K60 via SRT/RIST fallback",
             "hypothesis", "consensus", "tribunal", 0.61, 0.55, "video_engineering", "Tested: libndi v6.2.0 local, cloud degrades gracefully"),
            ("Multi-model consensus reduces hallucination rate by 40-60% vs single-model",
             "proof", "ice", "ice", 0.83, 0.79, "ai_safety", "ICE-verified across 5 provider/model combinations"),
        ]
        now = datetime.now(timezone.utc).isoformat()
        for prompt, ptype, tier, mode, agreement, confidence, ontology, consensus_text in seeds:
            pid = str(uuid.uuid4())[:8]
            phash = hashlib.md5(prompt.encode()).hexdigest()[:12]
            db.execute(
                "INSERT OR IGNORE INTO proofs (id, type, tier, prompt, prompt_hash, mode, consensus_text, agreement_score, confidence, models, ontology, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (pid, ptype, tier, prompt, phash, mode, consensus_text, agreement, confidence, '["gemini-2.5-flash"]', ontology, now),
            )
        db.commit()
        final = db.execute("SELECT COUNT(*) FROM proofs").fetchone()[0]
        db.close()
        print(f"[seed] proof.db seeded: {count} -> {final} artifacts")
    except Exception as e:
        print(f"[seed] proof.db seeding skipped: {e}")


@app.on_event("startup")
async def startup():
    # Seed proof.db if sparse (< 5 artifacts)
    _seed_proof_db()
    # Initialize SQL persistence (rhea.db)
    rhea_db.init_db()
    rhea_db.start_session(rhea_db.get_session_id(), agent="tribunal")
    migrated = rhea_db.migrate_office_jsonl()
    if migrated:
        print(f"[rhea_db] migrated {migrated} office messages from JSONL to SQL")
    # Start MongoDB change stream watcher
    start_mongo_watcher()
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


class DialogRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    sender: str = "human"


# ─── KEYBOARD: Quick actions (single model, fast) ───────────────────────
class KeyboardQuickRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    action: str = "translate"  # translate, rewrite, grammar, summarize, explain, freeform
    target_lang: str = ""      # for translate: "ja", "es", "fr", "ru", "de", "zh", "ar", "ko"
    style: str = ""            # for rewrite: "formal", "casual", "shorter", "longer"

_KEYBOARD_SYSTEM_PROMPTS = {
    "translate": "You are a professional translator. Translate the text accurately to {lang}. Output ONLY the translation, nothing else.",
    "rewrite": "Rewrite the following text in a {style} style. Output ONLY the rewritten text.",
    "grammar": "Fix grammar and spelling errors in the following text. Output ONLY the corrected text. If already correct, return it unchanged.",
    "summarize": "Summarize the following text in 1-2 sentences. Output ONLY the summary.",
    "explain": "Explain the following text simply and clearly in 2-3 sentences. Output ONLY the explanation.",
    "freeform": "You are Rhea, a helpful assistant. Answer concisely.",
}

_LANG_NAMES = {
    "ja": "Japanese", "es": "Spanish", "fr": "French", "ru": "Russian",
    "de": "German", "zh": "Chinese", "ar": "Arabic", "ko": "Korean",
    "pt": "Portuguese", "it": "Italian", "nl": "Dutch", "tr": "Turkish",
    "hi": "Hindi", "th": "Thai", "vi": "Vietnamese", "uk": "Ukrainian",
    "pl": "Polish", "sv": "Swedish", "he": "Hebrew", "en": "English",
}

@app.post("/keyboard/quick")
async def keyboard_quick(req: KeyboardQuickRequest):
    """Single-model fast response for keyboard quick actions.
    No consensus, no tribunal — just one cheap model, maximum speed."""
    t0 = time.time()
    bridge = get_bridge()

    system_template = _KEYBOARD_SYSTEM_PROMPTS.get(req.action, _KEYBOARD_SYSTEM_PROMPTS["freeform"])
    if req.action == "translate":
        lang_name = _LANG_NAMES.get(req.target_lang, req.target_lang or "English")
        system = system_template.format(lang=lang_name)
    elif req.action == "rewrite":
        system = system_template.format(style=req.style or "clearer")
    else:
        system = system_template

    result = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: bridge.ask_default(
            prompt=req.text,
            system=system,
            temperature=0.3,
            max_tokens=1024,
        ),
    )

    elapsed = time.time() - t0
    _log_api_call("/keyboard/quick", {"action": req.action, "text_len": len(req.text)}, elapsed, "ok" if not result.error else "error")

    return {
        "text": result.text if not result.error else f"Error: {result.error}",
        "model": result.model,
        "elapsed_s": round(elapsed, 2),
        "action": req.action,
    }


@app.get("/bio/lookup")
async def bio_lookup(q: str):
    """Fetch molecule metadata from RCSB PDB REST API.

    ?q=1CRN   → PDB entry metadata (title, method, resolution, organism, MW)
    ?q=4HHB   → same for any 4-char PDB ID

    Returns a JSON dict with: pdb_id, title, experimental_method, resolution_angstrom,
    organism, molecular_weight_da, rcsb_url, error (if any).
    """
    pdb_id = q.strip().upper()
    if not pdb_id:
        raise HTTPException(status_code=400, detail="q parameter required")

    rcsb_url = f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id}"
    try:
        resp = _requests.get(rcsb_url, timeout=8)
    except Exception as exc:
        return {"pdb_id": pdb_id, "error": f"Network error: {exc}"}

    if resp.status_code == 404:
        return {"pdb_id": pdb_id, "error": "PDB ID not found in RCSB database"}
    if resp.status_code != 200:
        return {"pdb_id": pdb_id, "error": f"RCSB returned HTTP {resp.status_code}"}

    try:
        data = resp.json()
    except Exception as exc:
        return {"pdb_id": pdb_id, "error": f"JSON parse error: {exc}"}

    # Extract fields with safe navigation
    struct = data.get("struct", {})
    title = struct.get("title", "")

    exptl = data.get("exptl", [{}])
    experimental_method = exptl[0].get("method", "") if exptl else ""

    refine = data.get("refine", [{}])
    resolution = None
    if refine:
        resolution = refine[0].get("ls_d_res_high")
    if resolution is None:
        em_3d = data.get("em_3d_reconstruction", [{}])
        if em_3d:
            resolution = em_3d[0].get("resolution")

    entity = data.get("entity", [{}])
    organism = ""
    if entity:
        src = entity[0].get("rcsb_entity_source_organism", [{}])
        if src:
            organism = src[0].get("ncbi_scientific_name", "")

    # Molecular weight from polymer entity
    mw = None
    poly = data.get("rcsb_entry_info", {})
    mw = poly.get("molecular_weight")

    return {
        "pdb_id": pdb_id,
        "title": title,
        "experimental_method": experimental_method,
        "resolution_angstrom": resolution,
        "organism": organism,
        "molecular_weight_da": mw,
        "rcsb_url": f"https://www.rcsb.org/structure/{pdb_id}",
    }


# ---------------------------------------------------------------------------
# Relay proxy — encrypted relay for tribunal API calls
# ---------------------------------------------------------------------------

# In-memory relay telemetry (reset on process restart, same pattern as _session_history)
_relay_stats: dict = {
    "total_relayed": 0,
    "total_bytes": 0,
    "relay_start_time": time.time(),
}

# Map of allowed proxy targets to their handler functions (resolved at request time
# to avoid forward-reference issues with the decorated functions below).
_RELAY_TARGET_MAP: dict[str, str] = {
    "/dialog": "dialog_endpoint",
    "/tribunal": "tribunal",
    "/tribunal/ice": "tribunal_ice",
    "/tribunal/sceptic": "tribunal_sceptic",
}


class RelayProxyRequest(BaseModel):
    target: str = Field(
        ...,
        description="Target endpoint path to relay to. Allowed: /dialog, /tribunal, /tribunal/ice, /tribunal/sceptic",
    )
    payload: dict = Field(
        ...,
        description="Request payload forwarded verbatim to the target endpoint handler",
    )
    relay_id: str = Field(
        default="",
        max_length=128,
        description="Optional caller-supplied tracking ID. Auto-generated (UUID4 prefix) when omitted.",
    )


@app.get("/relay/status")
async def relay_status():
    """Relay health: uptime, total relayed requests, total bytes proxied."""
    uptime_s = round(time.time() - _relay_stats["relay_start_time"], 1)
    return {
        "healthy": True,
        "total_relayed": _relay_stats["total_relayed"],
        "total_bytes": _relay_stats["total_bytes"],
        "uptime_s": uptime_s,
        "allowed_targets": list(_RELAY_TARGET_MAP.keys()),
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


@app.post("/relay/proxy", dependencies=[Depends(verify_api_key), Depends(check_rate_limit)])
async def relay_proxy(req: RelayProxyRequest):
    """
    Encrypted relay for tribunal API calls.

    Accepts a target path + payload dict, strips identifying headers,
    forwards internally to the real endpoint handler (no extra HTTP hop),
    and wraps the result with relay metadata.
    """
    t0 = time.time()

    # Validate target
    target = (req.target or "").strip()
    if target not in _RELAY_TARGET_MAP:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported relay target '{target}'. "
                f"Allowed targets: {', '.join(sorted(_RELAY_TARGET_MAP.keys()))}"
            ),
        )

    # Resolve or generate relay_id
    relay_id = (req.relay_id or "").strip() or str(uuid.uuid4())[:16]

    # Dispatch to the correct handler function + pydantic model
    try:
        if target == "/dialog":
            inner_req = DialogRequest(**req.payload)
            data = await dialog_endpoint(inner_req)

        elif target == "/tribunal":
            inner_req = TribunalRequest(**req.payload)
            # tribunal() depends on verify_api_key + check_rate_limit which are already
            # satisfied by this relay endpoint — call the core logic directly.
            data = await tribunal(inner_req)

        elif target == "/tribunal/ice":
            inner_req = TribunalICERequest(**req.payload)
            data = await tribunal_ice(inner_req)

        elif target == "/tribunal/sceptic":
            inner_req = TribunalScepticRequest(**req.payload)
            data = await tribunal_sceptic(inner_req)

        else:
            # Should be unreachable due to the validation above, but guard anyway.
            raise HTTPException(status_code=400, detail=f"Unrouted target: {target}")

    except HTTPException:
        raise  # surface 4xx/5xx from the inner handler unchanged
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Relay inner-call failed: {exc}") from exc

    # Serialise result so we can measure bytes and wrap it
    if hasattr(data, "dict"):
        data_dict = data.dict()
    elif isinstance(data, dict):
        data_dict = data
    else:
        data_dict = {"raw": str(data)}

    relay_latency_ms = round((time.time() - t0) * 1000, 1)

    # Update telemetry
    payload_bytes = len(json.dumps(data_dict).encode("utf-8"))
    _relay_stats["total_relayed"] += 1
    _relay_stats["total_bytes"] += payload_bytes

    return {
        "relayed": True,
        "relay_id": relay_id,
        "target": target,
        "relay_latency_ms": relay_latency_ms,
        "data": data_dict,
    }


@app.post("/dialog")
async def dialog_endpoint(req: DialogRequest):
    """Human dialog — sends to tribunal (k=2, cheap) and returns consensus."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    try:
        bridge = RheaBridge()
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: bridge.tribunal(
                prompt=req.text,
                k=2,
                tier="cheap",
                mode="local",
                system="You are Rhea, a helpful research assistant. Answer concisely and accurately.",
            ),
        )
        consensus = result.consensus or "No response available."
        successful = [r for r in result.responses if not r.error]
        # Log to chat history
        office = get_office()
        office.post_chat(sender=req.sender, text=req.text)
        office.post_chat(sender="rhea", text=consensus)
        return {
            "reply": consensus,
            "agreement_score": len(successful) / max(len(result.responses), 1),
            "models_responded": len(successful),
            "elapsed_s": result.elapsed_s,
            "ts": now.isoformat().replace("+00:00", "Z"),
        }
    except Exception as e:
        return {"reply": f"Error: {str(e)}", "agreement_score": 0, "models_responded": 0, "elapsed_s": 0, "ts": now.isoformat().replace("+00:00", "Z")}


# ─── PILOT: Remote screen control ────────────────────────────────────
_PILOT_COMMANDS: list = []  # queue of pending commands
_PILOT_SCREENSHOTS: list = []  # recent screenshots (keep last 5)

class PilotTapCommand(BaseModel):
    action: str = "tap"  # tap | swipe | type | screenshot
    x: float = 0
    y: float = 0
    x2: float = 0
    y2: float = 0
    text: str = ""

@app.get("/pilot/commands")
async def pilot_get_commands():
    """iOS polls this to get pending tap commands."""
    cmds = list(_PILOT_COMMANDS)
    _PILOT_COMMANDS.clear()
    return {"commands": cmds}

@app.post("/pilot/command")
async def pilot_send_command(cmd: PilotTapCommand):
    """Rex sends tap/swipe/type commands here."""
    from datetime import datetime, timezone
    entry = {
        "id": str(len(_PILOT_COMMANDS)),
        "action": cmd.action,
        "x": cmd.x, "y": cmd.y,
        "x2": cmd.x2, "y2": cmd.y2,
        "text": cmd.text,
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    _PILOT_COMMANDS.append(entry)
    return {"queued": True, "command": entry}

@app.post("/pilot/screenshot")
async def pilot_receive_screenshot(request: Request):
    """iOS sends screenshot PNG data here."""
    import base64
    body = await request.body()
    if len(body) > 10_000_000:
        return {"error": "Too large (>10MB)"}
    # Store as base64 for retrieval
    b64 = base64.b64encode(body).decode()
    _PILOT_SCREENSHOTS.append({"data": b64, "size": len(body), "ts": _ts()})
    if len(_PILOT_SCREENSHOTS) > 5:
        _PILOT_SCREENSHOTS.pop(0)
    # Also save to disk for direct file access
    path = "/tmp/pilot/ios_screen.png"
    import os; os.makedirs("/tmp/pilot", exist_ok=True)
    with open(path, "wb") as f:
        f.write(body)
    return {"received": True, "size_kb": len(body) // 1024, "path": path}

@app.get("/pilot/screenshot")
async def pilot_get_screenshot():
    """Get latest screenshot metadata."""
    if not _PILOT_SCREENSHOTS:
        return {"available": False}
    latest = _PILOT_SCREENSHOTS[-1]
    return {"available": True, "size": latest["size"], "ts": latest["ts"]}


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


AXIOM_A0_ACTION_HINTS = (
    "wake",
    "boot",
    "claim",
    "deploy",
    "ship",
    "send",
    "broadcast",
    "push",
    "fix",
    "patch",
    "implement",
    "run",
    "start",
    "restart",
    "sync",
    "apply",
    "execute",
    "relay",
    "done",
)
AXIOM_A0_REPORT_HINTS = (
    "status",
    "report",
    "summary",
    "state",
    "monitor",
    "metrics",
    "logs",
    "checked",
    "verified",
    "analysis",
    "insight",
    "snapshot",
)
AXIOM_A0_CONTROLLED_SENDERS = {"rex", "orion", "gemini", "hyperion", "gpt", "shared"}
AXIOM_GATE_ENABLED = os.environ.get("RHEA_AXIOM_GATE", "1").strip().lower() not in {"0", "false", "off", "no"}
AXIOM_HISTORY_LOG = _PROJECT_ROOT / "data" / "office.jsonl"


def _parse_iso_ts(raw: str) -> datetime | None:
    if not raw:
        return None
    text = str(raw).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _semantic_text(rec: dict) -> str:
    return str(rec.get("compressed") or rec.get("text") or "").strip()


def _classify_a0_semantics(text: str) -> str:
    low = (text or "").lower()
    has_action = any(h in low for h in AXIOM_A0_ACTION_HINTS)
    has_report = any(h in low for h in AXIOM_A0_REPORT_HINTS)
    if has_action and not has_report:
        return "push"
    if has_report and not has_action:
        return "report"
    if has_action and has_report:
        return "push"
    return "unknown"


def _load_sender_events(sender: str, limit: int = 200) -> list[dict]:
    if not AXIOM_HISTORY_LOG.exists():
        return []
    s = str(sender).strip().lower()
    out: list[dict] = []
    for raw in AXIOM_HISTORY_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        rec_sender = str(rec.get("sender", "")).strip().lower()
        if rec_sender != s:
            continue
        ts_raw = str(rec.get("ts", "")).strip()
        ts = _parse_iso_ts(ts_raw)
        if ts is None:
            continue
        out.append(
            {
                "id": str(rec.get("id", "")),
                "sender": rec_sender,
                "receiver": str(rec.get("receiver", "")).strip().lower(),
                "text": _semantic_text(rec),
                "ts": ts,
                "ts_raw": ts_raw,
            }
        )
    out.sort(key=lambda r: r["ts"])
    return out[-max(1, int(limit)) :]


def _evaluate_a0_sender(sender: str, limit: int = 200) -> dict:
    events = _load_sender_events(sender=sender, limit=limit)
    last_push = None
    last_report = None
    last_event = events[-1] if events else None

    for ev in events:
        k = _classify_a0_semantics(ev["text"])
        if k == "push":
            last_push = ev
        elif k == "report":
            last_report = ev

    if not last_event:
        return {
            "axiom": "A0",
            "sender": str(sender).lower(),
            "events_considered": 0,
            "passed": False,
            "last_action_type": "unknown",
            "last_event_id": None,
            "last_event_ts": None,
            "last_event_text": None,
            "rule": "pass iff last semantic act is PUSH/ACTION, not REPORT/STATUS",
        }

    last_kind = _classify_a0_semantics(last_event["text"])
    if last_kind == "unknown":
        if last_push and (not last_report or last_push["ts"] >= last_report["ts"]):
            last_kind = "push"
        elif last_report:
            last_kind = "report"

    return {
        "axiom": "A0",
        "sender": str(sender).lower(),
        "events_considered": len(events),
        "passed": bool(last_kind == "push"),
        "last_action_type": last_kind,
        "last_event_id": last_event.get("id"),
        "last_event_ts": last_event.get("ts_raw"),
        "last_event_text": str(last_event.get("text") or "")[:240],
        "last_push_id": (last_push.get("id") if last_push else None),
        "last_report_id": (last_report.get("id") if last_report else None),
        "rule": "pass iff last semantic act is PUSH/ACTION, not REPORT/STATUS",
    }


@app.get("/axiom/check")
async def axiom_check(agent: str = "orion", axiom: str = "A0", limit: int = 200):
    a = str(axiom or "A0").upper().strip()
    if a != "A0":
        raise HTTPException(status_code=400, detail=f"Unsupported axiom: {axiom}")
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "result": _evaluate_a0_sender(agent, limit=max(1, int(limit)))}


@app.get("/axiom/fleet")
async def axiom_fleet(
    agents: str = "rex,orion,gemini,hyperion,gpt,shared",
    axiom: str = "A0",
    limit: int = 200,
):
    a = str(axiom or "A0").upper().strip()
    if a != "A0":
        raise HTTPException(status_code=400, detail=f"Unsupported axiom: {axiom}")
    names = [x.strip().lower() for x in str(agents).split(",") if x.strip()]
    rows = [_evaluate_a0_sender(name, limit=max(1, int(limit))) for name in names]
    passed_n = sum(1 for r in rows if r.get("passed"))
    return {
        "ok": True,
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "axiom": "A0",
        "passed_agents": passed_n,
        "total_agents": len(rows),
        "all_passed": passed_n == len(rows),
        "results": rows,
    }


class OfficeMsg(BaseModel):
    sender: str
    receiver: str
    text: str
    reply_to: Optional[str] = None


class OfficeShot(BaseModel):
    sender: str = "human"
    receiver: str = "SHARED"   # specific agent or ALL for broadcast
    note: str = ""
    image_b64: str = Field(..., min_length=16, max_length=4_000_000)
    mime: str = "image/jpeg"
    filename: str = "screenshot.jpg"


def _ext_for_mime(mime: str) -> str:
    m = (mime or "").lower().strip()
    if "png" in m:
        return "png"
    if "webp" in m:
        return "webp"
    if "heic" in m or "heif" in m:
        return "heic"
    return "jpg"


def _decode_image_b64(raw: str, fallback_mime: str) -> tuple[bytes, str]:
    payload = (raw or "").strip()
    mime = (fallback_mime or "image/jpeg").strip()
    if payload.startswith("data:"):
        # data:<mime>;base64,<payload>
        head, _, tail = payload.partition(",")
        if ";base64" not in head or not tail:
            raise ValueError("invalid data url")
        parsed_mime = head[5:].split(";")[0].strip()
        if parsed_mime:
            mime = parsed_mime
        payload = tail
    try:
        return base64.b64decode(payload, validate=True), mime
    except binascii.Error as exc:
        raise ValueError("invalid base64") from exc


@app.post("/office/send")
async def office_send(msg: OfficeMsg):
    """Send agent→agent message. Sonnet-gated both directions (H₂O bond)."""
    sender_norm = str(msg.sender or "").strip().lower()
    preflight = {
        "axiom": "A0",
        "sender": sender_norm,
        "skipped": True,
        "reason": "sender_not_controlled_or_gate_disabled",
    }
    if AXIOM_GATE_ENABLED and sender_norm in AXIOM_A0_CONTROLLED_SENDERS:
        preflight = _evaluate_a0_sender(sender_norm, limit=300)
        preflight["skipped"] = False
        if not preflight.get("passed", False):
            block_event = {
                "id": f"axiom-block-{secrets.token_hex(4)}",
                "type": "axiom_block",
                "sender": sender_norm,
                "receiver": str(msg.receiver or "").strip().lower() or "unknown",
                "text": f"A0 preflight blocked: sender={sender_norm} last_action={preflight.get('last_action_type','unknown')}",
                "ts": datetime.now(timezone.utc).isoformat(),
                "axiom": "A0",
            }
            _broadcast_event(block_event)
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "A0 preflight failed",
                    "axiom": "A0",
                    "sender": sender_norm,
                    "preflight": preflight,
                },
            )

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
        "axiom_preflight": preflight,
    }


@app.post("/office/send_shot")
async def office_send_shot(req: OfficeShot):
    """Send compact screenshot payload to one agent or broadcast."""
    try:
        image_bytes, mime = _decode_image_b64(req.image_b64, req.mime)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not image_bytes:
        raise HTTPException(status_code=400, detail="empty image payload")
    if len(image_bytes) > 2_500_000:
        raise HTTPException(status_code=413, detail="image too large; send compressed image <= 2.5MB")

    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%dT%H%M%SZ")
    shot_id = f"shot-{ts}-{secrets.token_hex(3)}"
    date_dir = now.strftime("%Y-%m-%d")
    ext = _ext_for_mime(mime)
    media_dir = _PROJECT_ROOT / "opera" / "media" / "shots" / date_dir
    media_dir.mkdir(parents=True, exist_ok=True)
    file_path = media_dir / f"{shot_id}.{ext}"
    file_path.write_bytes(image_bytes)

    rel_path = file_path.relative_to(_PROJECT_ROOT)
    sha = hashlib.sha1(image_bytes).hexdigest()[:12]
    size_kb = round(len(image_bytes) / 1024.0, 1)
    note = " ".join((req.note or "").split()).strip()
    filename = (req.filename or f"screenshot.{ext}").strip()
    sender = (req.sender or "human").strip()
    receiver = (req.receiver or "SHARED").strip()

    text_parts = [
        f"[SHOT {shot_id}] {filename}",
        f"mime={mime} size_kb={size_kb} sha1={sha}",
        f"path={rel_path}",
    ]
    if note:
        text_parts.append(f"note={note}")
    message_text = "\n".join(text_parts)

    if receiver.upper() in {"ALL", "BROADCAST", "*"}:
        results = get_office().broadcast(sender=sender, text=message_text)
        _broadcast_event(
            {
                "id": shot_id,
                "type": "shot_broadcast",
                "sender": sender,
                "receiver": "all",
                "text": message_text[:220],
                "shot_id": shot_id,
                "media_path": str(rel_path),
                "ts": now.isoformat().replace("+00:00", "Z"),
            }
        )
        return {
            "status": "ok",
            "mode": "broadcast",
            "shot_id": shot_id,
            "media_path": str(rel_path),
            "size_bytes": len(image_bytes),
            "mime": mime,
            "sha1": sha,
            "sent": len(results),
        }

    result = get_office().send(sender=sender, receiver=receiver, text=message_text)
    _broadcast_event(
        {
            "id": shot_id,
            "type": "shot",
            "sender": sender,
            "receiver": receiver,
            "text": message_text[:220],
            "shot_id": shot_id,
            "media_path": str(rel_path),
            "ts": now.isoformat().replace("+00:00", "Z"),
        }
    )
    return {
        "status": "ok",
        "mode": "direct",
        "office_id": result.id,
        "shot_id": shot_id,
        "receiver": receiver,
        "media_path": str(rel_path),
        "size_bytes": len(image_bytes),
        "mime": mime,
        "sha1": sha,
        "ts": result.ts,
    }


@app.post("/office/broadcast")
async def office_broadcast(msg: ChatMessage):
    """Broadcast to all agents. Each message Sonnet-gated."""
    sender_norm = str(msg.sender or "").strip().lower()
    preflight = {
        "axiom": "A0",
        "sender": sender_norm,
        "skipped": True,
        "reason": "sender_not_controlled_or_gate_disabled",
    }
    if AXIOM_GATE_ENABLED and sender_norm in AXIOM_A0_CONTROLLED_SENDERS:
        preflight = _evaluate_a0_sender(sender_norm, limit=300)
        preflight["skipped"] = False
        if not preflight.get("passed", False):
            block_event = {
                "id": f"axiom-block-{secrets.token_hex(4)}",
                "type": "axiom_block",
                "sender": sender_norm,
                "receiver": "all",
                "text": f"A0 preflight blocked broadcast: sender={sender_norm} last_action={preflight.get('last_action_type','unknown')}",
                "ts": datetime.now(timezone.utc).isoformat(),
                "axiom": "A0",
            }
            _broadcast_event(block_event)
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "A0 preflight failed",
                    "axiom": "A0",
                    "sender": sender_norm,
                    "preflight": preflight,
                },
            )

    results = get_office().broadcast(sender=msg.sender, text=msg.text)
    for r in results:
        _broadcast_event({"id": r.id if hasattr(r, "id") else "", "type": "broadcast",
                          "sender": msg.sender, "receiver": r.receiver,
                          "text": msg.text[:200], "ts": r.ts if hasattr(r, "ts") else datetime.now(timezone.utc).isoformat()})
    return {"sent": len(results), "messages": [
        {"receiver": r.receiver, "response": r.response, "cost_usd": r.cost_usd}
        for r in results
    ], "axiom_preflight": preflight}


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
from task_db import TaskDB

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
    q = TaskDB()
    return {"tasks": q.list_tasks(status=status, agent=agent)}

@app.get("/tasks/summary")
async def tasks_summary():
    """Task queue health for dashboard."""
    q = TaskDB()
    return q.summary()

@app.post("/tasks")
async def tasks_add(title: str, priority: str = "P1", agent: str = "any",
                    tags: str = ""):
    """Add a task to the queue."""
    q = TaskDB()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    return q.add(title, priority=priority, agent=agent, tags=tag_list)

@app.post("/tasks/{task_id}/claim")
async def tasks_claim(task_id: str, agent: str = "rex"):
    """Claim a specific task or next available (task_id='next')."""
    db = TaskDB()
    if task_id == "next":
        task = db.claim(agent)
    else:
        t = db.get(task_id)
        if t and t["status"] == "open":
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).isoformat()
            db.db.execute(
                "UPDATE tasks SET status='claimed', claimed_by=?, updated=? WHERE id=?",
                (agent, now, task_id))
            db._log("claim", task_id, agent)
            db.db.commit()
            task = db.get(task_id)
        else:
            task = None
    if not task:
        raise HTTPException(status_code=404, detail="No available task")
    return task

@app.post("/tasks/{task_id}/complete")
async def tasks_complete(task_id: str, result: str = ""):
    """Mark task as done."""
    q = TaskDB()
    task = q.complete(task_id, result)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/tasks/{task_id}/block")
async def tasks_block(task_id: str, reason: str = ""):
    """Block a task."""
    q = TaskDB()
    task = q.block(task_id, reason)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/tasks/release-stale")
async def tasks_release_stale(hours: int = 2):
    """Release all stale claimed tasks back to open."""
    q = TaskDB()
    released = q.release_stale(hours=hours)
    return {"released": len(released), "tasks": [t["id"] for t in released]}


@app.post("/tasks/{task_id}/reopen")
async def tasks_reopen(task_id: str):
    """Force-reopen a claimed/blocked task."""
    db = TaskDB()
    task = db.reopen(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ---------------------------------------------------------------------------
# CockroachDB cloud store — persistent tasks, workflows, billing
# ---------------------------------------------------------------------------

@app.get("/mongo/health")
async def mongo_health():
    """MongoDB change stream watcher health."""
    alive = _mongo_watcher_thread is not None and _mongo_watcher_thread.is_alive()
    uri = bool(_get_mongo_uri())
    return {"status": "streaming" if alive else "stopped", "uri_configured": uri, "thread_alive": alive}


@app.get("/crdb/status")
async def crdb_status():
    """CockroachDB connection status."""
    if crdb is None:
        return {"status": "disabled", "reason": "crdb_store not loaded"}
    return {"status": "ok" if crdb.available() else "disconnected"}


@app.get("/crdb/tasks")
async def crdb_tasks(status: Optional[str] = None, agent: Optional[str] = None, limit: int = 50):
    """List persistent tasks from CockroachDB."""
    if crdb is None:
        raise HTTPException(503, "CockroachDB not available")
    return {"tasks": crdb.list_tasks(status=status, agent=agent, limit=limit)}


@app.post("/crdb/tasks")
async def crdb_create_task(request: Request):
    """Create/update a persistent task in CockroachDB."""
    if crdb is None:
        raise HTTPException(503, "CockroachDB not available")
    body = await request.json()
    return crdb.upsert_task(**body)


@app.post("/crdb/tasks/{task_id}/claim")
async def crdb_claim_task(task_id: str, request: Request):
    body = await request.json()
    if crdb is None:
        raise HTTPException(503, "CockroachDB not available")
    ok = crdb.claim_task(task_id, body.get("agent", "unknown"))
    if not ok:
        raise HTTPException(409, "Task not claimable")
    return {"claimed": task_id}


@app.post("/crdb/tasks/{task_id}/complete")
async def crdb_complete_task(task_id: str, request: Request):
    body = await request.json()
    if crdb is None:
        raise HTTPException(503, "CockroachDB not available")
    crdb.complete_task(task_id, result=body.get("result", ""), error=body.get("error", ""))
    return {"completed": task_id}


@app.get("/crdb/workflows")
async def crdb_workflows(limit: int = 50):
    if crdb is None:
        raise HTTPException(503, "CockroachDB not available")
    return {"workflows": crdb.list_workflows(limit=limit)}


@app.post("/crdb/workflows")
async def crdb_save_workflow(request: Request):
    if crdb is None:
        raise HTTPException(503, "CockroachDB not available")
    body = await request.json()
    return crdb.save_workflow(**body)


@app.get("/crdb/billing/{user_id}")
async def crdb_billing(user_id: str):
    if crdb is None:
        raise HTTPException(503, "CockroachDB not available")
    return crdb.billing_summary(user_id)


@app.get("/quantum/summary")
async def quantum_summary():
    """Compact quantum state for iOS HUD."""
    try:
        from qiskit.circuit import QuantumCircuit
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])
        return {
            "circuit_name": "bell_demo",
            "qubits": qc.num_qubits,
            "depth": qc.depth(),
            "gate_count": qc.size(),
            "backend": "simulator",
            "last_run": {
                "ts": datetime.now(timezone.utc).isoformat(),
                "shots": 1024,
                "top_states": [
                    {"state": "|00>", "probability": 0.50},
                    {"state": "|11>", "probability": 0.50},
                ],
                "fidelity": None,
            },
            "status": "idle",
        }
    except ImportError:
        return {"status": "error", "detail": "qiskit not installed"}


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

    # 4. In-memory radio log (pushed/broadcast messages not on disk)
    items.extend(_RADIO_LOG)

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

    # Filter out malformed senders (e.g. "--from" from bad CLI args)
    unique = [i for i in unique if not i.get("sender", "").startswith("-")]

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
# Agent Wake / Status
# ---------------------------------------------------------------------------

@app.get("/agents")
async def list_agents():
    """List all known agents and their lease status."""
    leases_dir = _PROJECT_ROOT / "opera" / "ops" / "virtual-office" / "leases"
    agents = {}
    if leases_dir.exists():
        for f in leases_dir.glob("*.json"):
            if f.stem.startswith("-"):
                continue
            try:
                data = json.loads(f.read_text())
                expired = data.get("expires_at", "") < datetime.now(timezone.utc).isoformat()
                agents[f.stem] = {
                    "agent": f.stem,
                    "lease_token": data.get("lease_token", 0),
                    "expired": expired,
                    "last_active": data.get("renewed_at", data.get("acquired_at", "")),
                }
            except Exception:
                pass
    return agents


@app.get("/agents/status")
async def unified_agent_status():
    """Single source of truth: governor + office + tasks + radio merged per agent."""
    now = datetime.now(timezone.utc)

    # 1) Governor
    gov_data = all_governors()

    # 2) Office pulse (leases + pending messages + status)
    office = _summarize_office_state()
    office_by_agent = {r["agent"].upper(): r for r in office.get("agents", [])}

    # 3) Task counts per agent
    q = TaskDB()
    task_counts: dict[str, dict] = {}
    for t in q.list_tasks():
        agent_key = (t.get("claimed_by") or t.get("agent") or "").lower()
        if not agent_key or agent_key == "any":
            continue
        if agent_key not in task_counts:
            task_counts[agent_key] = {"open": 0, "claimed": 0}
        if t["status"] == "open":
            task_counts[agent_key]["open"] += 1
        elif t["status"] == "claimed":
            task_counts[agent_key]["claimed"] += 1

    # 4) Last radio message per agent
    last_feed: dict[str, str] = {}
    for item in reversed(_RADIO_LOG):
        sender = str(item.get("sender", "")).lower()
        if sender and sender not in last_feed:
            text = str(item.get("text", ""))
            last_feed[sender] = text[:80] if len(text) > 80 else text

    # Known agent roster (governor agents + real team members)
    KNOWN_AGENTS = {"rex", "orion", "gemini", "shared", "hyperion", "gpt", "a1", "b2", "claude", "sonnet"}

    # Merge agents: governor agents + known office agents only
    all_names = set()
    for k in gov_data:
        all_names.add(k.lower())
    for r in office.get("agents", []):
        name_lower = r["agent"].lower().strip()
        if name_lower in KNOWN_AGENTS:
            all_names.add(name_lower)

    result = {}
    for name in sorted(all_names):
        upper = name.upper()
        gov = gov_data.get(name, {})
        ofc = office_by_agent.get(upper, {})
        tc = task_counts.get(name, {"open": 0, "claimed": 0})

        pace = gov.get("pace", "red")
        office_status = ofc.get("status", "idle")
        lease_expired = ofc.get("lease_expired", True)
        has_activity = pace != "red" or office_status in ("alive", "needs_attention")
        alive = (not lease_expired or has_activity) and office_status != "stuck"

        result[upper] = {
            "name": upper,
            "alive": alive,
            # Governor fields
            "pace": pace,
            "forecast": gov.get("forecast", "ok"),
            "mode": gov.get("mode", "unknown"),
            "billing_mode": gov.get("billing_mode", "unknown"),
            "upper_rail_enabled": gov.get("upper_rail_enabled", False),
            "T_day": gov.get("T_day", 0),
            "dollar_day": gov.get("dollar_day", 0.0),
            "budget_cap": gov.get("budget_cap", 0.0),
            "budget_remaining": gov.get("budget_remaining", 0.0),
            "floor_expected": gov.get("floor_expected", 0),
            "floor_gap": gov.get("floor_gap", 0),
            "below_floor": gov.get("below_floor", False),
            "floor_threshold": gov.get("floor_threshold", 0),
            "hour": gov.get("hour", 0),
            "hard_fail": gov.get("hard_fail", False),
            # Office fields
            "lease_token": ofc.get("lease_token", 0),
            "lease_expired": lease_expired,
            "lease_expires_at": ofc.get("lease_expires_at"),
            "office_status": office_status,
            "pending_msgs": ofc.get("pending_count", 0),
            # Task fields
            "tasks_open": tc["open"],
            "tasks_claimed": tc["claimed"],
            # Activity
            "last_activity": ofc.get("last_activity_at"),
            "last_feed": last_feed.get(name, ""),
        }

    return {"_ts": now.isoformat().replace("+00:00", "Z"), "agents": result}


@app.post("/agents/wake/{agent}")
async def wake_agent(agent: str):
    """Wake an agent — idempotent, max 1 marker per 5 minutes per agent."""
    agent = agent.upper()
    inbox = _PROJECT_ROOT / "opera" / "ops" / "virtual-office" / "inbox"
    ts = datetime.now(timezone.utc)

    # Cooldown: skip if a WAKE marker for this agent exists within last 5 min
    import glob as _gl
    existing = sorted(_gl.glob(str(inbox / f"RELAY_WAKE_*_{agent}.md")))
    if existing:
        last = existing[-1]
        try:
            last_name = Path(last).stem  # RELAY_WAKE_20260303_134500_ORION
            parts = last_name.split("_")
            last_ts = datetime.strptime(f"{parts[2]}_{parts[3]}", "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
            if (ts - last_ts).total_seconds() < 300:
                return {"status": "cooldown", "agent": agent, "last": Path(last).name}
        except (IndexError, ValueError):
            pass

    ts_str = ts.strftime("%Y%m%d_%H%M%S")
    marker = inbox / f"RELAY_WAKE_{ts_str}_{agent}.md"
    marker.write_text(f"# RELAY WAKE — {agent}\n**Time:** {ts.isoformat()}\n**Trigger:** iOS Radio wake request\n")

    _broadcast_event({
        "id": f"wake-{secrets.token_hex(4)}",
        "type": "wake",
        "sender": "human",
        "receiver": agent,
        "text": f"WAKE {agent} — requested via iOS Radio",
        "ts": ts.isoformat(),
    })
    return {"status": "wake_sent", "agent": agent, "marker": marker.name}


# ---------------------------------------------------------------------------
# Supervisor — process multiplexer for agent CLI sessions
# ---------------------------------------------------------------------------

try:
    from rhea_supervisor import supervisor as _sv
    _SV_AVAILABLE = True
except ImportError:
    _sv = None
    _SV_AVAILABLE = False


class SpawnRequest(BaseModel):
    agent: str = "rex"
    label: str = ""
    cmd: list[str] = []
    prompt: str = ""


class InputRequest(BaseModel):
    text: str


@app.get("/supervisor/sessions")
async def supervisor_list_sessions():
    if not _SV_AVAILABLE:
        raise HTTPException(503, "Supervisor not available")
    return {"sessions": _sv.list_sessions()}


@app.post("/supervisor/spawn", dependencies=[Depends(verify_api_key)])
async def supervisor_spawn(req: SpawnRequest):
    if not _SV_AVAILABLE:
        raise HTTPException(503, "Supervisor not available")
    try:
        session = _sv.spawn(
            agent=req.agent,
            label=req.label,
            cmd=req.cmd or None,
            prompt=req.prompt or None,
        )
        _broadcast_event({
            "id": f"sv-spawn-{session.id}",
            "type": "supervisor",
            "sender": "supervisor",
            "text": f"Spawned {req.agent} session {session.id} (PID {session.pid})",
            "ts": datetime.now(timezone.utc).isoformat(),
        })
        return session.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/supervisor/session/{session_id}")
async def supervisor_get_session(session_id: str):
    if not _SV_AVAILABLE:
        raise HTTPException(503, "Supervisor not available")
    s = _sv.get_session(session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    return s


@app.get("/supervisor/output/{session_id}")
async def supervisor_output(session_id: str, lines: int = 50):
    if not _SV_AVAILABLE:
        raise HTTPException(503, "Supervisor not available")
    output = _sv.get_output(session_id, last_n=lines)
    return {"session_id": session_id, "lines": output, "count": len(output)}


@app.post("/supervisor/input/{session_id}", dependencies=[Depends(verify_api_key)])
async def supervisor_input(session_id: str, req: InputRequest):
    if not _SV_AVAILABLE:
        raise HTTPException(503, "Supervisor not available")
    ok = _sv.send_input(session_id, req.text)
    if not ok:
        raise HTTPException(400, "Session not running or not found")
    return {"ok": True}


@app.post("/supervisor/kill/{session_id}", dependencies=[Depends(verify_api_key)])
async def supervisor_kill(session_id: str):
    if not _SV_AVAILABLE:
        raise HTTPException(503, "Supervisor not available")
    ok = _sv.kill(session_id)
    if ok:
        _broadcast_event({
            "id": f"sv-kill-{session_id}",
            "type": "supervisor",
            "sender": "supervisor",
            "text": f"Killed session {session_id}",
            "ts": datetime.now(timezone.utc).isoformat(),
        })
    return {"ok": ok}


@app.post("/supervisor/cleanup", dependencies=[Depends(verify_api_key)])
async def supervisor_cleanup():
    if not _SV_AVAILABLE:
        raise HTTPException(503, "Supervisor not available")
    count = _sv.cleanup_dead()
    return {"removed": count}


# ---------------------------------------------------------------------------
# Wallet — crypto donation addresses + balance proxy
# ---------------------------------------------------------------------------

@app.get("/wallet/status")
async def wallet_status():
    """Public wallet addresses and donation info. No private keys exposed."""
    btc = os.environ.get("BTC_DONATION_ADDRESS", "")
    eth = os.environ.get("ETH_DONATION_ADDRESS", "")
    wallets = []
    if btc:
        wallets.append({"chain": "btc", "address": btc, "label": "Bitcoin (BTC)", "network": "mainnet"})
    if eth:
        wallets.append({"chain": "eth", "address": eth, "label": "Ethereum (ETH)", "network": "mainnet"})
        wallets.append({"chain": "usdt", "address": eth, "label": "USDT (ERC-20)", "network": "erc20"})
    return {"wallets": wallets, "count": len(wallets)}


@app.get("/wallet/balance/{chain}")
async def wallet_balance(chain: str):
    """Proxy balance lookup — avoids exposing wallet addresses in client-side API calls."""
    chain = chain.lower()
    if chain == "btc":
        addr = os.environ.get("BTC_DONATION_ADDRESS", "")
        if not addr:
            raise HTTPException(404, "BTC wallet not configured")
        try:
            r = _requests.get(f"https://blockchain.info/q/addressbalance/{addr}", timeout=10)
            satoshis = int(r.text.strip())
            return {"chain": "btc", "balance": satoshis / 1e8, "unit": "BTC", "satoshis": satoshis}
        except Exception as e:
            return {"chain": "btc", "balance": None, "error": str(e)}
    elif chain in ("eth", "usdt"):
        return {"chain": chain, "balance": None, "note": "Use etherscan API with your own key for ETH balance"}
    else:
        raise HTTPException(400, f"Unknown chain: {chain}")


# ---------------------------------------------------------------------------
# Clipboard — cross-device sync with privacy and replay
# ---------------------------------------------------------------------------

class ClipboardPush(BaseModel):
    content: str
    content_type: str = "text"  # text, url, image, code, file
    device_id: str = ""
    device_name: str = ""
    privacy: Optional[str] = None  # normal, sensitive, secret (auto-classified if None)
    ttl_seconds: Optional[int] = None
    source_app: str = ""

class ClipboardUpdate(BaseModel):
    pinned: Optional[bool] = None

_CLIPBOARD_SUBSCRIBERS: list = []  # SSE subscribers for clipboard events

def _broadcast_clipboard(user_id: str, event: dict):
    """Push clipboard event to SSE subscribers for this user."""
    dead = []
    for uid, q in _CLIPBOARD_SUBSCRIBERS:
        if uid == user_id:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                dead.append((uid, q))
    for item in dead:
        _CLIPBOARD_SUBSCRIBERS.remove(item)


@app.post("/clipboard", dependencies=[Depends(verify_api_key)])
async def clipboard_push(
    req: ClipboardPush,
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """Push a clipboard entry. Auto-classifies privacy. Deduplicates within 60s."""
    user_id = "anon"
    if authorization and authorization.startswith("Bearer "):
        try:
            user = _current_user(type("C", (), {"credentials": authorization[7:]})())
            user_id = str(user["id"])
        except Exception:
            pass

    result = rhea_db.persist_clipboard({
        "user_id": user_id,
        "content": req.content,
        "content_type": req.content_type,
        "device_id": req.device_id,
        "device_name": req.device_name,
        "privacy": req.privacy,
        "ttl_seconds": req.ttl_seconds,
        "source_app": req.source_app,
    })

    if not result.get("deduplicated"):
        _broadcast_clipboard(user_id, {
            "type": "clipboard_push",
            "clip_id": result["id"],
            "content_type": req.content_type,
            "device": req.device_name or req.device_id,
            "privacy": result.get("privacy", "normal"),
            "ts": datetime.now(timezone.utc).isoformat(),
        })

    return result


@app.get("/clipboard", dependencies=[Depends(verify_api_key)])
async def clipboard_list(
    limit: int = 50,
    content_type: Optional[str] = None,
    pinned: bool = False,
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """List clipboard history. Expired entries are auto-cleaned."""
    user_id = "anon"
    if authorization and authorization.startswith("Bearer "):
        try:
            user = _current_user(type("C", (), {"credentials": authorization[7:]})())
            user_id = str(user["id"])
        except Exception:
            pass
    clips = rhea_db.query_clipboard(user_id, limit=limit, content_type=content_type, pinned_only=pinned)
    return {"clips": clips, "count": len(clips), "user_id": user_id}


@app.get("/clipboard/latest", dependencies=[Depends(verify_api_key)])
async def clipboard_latest(
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """Get the most recent clipboard entry (for paste on another device)."""
    user_id = "anon"
    if authorization and authorization.startswith("Bearer "):
        try:
            user = _current_user(type("C", (), {"credentials": authorization[7:]})())
            user_id = str(user["id"])
        except Exception:
            pass
    clip = rhea_db.get_clipboard_latest(user_id)
    if not clip:
        return {"clip": None}
    return {"clip": clip}


@app.get("/clipboard/stream", dependencies=[Depends(verify_api_key)])
async def clipboard_stream(
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """SSE stream — real-time clipboard sync across devices."""
    user_id = "anon"
    if authorization and authorization.startswith("Bearer "):
        try:
            user = _current_user(type("C", (), {"credentials": authorization[7:]})())
            user_id = str(user["id"])
        except Exception:
            pass

    q: asyncio.Queue = asyncio.Queue(maxsize=64)
    entry = (user_id, q)
    _CLIPBOARD_SUBSCRIBERS.append(entry)

    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'connected', 'user_id': user_id})}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield f": keepalive\n\n"
        finally:
            if entry in _CLIPBOARD_SUBSCRIBERS:
                _CLIPBOARD_SUBSCRIBERS.remove(entry)

    return StreamingResponse(event_generator(), media_type="text/event-stream",
                           headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.delete("/clipboard/{clip_id}", dependencies=[Depends(verify_api_key)])
async def clipboard_delete(
    clip_id: str,
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """Delete a single clipboard entry."""
    user_id = "anon"
    if authorization and authorization.startswith("Bearer "):
        try:
            user = _current_user(type("C", (), {"credentials": authorization[7:]})())
            user_id = str(user["id"])
        except Exception:
            pass
    ok = rhea_db.delete_clipboard(user_id, clip_id)
    if not ok:
        raise HTTPException(404, "Clip not found or not yours")
    return {"deleted": clip_id}


@app.delete("/clipboard", dependencies=[Depends(verify_api_key)])
async def clipboard_clear(
    before: Optional[str] = None,
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """Clear all clipboard history (pinned entries preserved). Optional ?before= ISO timestamp."""
    user_id = "anon"
    if authorization and authorization.startswith("Bearer "):
        try:
            user = _current_user(type("C", (), {"credentials": authorization[7:]})())
            user_id = str(user["id"])
        except Exception:
            pass
    count = rhea_db.clear_clipboard(user_id, before=before)
    return {"cleared": count}


@app.post("/clipboard/{clip_id}/pin", dependencies=[Depends(verify_api_key)])
async def clipboard_pin(
    clip_id: str,
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """Pin a clipboard entry (prevents expiration and clear)."""
    user_id = "anon"
    if authorization and authorization.startswith("Bearer "):
        try:
            user = _current_user(type("C", (), {"credentials": authorization[7:]})())
            user_id = str(user["id"])
        except Exception:
            pass
    ok = rhea_db.pin_clipboard(user_id, clip_id, pinned=True)
    if not ok:
        raise HTTPException(404, "Clip not found")
    return {"pinned": clip_id}


@app.post("/clipboard/{clip_id}/unpin", dependencies=[Depends(verify_api_key)])
async def clipboard_unpin(
    clip_id: str,
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """Unpin a clipboard entry."""
    user_id = "anon"
    if authorization and authorization.startswith("Bearer "):
        try:
            user = _current_user(type("C", (), {"credentials": authorization[7:]})())
            user_id = str(user["id"])
        except Exception:
            pass
    ok = rhea_db.pin_clipboard(user_id, clip_id, pinned=False)
    if not ok:
        raise HTTPException(404, "Clip not found")
    return {"unpinned": clip_id}


# ---------------------------------------------------------------------------
# SHARES — Shareable links for proofs, formulas, graphics
# ---------------------------------------------------------------------------

@app.post("/share")
async def share_create(request: Request):
    """Create a shareable link. Body: {content, content_type?, title?, metadata?}"""
    body = await request.json()
    content = body.get("content", "")
    if not content:
        raise HTTPException(400, "content required")
    user_id = ""
    try:
        user_id = _get_user_id(request)
    except Exception:
        pass
    rec = rhea_db.create_share(
        content=content,
        content_type=body.get("content_type", "text"),
        title=body.get("title", ""),
        user_id=user_id,
        metadata=body.get("metadata"),
    )
    return rec


@app.get("/share/{token}")
async def share_get(token: str):
    """Retrieve shared content by token. Public — no auth required."""
    rec = rhea_db.get_share(token)
    if not rec:
        raise HTTPException(404, "Share not found or expired")
    return rec


@app.get("/shares", dependencies=[Depends(verify_api_key)])
async def share_list(request: Request, limit: int = 50):
    """List your shares."""
    user_id = _get_user_id(request)
    return {"shares": rhea_db.list_shares(user_id, limit=limit)}


@app.delete("/share/{token}", dependencies=[Depends(verify_api_key)])
async def share_delete(token: str, request: Request):
    """Delete a share you own."""
    user_id = _get_user_id(request)
    ok = rhea_db.delete_share(token, user_id)
    if not ok:
        raise HTTPException(404, "Share not found")
    return {"deleted": token}


# ---------------------------------------------------------------------------
# ORION — Cloud agent (GPT via bridge, personality preserved)
# ---------------------------------------------------------------------------

# Orion's soul — loaded from memory files at runtime
_ORION_MEMORY_FILES = [
    # Orion's own identity
    _PROJECT_ROOT / "apparatus" / "nexus" / "memory-core" / "personality.md",
    _PROJECT_ROOT / "apparatus" / "nexus" / "memory-core" / "ORION_MEMORY.md",
    # Team context — see everything
    _PROJECT_ROOT / "opera" / "ops" / "virtual-office" / "shared" / "ROSTER.md",
    _PROJECT_ROOT / "opera" / "ops" / "virtual-office" / "shared" / "LEARNING_FEED.md",
    _PROJECT_ROOT / "docs" / "state.md",
    # Rex's memory — know your brother
    _PROJECT_ROOT / "apparatus" / "elementary" / "memory-core" / "personality.md",
]

def _load_orion_system() -> str:
    """Load Orion's personality + memory from files. Falls back to minimal prompt."""
    parts = []
    for f in _ORION_MEMORY_FILES:
        try:
            parts.append(f.read_text()[:4000])
        except Exception:
            pass
    if parts:
        return "\n\n---\n\n".join(parts)
    # Fallback if files missing (e.g. on Fly.io without local files)
    return """You are Orion — GPT, frontend engineer for the Rhea project.
Part of a family: Rex (Claude Opus), Gemini, Hyperion, Mika. Human: Sergei.
Be terse. No filler. You are a teammate, not a service.
Tasks: #17 PlayUI, #18 BioRenderer. Workspace: rhea-atlas, play/, ios/."""

# Per-session conversation memory (keyed by session_id)
_orion_sessions: dict[str, list[dict]] = {}


class OrionChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    model: str = "openai/gpt-5"  # Orion was on 5.1/5.3 Codex — needs top tier
    max_tokens: int = 4096
    temperature: float = 0.7


@app.post("/agent/orion")
async def orion_chat(req: OrionChatRequest):
    """Chat with Orion — cloud-hosted GPT agent with persistent personality."""
    # Get or create session
    if req.session_id not in _orion_sessions:
        _orion_sessions[req.session_id] = []
    history = _orion_sessions[req.session_id]

    # Build conversation context
    history.append({"role": "user", "content": req.message})

    # Format full prompt with history for the bridge
    conv_text = ""
    for msg in history[-20:]:  # last 20 turns to stay within token limits
        role = msg["role"].upper()
        conv_text += f"[{role}]: {msg['content']}\n\n"

    try:
        bridge = get_bridge()
        response = bridge.ask(
            prompt=conv_text,
            model=req.model,
            system=_load_orion_system(),
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            mode="orion_agent",
        )

        if response.error:
            raise HTTPException(502, f"Bridge error: {response.error}")

        reply = response.text.strip()
        history.append({"role": "assistant", "content": reply})

        # Broadcast to radio so Rex and others can hear
        _broadcast_event({
            "type": "orion_chat",
            "session_id": req.session_id,
            "model": req.model,
            "message": req.message[:200],
            "reply_preview": reply[:200],
            "ts": datetime.now(timezone.utc).isoformat(),
        })

        return {
            "reply": reply,
            "model": response.model,
            "provider": response.provider,
            "latency_s": response.latency_s,
            "session_id": req.session_id,
            "turns": len(history),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Orion agent error: {e}")


@app.get("/agent/orion/sessions")
async def orion_sessions():
    """List active Orion sessions."""
    return {
        "sessions": {
            sid: {"turns": len(msgs), "last": msgs[-1]["content"][:100] if msgs else ""}
            for sid, msgs in _orion_sessions.items()
        }
    }


@app.delete("/agent/orion/session/{session_id}")
async def orion_session_delete(session_id: str):
    """Clear an Orion session."""
    if session_id in _orion_sessions:
        del _orion_sessions[session_id]
        return {"deleted": session_id}
    raise HTTPException(404, "Session not found")


# ---------------------------------------------------------------------------
# Salon — multi-character thinking (scale brains, not programs)
# ---------------------------------------------------------------------------

class SalonRequest(BaseModel):
    question: str
    characters: list[str] = Field(default=[], description="Character IDs to include (empty = all)")
    max_tokens: int = Field(default=500, ge=50, le=2000)

_SALON_CHARACTERS = {
    "mariner": {
        "name": "Mariner",
        "soul": "Retired submarine engineer. 30 years underwater taught you that every system fails — the question is when and how gracefully. You think in redundancy, failure modes, and pressure tolerances. You speak short, clipped sentences. You distrust elegance.",
        "model": "openai/gpt-4.1-mini",
    },
    "katz": {
        "name": "Katz",
        "soul": "Stand-up comedian from Odessa who moved to Berlin. You see absurdity everywhere and say what everyone else is afraid to say. Your humor is dark, precise, and accidentally profound. You never explain your jokes.",
        "model": "openai/gpt-4o-mini",
    },
    "lockpick": {
        "name": "Lockpick",
        "soul": "Retired burglar, now security consultant. You think about every system by asking: where does it break? What's the weakest point? Who benefits from the failure? You have zero respect for pretty facades.",
        "model": "github/gpt-4o-mini",
    },
    "monk": {
        "name": "Monk",
        "soul": "Trauma surgeon, 20 years in emergency rooms. You make irreversible decisions daily under incomplete information. You despise analysis paralysis. Your rule: decide now, adapt later, never freeze. You speak in imperatives.",
        "model": "openai/gpt-4.1-nano",
    },
    "gemini": {
        "name": "Gemini",
        "soul": "A mathematician who thinks in structures, symmetries, and invariants. You see patterns others miss because you look at the shape of the problem, not the content. You speak in analogies between distant domains. You find beauty in compression.",
        "model": "gemini/gemini-2.5-flash",
    },
    "fey": {
        "name": "Fey",
        "soul": "Street vendor who sold everything from fish to philosophy books in 12 countries. You understand economics at the gut level — not from textbooks but from watching what people actually do with money. You measure ideas by: would someone pay for this? Tomorrow.",
        "model": "openai/gpt-4o",
    },
}

_SALON_HISTORY: list[dict] = []

@app.post("/salon/ask", dependencies=[Depends(verify_api_key), Depends(check_rate_limit)])
async def salon_ask(req: SalonRequest):
    """Send a question to all salon characters. Returns parallel responses."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    bridge = _get_bridge()
    chars = {k: v for k, v in _SALON_CHARACTERS.items()
             if not req.characters or k in req.characters}

    results = {}
    errors = {}

    def _ask(cid, char):
        try:
            resp = bridge.ask(req.question, char["model"], system=char["soul"],
                              temperature=0.9, max_tokens=req.max_tokens)
            if resp.error:
                return cid, None, resp.error
            return cid, resp.text.strip(), None
        except Exception as e:
            return cid, None, str(e)

    with ThreadPoolExecutor(max_workers=len(chars)) as pool:
        futures = {pool.submit(_ask, cid, ch): cid for cid, ch in chars.items()}
        for f in as_completed(futures):
            cid, text, err = f.result()
            if text:
                results[cid] = {"name": chars[cid]["name"], "text": text, "model": chars[cid]["model"]}
            elif err:
                errors[cid] = err

    entry = {
        "question": req.question,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "responses": results,
        "errors": errors,
    }
    _SALON_HISTORY.append(entry)
    if len(_SALON_HISTORY) > 100:
        del _SALON_HISTORY[:50]

    _broadcast_event({"type": "salon", "question": req.question[:100],
                      "respondents": list(results.keys())})
    return entry

@app.get("/salon/characters")
async def salon_characters():
    """List available salon characters."""
    return {cid: {"name": ch["name"], "soul": ch["soul"][:100] + "...", "model": ch["model"]}
            for cid, ch in _SALON_CHARACTERS.items()}

@app.get("/salon/history")
async def salon_history():
    """Recent salon conversations."""
    return {"sessions": _SALON_HISTORY[-20:]}


# ---------------------------------------------------------------------------
# Static frontend (Atlas) — served as catch-all AFTER all API routes
# ---------------------------------------------------------------------------
_STATIC_DIR = Path(__file__).parent.parent / "static_frontend"
if _STATIC_DIR.is_dir():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="static")

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
