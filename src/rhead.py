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

# Mount auth router
from auth_api import auth_router
app.include_router(auth_router, prefix="/auth")

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


def _probe_component(name, check_fn, timeout=3.0):
    """Probe a single distributed component. Returns dict with status + latency."""
    import threading
    result = {"name": name, "status": "offline", "latency_ms": None, "detail": None}
    start = time.time()
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
    """Probe all distributed cloud components in parallel."""
    import concurrent.futures
    probes = {}

    # 1. Redis (local or Oracle VM)
    def check_redis():
        if not r: raise ConnectionError("no redis client configured")
        r.ping()
        info = r.info("memory")
        return f"used_memory={info.get('used_memory_human','?')}"
    probes["redis"] = lambda: check_redis()

    # 2. SQLite (proof.db — local persistence)
    def check_sqlite():
        db_path = str(PROJECT_ROOT / "data" / "proof.db")
        db = sqlite3.connect(db_path, timeout=2)
        count = db.execute("SELECT count(*) FROM logic_audit").fetchone()[0]
        db.close()
        return f"audit_records={count}"
    probes["sqlite"] = check_sqlite

    # 3. LLM Bridge (multi-provider availability)
    def check_bridge():
        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from rhea_bridge import RheaBridge
        _b = RheaBridge()
        st = _b.models_status()
        avail = st["summary"]["available_providers"]
        total = st["summary"]["total_providers"]
        return f"{avail}/{total} providers"
    probes["llm_bridge"] = check_bridge

    # 4. Vercel frontend (Orion Atlas)
    def check_vercel():
        import urllib.request
        vercel_url = os.environ.get("VERCEL_URL", "")
        if not vercel_url:
            raise ConnectionError("VERCEL_URL not configured")
        req = urllib.request.Request(f"{vercel_url}/api/health", method="GET")
        resp = urllib.request.urlopen(req, timeout=5)
        return f"http {resp.status}"
    probes["frontend_vercel"] = check_vercel

    # 5. Oracle VM (Redis/backup — if configured)
    def check_oracle():
        oracle_host = os.environ.get("ORACLE_VM_HOST", "")
        if not oracle_host:
            raise ConnectionError("ORACLE_VM_HOST not configured")
        import urllib.request
        req = urllib.request.Request(f"http://{oracle_host}:8000/health", method="GET")
        resp = urllib.request.urlopen(req, timeout=5)
        return f"backup_api http {resp.status}"
    probes["oracle_vm"] = check_oracle

    # 6. Firebase (if configured)
    def check_firebase():
        fb_project = os.environ.get("FIREBASE_PROJECT_ID", "")
        if not fb_project:
            raise ConnectionError("FIREBASE_PROJECT_ID not configured")
        return f"project={fb_project}"
    probes["firebase"] = check_firebase

    # Run all probes in parallel (3s timeout each)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(_probe_component, name, fn): name
            for name, fn in probes.items()
        }
        for future in concurrent.futures.as_completed(futures, timeout=8):
            results.append(future.result())

    return sorted(results, key=lambda x: x["name"])


@app.get("/health")
def health_check():
    """Full distributed cloud component status — probes all layers in parallel."""
    components = _probe_all_components()
    online = sum(1 for c in components if c["status"] == "online")
    total = len(components)

    # Count LLM providers from the bridge probe
    bridge = next((c for c in components if c["name"] == "llm_bridge"), None)
    providers_str = bridge["detail"] if bridge and bridge["status"] == "online" else "0/?"

    return {
        "status": "ok" if online >= 2 else "degraded",
        "environment": ENVIRONMENT,
        "version": VERSION,
        "uptime": round(time.time() - _START_TIME, 1),
        "cloud": "dispersed",
        "components_online": f"{online}/{total}",
        "providers": providers_str,
        "components": components,
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
