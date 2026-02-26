#!/usr/bin/env python3
"""
ui_sync.py — Project system state into Redis STM for Orion's Atlas UI.
Synchronizes metrics, task load, and recent relay events.
"""
import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
import redis

# Load env from root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

REDIS_URL = os.environ.get("REDIS_URL")
DASHBOARD_FILE = PROJECT_ROOT / "opera" / "metrics" / "live_dashboard.json"
RELAY_CHAIN_FILE = PROJECT_ROOT / "opera" / "ops" / "virtual-office" / "relay_chain.jsonl"

def sync_to_redis():
    if not REDIS_URL:
        print("[ui-sync] ERROR: REDIS_URL not set.")
        return

    r = redis.from_url(REDIS_URL)
    try:
        # 1. Sync Dashboard Metrics
        if DASHBOARD_FILE.exists():
            try:
                data = json.loads(DASHBOARD_FILE.read_text())
                r.set("ui:dashboard", json.dumps(data))
                r.publish("ui:update", json.dumps({"type": "metrics", "ts": time.time()}))
                print(f"[ui-sync] Dashboard metrics synced. D={data['metrics']['d_metric']['value']}")
            except Exception as e:
                print(f"[ui-sync] Dashboard sync failed: {e}")

        # 2. Sync Recent Relay Chain (Last 10 events) for Atlas geometry
        if RELAY_CHAIN_FILE.exists():
            try:
                with open(RELAY_CHAIN_FILE, "r") as f:
                    lines = f.readlines()
                recent = [json.loads(line) for line in lines[-10:]]
                r.set("ui:relay_recent", json.dumps(recent))
                print(f"[ui-sync] Relay chain synced ({len(recent)} events).")
            except Exception as e:
                print(f"[ui-sync] Relay sync failed: {e}")
    finally:
        r.close()

if __name__ == "__main__":
    sync_to_redis()
