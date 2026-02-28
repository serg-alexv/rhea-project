import zmq
import json
import hmac
import hashlib
import sys
import time

INTERNAL_KEY = b"rhea_integrity_v1"

class BonsaiNode:
    """A standardized operator node for the Unstoppable Swarm."""
    def __init__(self, node_name: str, provider: str):
        self.node_name = node_name
        self.provider = provider
        self.ctx = zmq.Context()
        
        # Subscribe to requests
        self.sub = self.ctx.socket(zmq.SUB)
        self.sub.connect("ipc:///tmp/rhea_swarm_requests")
        self.sub.setsockopt_string(zmq.SUBSCRIBE, "")
        
        # Publish results
        self.pub = self.ctx.socket(zmq.PUB)
        self.pub.bind(f"ipc:///tmp/rhea_swarm_results")

    def _verify(self, message: dict) -> bool:
        """Verify the intent signature using the HIP protocol."""
        payload = message.get("payload")
        signature = message.get("signature")
        expected = hmac.new(INTERNAL_KEY, json.dumps(payload).encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)

    def process_logic(self, hypothesis: str):
        """Placeholder for actual provider call (Gemini/DeepSeek/etc)."""
        print(f"🧠 [{self.node_name}] Reasoning on: {hypothesis[:50]}...")
        # Simulating high-density inference
        time.sleep(0.5)
        return f"Logic proof from {self.provider} for: {hypothesis[:20]}"

    def run(self):
        print(f"🟢 BONSAI NODE '{self.node_name}' (Provider: {self.provider}) ONLINE")
        while True:
            try:
                message = self.sub.recv_json()
                if self._verify(message):
                    req_id = message['payload']['request_id']
                    result = self.process_logic(message['payload']['hypothesis'])
                    
                    response = {
                        "request_id": req_id,
                        "node": self.node_name,
                        "provider": self.provider,
                        "result": result,
                        "timestamp": time.time()
                    }
                    self.pub.send_json(response)
                else:
                    print(f"🕵️ [{self.node_name}] SECURITY ALERT: Signature mismatch! Ignoring request.")
            except Exception as e:
                print(f"❌ [{self.node_name}] Error: {e}")
                time.sleep(1)

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "alpha-node"
    prov = sys.argv[2] if len(sys.argv) > 2 else "mock"
    BonsaiNode(name, prov).run()
