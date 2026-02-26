from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
load_dotenv(PROJECT_ROOT / ".env")

app = FastAPI(title="Rhea rhead Daemon (v4.1)")

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
