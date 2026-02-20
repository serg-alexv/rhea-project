#!/usr/bin/env python3
"""
rhea_overwatcher.py — Advanced Process & Logic Monitor
Part of Rhea Agent Coordination OS (Node-00: Watcher)

Monitors:
  - Tribunal API (8400)
  - Rex System Service (launchd)
  - Memory Coherency (L4 Age)
  - Repo Invariants (check.sh)

Communicates via Virtual Office Inbox and macOS Notifications.
"""

import os
import time
import subprocess
import requests
import json
from datetime import datetime, timezone
from pathlib import Path

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent
INBOX_DIR = PROJECT_ROOT / "ops" / "virtual-office" / "inbox"
API_URL = "http://localhost:8400/health"
CHECK_INTERVAL_S = 30
L4_BRIDGE_PATH = PROJECT_ROOT / "rhea-elementary/memory-core/context-bridge.md"
MAX_L4_AGE_H = 6

def log_to_office(topic, content, priority="P1"):
    """Drops a monitor report into the Virtual Office inbox."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"WATCHER_{ts}_{topic}.md"
    path = INBOX_DIR / filename
    
    header = f"# WATCHER REPORT: {topic}\n"
    meta = f"> Timestamp: {datetime.now(timezone.utc).isoformat()}\n> Priority: {priority}\n\n"
    
    with open(path, "w") as f:
        f.write(header)
        f.write(meta)
        f.write(content)
    print(f"[Watcher] Report delivered: {filename}")

def notify(title, msg, sound="Glass"):
    """Sends a native macOS notification."""
    cmd = f'display notification "{msg}" with title "{title}" sound name "{sound}"'
    subprocess.run(["osascript", "-e", cmd])

def check_api():
    try:
        r = requests.get(API_URL, timeout=2)
        return r.status_code == 200
    except:
        return False

def check_rex_service():
    """Checks if the com.rhea.rex service is loaded in launchctl."""
    try:
        res = subprocess.run(["launchctl", "list", "com.rhea.rex"], capture_output=True, text=True)
        return res.returncode == 0
    except:
        return False

def check_l4_freshness():
    if not L4_BRIDGE_PATH.exists():
        return False, "Missing"
    mtime = L4_BRIDGE_PATH.stat().st_mtime
    age_h = (time.time() - mtime) / 3600
    return age_h < MAX_L4_AGE_H, f"{age_h:.1f}h"

def run_overwatch_loop():
    print(f"💠 RHEA OVERWATCHER ONLINE (PID {os.getpid()})")
    print(f"Monitoring {API_URL} and com.rhea.rex...")
    
    state = {
        "api": True,
        "rex": True,
        "l4": True
    }

    while True:
        # 1. Check API
        api_alive = check_api()
        if api_alive != state["api"]:
            if not api_alive:
                notify("WATCHER ALERT", "Tribunal API is DOWN", "Sosumi")
                log_to_office("API_FAILURE", "The Tribunal API on port 8400 has stopped responding.", "P0")
            else:
                notify("WATCHER SYNC", "Tribunal API recovered", "Glass")
                log_to_office("API_RECOVERY", "The Tribunal API is back online.")
            state["api"] = api_alive

        # 2. Check Rex Service
        rex_alive = check_rex_service()
        if rex_alive != state["rex"]:
            if not rex_alive:
                notify("WATCHER ALERT", "Rex Service is DOWN", "Basso")
                log_to_office("REX_FAILURE", "The com.rhea.rex system service is no longer listed in launchctl.", "P0")
            else:
                notify("WATCHER SYNC", "Rex Service restored", "Glass")
                log_to_office("REX_RECOVERY", "The Rex system service has been re-enabled.")
            state["rex"] = rex_alive

        # 3. Check L4 Freshness
        l4_ok, age_str = check_l4_freshness()
        if not l4_ok and state["l4"]:
            log_to_office("L4_STALE", f"Context bridge is {age_str} old. Cache coherency risk high.", "P1")
            state["l4"] = False
        elif l4_ok:
            state["l4"] = True

        time.sleep(CHECK_INTERVAL_S)

if __name__ == "__main__":
    try:
        run_overwatch_loop()
    except KeyboardInterrupt:
        print("\nWatcher terminated.")
