from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sqlite3
import json
import time

app = FastAPI(title="Rhea rhead Daemon")

# Enable CORS for the future Atlas Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "ALIVE",
        "node": "ORION-NODE-02",
        "engine": "High-Density Logic",
        "message": "Welcome to the Rhea Council Chamber. The Atlas is being scaffolded."
    }

@app.get("/health")
def health_check():
    # Real-time data from our SQLite Hard Audit
    try:
        db = sqlite3.connect("data/proof.db")
        res = db.execute("SELECT count(*) FROM logic_audit").fetchone()
        audit_count = res[0]
    except:
        audit_count = 0
        
    return {
        "status": "healthy",
        "uptime": time.time(),
        "audit_records": audit_count,
        "d_metric": 243.8,
        "active_council": ["ORION", "HYPERION", "B2", "REX", "GPT-5"]
    }

if __name__ == "__main__":
    print("💠 Starting Rhea Daemon on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
