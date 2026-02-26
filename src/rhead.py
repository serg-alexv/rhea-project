#!/usr/bin/env python3
"""
rhead.py — Rhea's single daemon entry point.

Mounts the Tribunal API and provides top-level health/status.
All traffic goes through one port (default 8000).

Usage:
    python3 src/rhead.py                  # port 8000
    RHEAD_PORT=8400 python3 src/rhead.py  # port 8400
"""
import os
import sys
import time
from pathlib import Path

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the tribunal sub-application
from tribunal_api import app as tribunal_app

app = FastAPI(
    title="Rhea Daemon",
    description="Single entry point for all Rhea services.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the full Tribunal API under /api
app.mount("/api", tribunal_app)


@app.get("/")
def root():
    return {
        "status": "ALIVE",
        "engine": "rhead v0.2.0",
        "endpoints": {
            "/": "this message",
            "/health": "quick liveness check",
            "/api/health": "tribunal health (providers, redis, models)",
            "/api/tribunal": "POST — multi-model consensus (L1/L2)",
            "/api/tribunal/ice": "POST — ICE iterative consensus (L3)",
            "/api/models": "GET — available models and providers",
            "/api/modes": "GET — cognitive stance modes",
        },
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "uptime_s": time.time(),
        "version": "0.2.0",
    }


if __name__ == "__main__":
    import uvicorn
    import logging
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    port = int(os.environ.get("RHEAD_PORT", "8000"))
    print(f"  Rhea Daemon starting on http://0.0.0.0:{port}")
    print(f"  Tribunal API at http://0.0.0.0:{port}/api/")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
