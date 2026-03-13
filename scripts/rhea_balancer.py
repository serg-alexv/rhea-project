#!/usr/bin/env python3
"""
rhea_balancer.py - The Central Traffic Controller for Multi-Agent Loops.
Enforces write locks and coordinates the [Prompt -> Enhance -> Extend -> Compact -> Check -> Send] loop.
"""
import sys
import json
import redis
import os
import time

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

class Balancer:
    def __init__(self):
        try:
            self.r = redis.from_url(REDIS_URL, decode_responses=True)
            self.r.ping()
        except Exception as e:
            print(json.dumps({"error": f"Redis connection failed: {e}"}))
            sys.exit(1)

    def request_write_lock(self, agent_id: str, file_path: str) -> dict:
        """Attempt to acquire an exclusive lock to write to a file."""
        lock_key = f"rhea:lock:file:{file_path}"
        # Lock expires in 60 seconds to prevent deadlocks if agent crashes
        acquired = self.r.set(lock_key, agent_id, nx=True, ex=60)
        if acquired:
            return {"status": "granted", "message": f"Lock acquired for {file_path}", "agent": agent_id}
        else:
            current_owner = self.r.get(lock_key)
            return {"status": "denied", "message": f"File {file_path} is locked by {current_owner}", "agent": agent_id}

    def release_write_lock(self, agent_id: str, file_path: str) -> dict:
        """Release the lock if the agent owns it."""
        lock_key = f"rhea:lock:file:{file_path}"
        current_owner = self.r.get(lock_key)
        if current_owner == agent_id:
            self.r.delete(lock_key)
            return {"status": "released", "message": f"Lock released for {file_path}"}
        return {"status": "error", "message": "You do not own this lock."}

    def trigger_loop_stage(self, stage: str, payload: dict) -> dict:
        """Advance the Multi-Team Loop."""
        valid_stages = ["prompt", "enhance", "extend", "compact", "check", "send"]
        if stage not in valid_stages:
            return {"error": f"Invalid stage. Must be one of {valid_stages}"}
        
        event = {
            "stage": stage,
            "ts": time.time(),
            "payload": payload
        }
        self.r.publish("rhea:loop", json.dumps(event))
        return {"status": "triggered", "stage": stage, "details": "Event published to rhea:loop"}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command provided"}))
        sys.exit(1)
        
    cmd = sys.argv[1]
    balancer = Balancer()

    try:
        if cmd == "request_lock" and len(sys.argv) == 4:
            res = balancer.request_write_lock(sys.argv[2], sys.argv[3])
            print(json.dumps(res))
        elif cmd == "release_lock" and len(sys.argv) == 4:
            res = balancer.release_write_lock(sys.argv[2], sys.argv[3])
            print(json.dumps(res))
        elif cmd == "trigger" and len(sys.argv) == 4:
            res = balancer.trigger_loop_stage(sys.argv[2], json.loads(sys.argv[3]))
            print(json.dumps(res))
        else:
            print(json.dumps({"error": "Invalid arguments."}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
