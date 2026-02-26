#!/usr/bin/env python3
"""
rhead.py — Rhea's single daemon entry point (v0.3.0 "Scientific Gem").

Mounts: Tribunal API, Agent Bus, SSE Event Stream, Static Frontend.
All traffic through one port (default 8000).

Usage:
    python3 src/rhead.py                  # port 8000
    RHEAD_PORT=8400 python3 src/rhead.py  # port 8400
"""
import os
import sys
import json
import asyncio
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from tribunal_api import app as tribunal_app
from rhea_bus import RheaBus

app = FastAPI(
    title="Rhea Daemon",
    description="Single entry point for all Rhea services.",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Tribunal API under /api
app.mount("/api", tribunal_app)

# Mount static frontend if it exists
_FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if _FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")

# Lazy bus
_bus: Optional[RheaBus] = None


def _get_bus() -> Optional[RheaBus]:
    global _bus
    if _bus is None:
        try:
            _bus = RheaBus("rhead")
            if not _bus.ping():
                _bus = None
        except Exception:
            _bus = None
    return _bus


# ---------------------------------------------------------------------------
# Core endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "ALIVE",
        "engine": "rhead v0.3.0 (Scientific Gem)",
        "endpoints": {
            "/": "this message",
            "/health": "liveness + redis + agents",
            "/app": "frontend UI (Scientific Gem)",
            "/events": "GET — SSE live event stream",
            "/events/history": "GET — recent events",
            "/agents": "GET — live agent heartbeats",
            "/agents/{id}/inbox": "GET/POST — agent mailbox",
            "/api/health": "tribunal health",
            "/api/tribunal": "POST — consensus (L1/L2)",
            "/api/tribunal/ice": "POST — ICE consensus (L3)",
            "/api/models": "GET — available models",
        },
    }


@app.get("/health")
def health():
    bus = _get_bus()
    redis_ok = bus.ping() if bus else False
    agents = bus.get_heartbeats() if bus else {}
    return {
        "status": "healthy",
        "version": "0.3.0",
        "uptime_s": time.time(),
        "redis": "connected" if redis_ok else "unavailable",
        "live_agents": list(agents.keys()),
    }


# ---------------------------------------------------------------------------
# SSE Event Stream (Server-Sent Events)
# ---------------------------------------------------------------------------

@app.get("/events")
async def event_stream(last_id: str = Query("$", description="Last event ID for resumption")):
    """SSE stream of all Rhea events. Connect with EventSource('/events')."""
    bus = _get_bus()
    if not bus:
        return {"error": "Redis unavailable"}

    async def generate():
        pubsub = bus.r.pubsub()
        pubsub.subscribe("rhea:events:live")
        try:
            # Send recent history first
            recent = bus.read_events(count=10)
            for evt in recent:
                yield f"data: {json.dumps(evt)}\n\n"

            # Then stream live
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

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/events/history")
def event_history(count: int = Query(50, ge=1, le=500)):
    bus = _get_bus()
    if not bus:
        return []
    return bus.read_events(count=count)


# ---------------------------------------------------------------------------
# Agent Bus endpoints
# ---------------------------------------------------------------------------

@app.get("/agents")
def list_agents():
    bus = _get_bus()
    if not bus:
        return {"agents": {}, "redis": "unavailable"}
    return {"agents": bus.get_heartbeats()}


class AgentMessage(BaseModel):
    message: str = Field(..., max_length=5000)
    priority: str = Field(default="normal")
    meta: dict = {}


@app.post("/agents/{agent_id}/inbox")
def send_to_agent(agent_id: str, msg: AgentMessage):
    bus = _get_bus()
    if not bus:
        return {"error": "Redis unavailable"}
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
    if not bus:
        return []
    return bus.read_inbox(agent_id, limit=limit)


@app.post("/agents/{agent_id}/heartbeat")
def agent_heartbeat(agent_id: str, status: str = "alive"):
    bus = _get_bus()
    if not bus:
        return {"error": "Redis unavailable"}
    # Override node_id for this call
    bus.node_id = agent_id
    bus.heartbeat(status)
    bus.agent_event("heartbeat", {"agent": agent_id, "status": status})
    return {"status": "ok", "agent": agent_id}


# ---------------------------------------------------------------------------
# Frontend (inline fallback if no frontend/ dir)
# ---------------------------------------------------------------------------

@app.get("/gem", response_class=HTMLResponse)
def gem_redirect():
    if _FRONTEND_DIR.exists():
        return HTMLResponse(
            content='<meta http-equiv="refresh" content="0;url=/app/">',
            status_code=302,
        )
    return HTMLResponse(content="<h1>Frontend not built yet. Run from /frontend</h1>")


if __name__ == "__main__":
    import uvicorn
    import logging
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    port = int(os.environ.get("RHEAD_PORT", "8000"))
    print(f"  Rhea Daemon v0.3.0 (Scientific Gem)")
    print(f"  http://0.0.0.0:{port}")
    print(f"  Tribunal: /api  |  Agents: /agents  |  Events: /events  |  UI: /app")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
