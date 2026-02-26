from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import sqlite3
import json
import time
import os
import redis
from dotenv import load_dotenv
from pathlib import Path

# Load env
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Set dev API key for local frontend
if not os.environ.get("TRIBUNAL_API_KEYS"):
    os.environ["TRIBUNAL_API_KEYS"] = "dev-bypass"

import sys
sys.path.insert(0, str(Path(__file__).parent))

# ---------------------------------------------------------------------------
# Environment detection
# ---------------------------------------------------------------------------
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").lower()
IS_PRODUCTION = ENVIRONMENT == "production"
VERSION = os.environ.get("VERSION", "dev")

app = FastAPI(title="Rhea rhead Daemon (v4.1)")

# Mount Tribunal API under /api
try:
    from tribunal_api import app as tribunal_app
    app.mount("/api", tribunal_app)
except ImportError:
    pass

# Mount frontend
_FRONTEND_DIR = PROJECT_ROOT / "frontend"
if _FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")

# ---------------------------------------------------------------------------
# CORS — strict in production, permissive in dev
# ---------------------------------------------------------------------------
if IS_PRODUCTION:
    _allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "")
    _cors_origins = [o.strip() for o in _allowed_origins_env.split(",") if o.strip()]
    if not _cors_origins:
        # Fallback: deny all cross-origin requests if ALLOWED_ORIGINS is not set in prod
        _cors_origins = []
    _allow_all = False
else:
    # Dev: allow common local frontend ports
    _cors_origins = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    _allow_all = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not IS_PRODUCTION else _cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=not IS_PRODUCTION,
)

# Redis Connection
REDIS_URL = os.environ.get("REDIS_URL")
r = redis.from_url(REDIS_URL) if REDIS_URL else None

@app.get("/")
def read_root():
    return {
        "status": "ALIVE",
        "node": "ORION-NODE-02",
        "version": "4.1.0-STM",
        "message": "Welcome to the Rhea Council Chamber. STM Layer is ACTIVE."
    }

from fastapi.responses import StreamingResponse
import asyncio

# ... (existing imports)

@app.get("/ui/events")
async def event_stream():
    """Server-Sent Events stream for Orion's UI."""
    if not r:
        raise HTTPException(status_code=503, detail="Redis STM not available")
    
    def generator():
        pubsub = r.pubsub()
        pubsub.subscribe("ui:update")
        print("[rhead] SSE Stream Started.")
        try:
            for message in pubsub.listen():
                if message['type'] == 'message':
                    yield f"data: {message['data']}\n\n"
        finally:
            pubsub.unsubscribe()
            print("[rhead] SSE Stream Closed.")

    return StreamingResponse(generator(), media_type="text/event-stream")

@app.get("/ui/atlas")
def get_atlas_state():
    """Fetch current system state for Three.js projection."""
    if not r:
        raise HTTPException(status_code=503, detail="Redis STM not available")
    
    dashboard = r.get("ui:dashboard")
    relay = r.get("ui:relay_recent")
    
    return {
        "metrics": json.loads(dashboard) if dashboard else {},
        "geometry": json.loads(relay) if relay else [],
        "ts": time.time()
    }

_START_TIME = time.time()


@app.get("/health")
def health_check():
    """Production health endpoint — includes environment, version, uptime, provider count."""
    # Check SQL
    try:
        db_path = str(PROJECT_ROOT / "data" / "proof.db")
        db = sqlite3.connect(db_path)
        res = db.execute("SELECT count(*) FROM logic_audit").fetchone()
        audit_count = res[0]
        db.close()
    except Exception:
        audit_count = 0

    redis_alive = False
    try:
        redis_alive = r.ping() if r else False
    except Exception:
        pass

    # Count available providers from bridge (lazy — don't import at module level)
    providers_available = 0
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from rhea_bridge import RheaBridge
        _b = RheaBridge()
        status = _b.models_status()
        providers_available = status["summary"]["available_providers"]
    except Exception:
        pass

    return {
        "status": "ok",
        "environment": ENVIRONMENT,
        "version": VERSION,
        "uptime": round(time.time() - _START_TIME, 1),
        "providers_available": providers_available,
        "audit_records": audit_count,
        "redis_stm": "online" if redis_alive else "offline",
        "active_council": ["ORION", "HYPERION", "B2", "REX", "A1", "A8"],
    }


@app.get("/ready")
def readiness_probe():
    """Cloud Run startup/readiness probe — returns 200 as soon as the app is up."""
    return {"status": "ready", "environment": ENVIRONMENT, "version": VERSION}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"Starting Rhea Daemon (STM-Ready) on 0.0.0.0:{port} [{ENVIRONMENT}]")
    uvicorn.run(app, host="0.0.0.0", port=port)
