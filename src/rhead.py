#!/usr/bin/env python3
"""
rhead.py — Rhea's single daemon entry point.
Unified version: preserves Cloud Probes (stage4) + Agent Bus (hyperion).
"""
import os
import sys
import json
import asyncio
import time
import sqlite3
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel, Field
import uvicorn

# Project Root & Path Setup
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Load env (native — no python-dotenv dependency)
from env_loader import load_env
load_env(PROJECT_ROOT / ".env", override=True)

from rhea_bus import RheaBus
try:
    from tribunal_api import app as tribunal_app
except ImportError:
    tribunal_app = None

# Set dev API key for local frontend
if not os.environ.get("TRIBUNAL_API_KEYS"):
    os.environ["TRIBUNAL_API_KEYS"] = "dev-bypass"

# Environment detection
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").lower()
IS_PRODUCTION = ENVIRONMENT == "production"
VERSION = os.environ.get("VERSION", "4.1.0-STM")

app = FastAPI(
    title="Rhea Daemon",
    description="Single entry point for all Rhea services (L1-L3 + Agent Bus).",
    version=VERSION,
)

# ---------------------------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------------------------
if IS_PRODUCTION:
    _allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "")
    _cors_origins = [o.strip() for o in _allowed_origins_env.split(",") if o.strip()]
    if not _cors_origins:
        _cors_origins = []
else:
    _cors_origins = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not IS_PRODUCTION else _cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=not IS_PRODUCTION,
)

# ---------------------------------------------------------------------------
# Routers & Mounting
# ---------------------------------------------------------------------------

# Mount Tribunal API under /api
if tribunal_app:
    app.mount("/api", tribunal_app)

# Mount auth router
try:
    from auth_api import auth_router
    app.include_router(auth_router, prefix="/auth")
except ImportError:
    pass

# Mount Aletheia proof pipeline router
try:
    from aletheia_api import aletheia_router
    app.include_router(aletheia_router, prefix="/aletheia")
except ImportError:
    pass

# Mount frontend
_FRONTEND_DIR = PROJECT_ROOT / "frontend"
if _FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")

# ---------------------------------------------------------------------------
# Redis / Bus Setup
# ---------------------------------------------------------------------------
_bus: Optional[RheaBus] = None

def _get_bus() -> Optional[RheaBus]:
    global _bus
    if _bus is None:
        try:
            _bus = RheaBus("rhead")
            if not _bus.ping():
                # Attempt to use local fallback if URL fails? 
                # RheaBus already handles fallback to localhost:6379
                pass
        except Exception:
            _bus = None
    return _bus

# ---------------------------------------------------------------------------
# Core Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def read_root():
    bus = _get_bus()
    payload = {
        "status": "ALIVE",
        "version": VERSION,
        "engine": "rhead (Scientific Gem)",
        "message": "Welcome to the Rhea Council Chamber. STM Layer is ACTIVE.",
        "endpoints": {
            "/": "this message",
            "/health": "full component probes",
            "/app": "frontend UI",
            "/events": "SSE live event stream",
            "/agents": "live agent heartbeats",
            "/api/tribunal": "consensus API",
        }
    }
    if not IS_PRODUCTION:
        payload["node"] = "ORION-NODE-02"
        payload["redis"] = "connected" if bus and bus.ping() else "unavailable"
    return payload

# ---------------------------------------------------------------------------
# Health & Probes (Stage 4 Logic)
# ---------------------------------------------------------------------------
_START_TIME = time.time()

def _probe_component(name, check_fn):
    start = time.time()
    result = {"name": name, "status": "offline", "latency_ms": None, "detail": None}
    try:
        detail = check_fn()
        result["status"] = "online"
        result["latency_ms"] = round((time.time() - start) * 1000, 1)
        result["detail"] = detail
    except Exception as e:
        result["latency_ms"] = round((time.time() - start) * 1000, 1)
        result["detail"] = str(e)[:120]
    return result

def _probe_all_components():
    import concurrent.futures
    probes = {}
    bus = _get_bus()

    # 1. Redis
    def check_redis():
        if not bus or not bus.r: raise ConnectionError("no redis client")
        bus.r.ping()
        return "connected"
    probes["redis"] = check_redis

    # 2. SQLite
    def check_sqlite():
        db_path = PROJECT_ROOT / "data" / "rhea.db"
        conn = sqlite3.connect(str(db_path), timeout=2)
        count = conn.execute("SELECT count(*) FROM history").fetchone()[0]
        conn.close()
        return f"history_records={count}"
    probes["sqlite"] = check_sqlite

    # 3. LLM Bridge
    def check_bridge():
        from rhea_bridge import RheaBridge
        _b = RheaBridge()
        st = _b.models_status()
        return f"{st['summary']['available_providers']} providers"
    probes["llm_bridge"] = check_bridge

    # Run in parallel
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_probe_component, name, fn): name for name, fn in probes.items()}
        for future in concurrent.futures.as_completed(futures, timeout=5):
            results.append(future.result())
    return sorted(results, key=lambda x: x["name"])

@app.get("/health")
def health_check():
    bus = _get_bus()
    components = _probe_all_components()
    online = sum(1 for c in components if c["status"] == "online")
    
    agents = bus.get_heartbeats() if bus else {}
    
    return {
        "status": "ok" if online >= 2 else "degraded",
        "environment": ENVIRONMENT,
        "version": VERSION,
        "uptime": round(time.time() - _START_TIME, 1),
        "redis": "connected" if bus and bus.ping() else "unavailable",
        "live_agents": list(agents.keys()),
        "components": components,
    }

@app.get("/ready")
def readiness_probe():
    return {"status": "ready", "environment": ENVIRONMENT, "version": VERSION}

# ---------------------------------------------------------------------------
# SSE & UI Endpoints
# ---------------------------------------------------------------------------

@app.get("/events")
async def event_stream(last_id: str = Query("$")):
    """Unified SSE stream (rhea:events:live)."""
    bus = _get_bus()
    if not bus or not bus.r:
        raise HTTPException(status_code=503, detail="Redis STM not available")
    
    async def generator():
        pubsub = bus.r.pubsub()
        pubsub.subscribe("rhea:events:live")
        try:
            # History first
            recent = bus.read_events(count=10)
            for evt in recent:
                yield f"data: {json.dumps(evt)}\n\n"
            
            # Then live
            while True:
                msg = pubsub.get_message(timeout=1.0)
                if msg and msg["type"] == "message":
                    yield f"data: {msg['data']}\n\n"
                else:
                    yield f": keepalive\n\n"
                await asyncio.sleep(0.1)
        finally:
            pubsub.unsubscribe("rhea:events:live")
            pubsub.close()

    return StreamingResponse(generator(), media_type="text/event-stream")

@app.get("/ui/events")
async def ui_event_stream():
    """SSE for ui:update channel."""
    bus = _get_bus()
    if not bus or not bus.r:
        raise HTTPException(status_code=503, detail="Redis STM not available")
    
    def generator():
        pubsub = bus.r.pubsub()
        pubsub.subscribe("ui:update")
        try:
            for message in pubsub.listen():
                if message['type'] == 'message':
                    yield f"data: {message['data']}\n\n"
        finally:
            pubsub.unsubscribe("ui:update")
            pubsub.close()

    return StreamingResponse(generator(), media_type="text/event-stream")

@app.get("/ui/atlas")
def get_atlas_state():
    bus = _get_bus()
    if not bus:
        raise HTTPException(status_code=503, detail="Redis STM not available")

    dashboard = bus.r.get("ui:dashboard")
    relay = bus.r.get("ui:relay_recent")
    geometry = json.loads(relay) if relay else []

    if IS_PRODUCTION and isinstance(geometry, list):
        for item in geometry:
            if isinstance(item, dict):
                item.pop("actor", None)

    return {
        "metrics": json.loads(dashboard) if dashboard else {},
        "geometry": geometry,
        "ts": time.time()
    }

# ---------------------------------------------------------------------------
# Agent Bus Endpoints (Hyperion)
# ---------------------------------------------------------------------------

@app.get("/agents")
def list_agents():
    bus = _get_bus()
    if not bus: return {"agents": {}}
    return {"agents": bus.get_heartbeats()}

class AgentMessage(BaseModel):
    message: str = Field(..., max_length=5000)
    priority: str = Field(default="normal")
    meta: dict = {}

@app.post("/agents/{agent_id}/inbox")
def send_to_agent(agent_id: str, msg: AgentMessage):
    bus = _get_bus()
    if not bus: raise HTTPException(status_code=503)
    envelope = bus.send_message(agent_id, {
        "message": msg.message,
        "priority": msg.priority,
        **msg.meta,
    })
    bus.agent_event("message_sent", {"to": agent_id, "priority": msg.priority})
    return {"status": "sent", "envelope": envelope}

@app.get("/agents/{agent_id}/inbox")
def read_agent_inbox(agent_id: str, limit: int = Query(20, ge=1, le=100)):
    bus = _get_bus()
    if not bus: return []
    return bus.read_inbox(agent_id, limit=limit)

@app.post("/agents/{agent_id}/heartbeat")
def agent_heartbeat(agent_id: str, status: str = "alive"):
    bus = _get_bus()
    if not bus: raise HTTPException(status_code=503)
    # Temporary switch context for heartbeat
    orig_id = bus.node_id
    bus.node_id = agent_id
    bus.heartbeat(status)
    bus.node_id = orig_id
    bus.agent_event("heartbeat", {"agent": agent_id, "status": status})
    return {"status": "ok", "agent": agent_id}

@app.get("/gem", response_class=HTMLResponse)
def gem_redirect():
    if _FRONTEND_DIR.exists():
        return HTMLResponse(content='<meta http-equiv="refresh" content="0;url=/app/">', status_code=302)
    return HTMLResponse(content="<h1>Frontend not built yet.</h1>")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", os.environ.get("RHEAD_PORT", "8000")))
    print(f"Starting Rhea Daemon ({VERSION}) on 0.0.0.0:{port} [{ENVIRONMENT}]")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
