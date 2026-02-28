import zmq
import json
import hmac
import hashlib
import time
import uuid
import sqlite3
from typing import List, Dict

# ADR-015: The Unstoppable Swarm Orchestrator
INTERNAL_KEY = b"rhea_integrity_v1" # Local secret for AITM defense

class RheaSwarm:
    def __init__(self):
        self.ctx = zmq.Context()
        self.pub = self.ctx.socket(zmq.PUB)
        self.pub.bind("ipc:///tmp/rhea_swarm_requests")
        
        self.sub = self.ctx.socket(zmq.SUB)
        self.sub.connect("ipc:///tmp/rhea_swarm_results")
        self.sub.setsockopt_string(zmq.SUBSCRIBE, "")
        
        # Contour B: Hard Audit (SQLite)
        self.db = sqlite3.connect("data/swarm_ledger.db", check_same_thread=False)
        self.setup_db()

    def setup_db(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS logic_chain (
                request_id TEXT PRIMARY KEY,
                timestamp REAL,
                intent_hash TEXT,
                consensus_score REAL,
                status TEXT
            )
        """)
        self.db.commit()

    def _sign(self, payload: dict) -> str:
        return hmac.new(INTERNAL_KEY, json.dumps(payload).encode(), hashlib.sha256).hexdigest()

    def dispatch(self, hypothesis: str, target_nodes: int = 3):
        """Broadcast a signed scientific intent to the swarm."""
        req_id = str(uuid.uuid4())
        payload = {
            "request_id": req_id,
            "hypothesis": hypothesis,
            "timestamp": time.time()
        }
        signature = self._sign(payload)
        
        message = {
            "payload": payload,
            "signature": signature,
            "nodes_required": target_nodes
        }
        
        print(f"📡 SWARM DISPATCH: {req_id[:8]} | Sig: {signature[:8]}")
        self.pub.send_json(message)
        
        # Record in Hard Audit
        self.db.execute("INSERT INTO logic_chain VALUES (?, ?, ?, ?, ?)",
                       (req_id, time.time(), signature, 0.0, "PENDING"))
        self.db.commit()
        return req_id

    def collect_responses(self, timeout_s: int = 30):
        """Wait for and verify responses from the seeder nodes."""
        # Note: In a production environment, this would run in a background thread
        # and update the Atlas UI via WebSockets.
        pass

if __name__ == "__main__":
    swarm = RheaSwarm()
    # Initializing the first swarm heartbeat
    swarm.dispatch("Initialize Stage 3: Unstoppable Swarm Logic")
