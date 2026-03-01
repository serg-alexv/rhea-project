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
    description="Multi-model consensus as a service. Send a prompt, get structured agreement analysis across 3-7 AI models.",
    version="0.1.0",
)

# Expose Aletheia read-only endpoints under /api/aletheia (mirrors rhead /aletheia)
app.include_router(aletheia_router, prefix="/aletheia")

# Auth (signup/login/profile)
from auth_api import auth_router
app.include_router(auth_router, prefix="/auth")

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
            from auth_api import _decode_token
            _decode_token(authorization[7:])
            return  # valid JWT — allow through
        except Exception:
            pass  # fall through to API key check

    if not TRIBUNAL_API_KEYS:
        raise HTTPException(status_code=401, detail="API is locked: No keys configured in TRIBUNAL_API_KEYS")
    if not x_api_key or x_api_key not in TRIBUNAL_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key. Sign up at /auth/signup")


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

@app.get("/")
async def landing():
    """Landing page — what Rhea is + how to try it."""
    from fastapi.responses import HTMLResponse
    # Dynamic stats from Aletheia
    try:
        from aletheia_pipeline import AletheiaCapturePipeline
        pipe = AletheiaCapturePipeline()
        stats = pipe.get_stats()
        proof_count = stats.get("proof_count", 0)
        ontology_count = stats.get("ontology_count", 0)
        avg_confidence = stats.get("avg_confidence")
        avg_conf_str = f"{avg_confidence:.0%}" if avg_confidence else "—"
    except Exception:
        proof_count, ontology_count, avg_conf_str = 0, 0, "—"

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

    url = os.environ.get("FLY_APP_NAME") and "https://rhea-tribunal.fly.dev" or "http://localhost:8400"
    providers_line = f"{n_providers} model{'s' if n_providers != 1 else ''} live" if n_providers > 0 else "warming up"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rhea</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'SF Mono',SFMono-Regular,Menlo,Consolas,monospace;
  background:#050505;color:#c0c0c0;display:flex;justify-content:center;padding:3rem 1.5rem}}
main{{max-width:600px;width:100%}}
.mark{{font-size:2.8rem;color:#fff;letter-spacing:-.05em;margin-bottom:.2rem}}
.epithet{{color:#555;font-size:.85rem;margin-bottom:2.5rem;line-height:1.5}}
.axiom{{color:#ff4400;font-size:1.1rem;margin:2rem 0;padding:.8rem 1.2rem;
  border-left:2px solid #ff4400;letter-spacing:.02em}}
.axiom small{{color:#444;display:block;margin-top:.3rem;font-size:.75rem}}
.live{{display:flex;gap:1.5rem;margin:2rem 0;flex-wrap:wrap}}
.live .v{{font-size:1.6rem;color:#fff;font-weight:600}}
.live .k{{color:#444;font-size:.65rem;text-transform:uppercase;letter-spacing:.15em}}
.live .cell{{min-width:80px}}
h2{{font-size:.7rem;color:#333;margin:2.5rem 0 .8rem;text-transform:uppercase;
  letter-spacing:.2em;font-weight:400}}
pre{{background:#0a0a0a;padding:1rem;border-radius:4px;overflow-x:auto;
  font-size:.78rem;line-height:1.6;margin:.5rem 0;border:1px solid #151515}}
code{{color:#888}}.g{{color:#4a7}}.r{{color:#a44}}.w{{color:#ddd}}
a{{color:#666;text-decoration:none;border-bottom:1px solid #222}}
a:hover{{color:#fff;border-color:#444}}
.hunt{{color:#666;font-size:.8rem;line-height:1.7;margin:1.5rem 0}}
.hunt em{{color:#999;font-style:normal}}
.foot{{margin-top:4rem;color:#222;font-size:.65rem;text-align:center;letter-spacing:.1em}}
</style></head>
<body><main>

<div class="mark">Rhea</div>
<p class="epithet">The titan who tricked Time.<br>
Now she spins the Toile.</p>

<div class="axiom">&#x2207; &gt; 0 &#x2228; &#x22A5;
<small>gradient positive or bottom &mdash; settle and you're prey</small></div>

<div class="live">
<div class="cell"><div class="v">{proof_count}</div><div class="k">proofs</div></div>
<div class="cell"><div class="v">{ontology_count}</div><div class="k">ontologies</div></div>
<div class="cell"><div class="v">{avg_conf_str}</div><div class="k">confidence</div></div>
<div class="cell"><div class="v">{providers_line}</div><div class="k">right now</div></div>
</div>

<h2>Pull a thread</h2>
<pre><code><span class="g">curl</span> <span class="w">"{url}/aletheia/search?q=hemoglobin"</span>

<span class="g">curl</span> <span class="w">"{url}/aletheia/stats"</span>

<span class="g">curl</span> -X POST {url}/tribunal \\
  -H <span class="w">"Content-Type: application/json"</span> \\
  -H <span class="w">"Authorization: Bearer YOUR_TOKEN"</span> \\
  -d <span class="w">'{{"prompt":"ATP synthase uses rotary catalysis"}}'</span></code></pre>

<h2>What the spider does</h2>
<p class="hunt">
You throw a claim into the web.<br>
Rhea sends it to <em>{n_providers} independent model{'s' if n_providers != 1 else ''}</em> &mdash; they don't see each other.<br>
Agreement = signal. Divergence = where the lie hides.<br>
Every kill is stored in <em>Aletheia</em> &mdash; provenance chains, not marketing copy.</p>

<h2>Endpoints</h2>
<pre><code><span class="g">GET </span> /aletheia/search?q=   search the web
<span class="g">GET </span> /aletheia/stats       what's caught
<span class="g">GET </span> /aletheia/proofs      all kills
<span class="g">GET </span> /agents/status        who's hunting
<span class="g">POST</span> /tribunal             verify a claim
<span class="g">POST</span> /tribunal/ice         deep verification
<span class="g">GET </span> /health               pulse</code></pre>

<h2>Get started</h2>
<pre><code><span class="g">curl</span> -X POST {url}/auth/signup \\
  -H <span class="w">"Content-Type: application/json"</span> \\
  -d <span class="w">'{{"email":"you@example.com","password":"your-password"}}'</span>

<span class="r"># Returns: {{"token": "eyJ..."}}</span>
<span class="r"># Use in Authorization: Bearer YOUR_TOKEN</span></code></pre>

<p class="hunt">
<em>iOS app</em>: <a href="https://testflight.apple.com/join/BNya22Jg">TestFlight</a><br>
<em>macOS app</em>: <a href="https://github.com/serg-alexv/rhea-project/releases">GitHub Releases</a><br>
<em>Memory package</em>: <code>pip install packages/rhea-memory/</code>
</p>

<h2>Anatomy</h2>
<pre><code>FastAPI &middot; SQLite WAL &middot; Gemini 2.5 Flash &middot; Fly.io
Built by a biochemist and three AI agents.
<a href="https://github.com/serg-alexv/rhea-project">src</a> &middot; <a href="https://github.com/serg-alexv/rhea-project/releases">releases</a></code></pre>

<div class="foot">&#x2207; &gt; 0 &#x2228; &#x22A5;</div>
</main></body></html>"""
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

@app.get("/cc/history", dependencies=[Depends(verify_api_key)])
async def cc_history(limit: int = 50, session_id: Optional[str] = None, type: Optional[str] = None):
    """Persistent history from SQL — survives restarts."""
    return {"history": rhea_db.query_history(limit=limit, session_id=session_id, type_filter=type)}

@app.get("/cc/radio", dependencies=[Depends(verify_api_key)])
async def cc_radio(limit: int = 100, since: Optional[str] = None):
    """Persistent radio feed from SQL."""
    return {"radio": rhea_db.query_radio(limit=limit, since=since)}

@app.get("/cc/office", dependencies=[Depends(verify_api_key)])
async def cc_office(limit: int = 50, agent: Optional[str] = None):
    """Persistent office messages from SQL."""
    return {"messages": rhea_db.query_office(limit=limit, agent=agent)}

@app.get("/cc/sessions", dependencies=[Depends(verify_api_key)])
async def cc_sessions(limit: int = 20):
    """List all tribunal sessions with step counts."""
    return {"sessions": rhea_db.query_sessions(limit=limit)}

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

@app.on_event("startup")
async def startup():
    # Initialize SQL persistence (rhea.db)
    rhea_db.init_db()
    rhea_db.start_session(rhea_db.get_session_id(), agent="tribunal")
    migrated = rhea_db.migrate_office_jsonl()
    if migrated:
        print(f"[rhea_db] migrated {migrated} office messages from JSONL to SQL")
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
    """Wake an agent by writing a wake marker and broadcasting on Radio."""
    agent = agent.upper()
    # Write wake marker
    inbox = _PROJECT_ROOT / "opera" / "ops" / "virtual-office" / "inbox"
    ts = datetime.now(timezone.utc)
    ts_str = ts.strftime("%Y%m%d_%H%M%S")
    marker = inbox / f"RELAY_WAKE_{ts_str}_{agent}.md"
    marker.write_text(f"# RELAY WAKE — {agent}\n**Time:** {ts.isoformat()}\n**Trigger:** iOS Radio wake request\n")

    # Broadcast on radio
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
