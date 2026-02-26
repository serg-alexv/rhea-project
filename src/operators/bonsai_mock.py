import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rhea_bus import RheaBus

class MockBonsai:
    """A Stateless Mock Operator to proof the Bonsai/9router interface."""
    def __init__(self, provider_id: str):
        self.bus = RheaBus(node_id=f"bonsai-{provider_id}")
        self.provider_id = provider_id

    def on_request(self, payload):
        """Handle incoming inference requests."""
        request_id = payload['data'].get("request_id")
        print(f"[{self.provider_id}] Processing request {request_id}...")
        
        # Simulate logic work
        time.sleep(0.1) 
        
        # Publish result to response channel
        self.bus.publish("inference_results", {
            "request_id": request_id,
            "status": "success",
            "provider": self.provider_id,
            "result": f"Logical proof from {self.provider_id}"
        })

    def run(self):
        print(f"💠 Bonsai Operator '{self.provider_id}' ONLINE")
        self.bus.subscribe("inference_requests", self.on_request)

if __name__ == "__main__":
    provider = sys.argv[1] if len(sys.argv) > 1 else "mock-1"
    MockBonsai(provider).run()
