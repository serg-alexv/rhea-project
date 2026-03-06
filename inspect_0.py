#!/usr/bin/env python3
import json
import time
import os

LOG_PATH = "/tmp/0.log"

def tail_log():
    print(f"👀 Observing {LOG_PATH}...")
    if not os.path.exists(LOG_PATH):
        print("⚠️  Log file does not exist yet.")
        
    while True:
        if not os.path.exists(LOG_PATH):
            time.sleep(1)
            continue
            
        with open(LOG_PATH, "r") as f:
            # Go to the end of the file
            f.seek(0, os.SEEK_END)
            
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                
                try:
                    event = json.loads(line)
                    origin = event.get("origin", "???")
                    ts = event.get("timestamp", 0)
                    payload = event.get("payload", {})
                    h = event.get("hash", "0")[:8]
                    
                    print(f"\n--- [ {origin} ] @ {ts} | {h} ---")
                    print(json.dumps(payload, indent=2, ensure_ascii=False))
                except Exception as e:
                    print(f"❌ Parse error: {line.strip()} ({e})")

if __name__ == "__main__":
    try:
        tail_log()
    except KeyboardInterrupt:
        print("\n👋 Observer detached.")
