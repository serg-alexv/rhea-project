#!/usr/bin/env python3
"""
dobby_handler.py — Reactive webhook handler for Dobby automation.
Processes external triggers to automate routine tasks (commit, sync, build).

ADR-018: Cellular stress response integration.
"""

import json
import os
import subprocess
import sys
from datetime import datetime

# Authoritative keyspace for state sync
REDIS_KEY_JOBS = "rhea:queue:jobs"
REDIS_KEY_SNAPSHOT = "rhea:state:snapshot"

def run_task(cmd: str):
    """Execute a shell task and log the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {
            "status": "success" if result.returncode == 0 else "error",
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        return {"status": "exception", "error": str(e)}

def handle_payload(payload: dict):
    """Route the Dobby payload to the appropriate automation task."""
    event = payload.get("event")
    
    if event == "git:autocommit":
        # Automatically stage and commit with a standard message
        msg = f"chore(auto): dobby trigger at {datetime.now().isoformat()}"
        return run_task(f"git add . && git commit -m '{msg}' && git push")
    
    elif event == "rclone:sync":
        # Trigger an immediate cloud sync
        return run_task("bash scripts/cloud_sync.sh")
    
    elif event == "rhea:compact":
        # Signal the agent to compact its context window
        # (This usually happens by writing to a Redis channel or file)
        return run_task("touch STOP")

    return {"status": "ignored", "reason": f"unknown event: {event}"}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: dobby_handler.py <json_payload>")
        sys.exit(1)
        
    try:
        data = json.loads(sys.argv[1])
        result = handle_payload(data)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)
