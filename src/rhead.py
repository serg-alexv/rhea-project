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

# Enable CORS for the Atlas Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.get("/health")
def health_check():
    # Check SQL and Redis
    try:
        db = sqlite3.connect("data/proof.db")
        res = db.execute("SELECT count(*) FROM logic_audit").fetchone()
        audit_count = res[0]
    except:
        audit_count = 0
        
    redis_alive = r.ping() if r else False
    
    return {
        "status": "healthy" if redis_alive else "degraded",
        "uptime": time.time(),
        "audit_records": audit_count,
        "redis_stm": "online" if redis_alive else "offline",
        "active_council": ["ORION", "HYPERION", "B2", "REX", "A1", "A8"]
    }

if __name__ == "__main__":
    print("💠 Starting Rhea Daemon (STM-Ready) on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
